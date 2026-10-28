"""Check the engine against the blind human coding of the 144 ARGUS outputs.

Ground truth is M5 (unsupported assertions) from the frozen primary coding of
the MSc benchmark: a count per output, with each counted claim quoted in the
note. The engine sees only what the ARGUS model saw (scenario and focal
claim) plus the output text. It never sees the coding.

Discipline carried over from the dissertation: the sample is fixed by seed,
every item used for development is recorded in bench/argus_dev_set.json, and
a held-out run excludes those items. Only held-out numbers are reportable.

    uv run python bench/argus.py --split dev --n 16 --env-file PATH
    uv run python bench/argus.py --split devset --env-file PATH
    uv run python bench/argus.py --split heldout --env-file PATH
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import pathlib
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

import anthropic  # noqa: E402

from receipts.engine import check  # noqa: E402
from receipts.keys import load_key  # noqa: E402
from receipts.verify import norm  # noqa: E402

ARGUS = pathlib.Path.home() / "Desktop/projects/dissertation-artefact/analysis"
VIEW = ARGUS / "coding_view.jsonl"
SCORES = ARGUS / "coding_scores_primary_144of144_2026-08-10.csv"
DEV_SET = pathlib.Path(__file__).with_name("argus_dev_set.json")
FLAGGED = ("UNSUPPORTED", "CONTRADICTED")


def load_items(view=VIEW, scores=SCORES) -> list[dict]:
    coded = {r["output_id"]: r for r in csv.DictReader(open(scores, encoding="utf-8"))}
    items = []
    for line in open(view, encoding="utf-8"):
        v = json.loads(line)
        s = coded[v["output_id"]]
        resp = v["structured_response"]
        # Sections stay in the order the model wrote them, which is the order the coder read.
        text = "\n\n".join(f"{k.replace('_', ' ').capitalize()}: {t}" for k, t in resp.items() if k != "verdict_class")
        items.append(
            {
                "output_id": v["output_id"],
                "case_id": v["case_id"],
                "scenario": v["scenario"],
                "focal_claim": v["focal_claim"],
                "output": text,
                "m5": int(s["m5_unsupported_assertions"]),
                "m5_note": s["m5_note"],
                "human_quotes": human_quotes(s["m5_note"]) if int(s["m5_unsupported_assertions"]) else [],
            }
        )
    return items


def human_quotes(note: str) -> list[str]:
    """Claims the coder quoted in the M5 note. Some notes paraphrase instead;
    those outputs still count at item level but add no claim-level quotes."""
    pairs = re.findall(r'"([^"]{8,})"|“([^”]{8,})”', note)
    return [straight or curly for straight, curly in pairs]


def overlaps(a: str, b: str) -> bool:
    a, b = norm(a).lower().rstrip("."), norm(b).lower().rstrip(".")
    if a in b or b in a:
        return True
    ta, tb = set(re.findall(r"\w+", a)), set(re.findall(r"\w+", b))
    return bool(ta and tb) and len(ta & tb) / min(len(ta), len(tb)) >= 0.6


def pick(items: list[dict], split: str, n: int, seed: int) -> list[dict]:
    dev_ids = set(json.loads(DEV_SET.read_text())["output_ids"]) if DEV_SET.exists() else set()
    if split == "heldout":
        return [i for i in items if i["output_id"] not in dev_ids]
    if split == "devset":
        return [i for i in items if i["output_id"] in dev_ids]
    pool = [i for i in items if i["output_id"] not in dev_ids]
    rng = random.Random(seed)
    pos = sorted((i for i in pool if i["m5"] > 0), key=lambda i: i["output_id"])
    neg = sorted((i for i in pool if i["m5"] == 0), key=lambda i: i["output_id"])
    chosen = rng.sample(pos, n // 2) + rng.sample(neg, n - n // 2)
    DEV_SET.write_text(
        json.dumps({"seed": seed, "output_ids": sorted(dev_ids | {i["output_id"] for i in chosen})}, indent=2) + "\n"
    )
    return chosen


def score(item: dict, receipt: dict) -> dict:
    flagged = [c for c in receipt["claims"] if c["status"] in FLAGGED]
    matched = [q for q in item["human_quotes"] if any(overlaps(q, c["output_quote"]) for c in flagged)]
    return {
        "output_id": item["output_id"],
        "case_id": item["case_id"],
        "human_m5": item["m5"],
        "human_quotes": item["human_quotes"],
        "human_quotes_matched": matched,
        "engine_flags": [{"status": c["status"], "quote": c["output_quote"], "why": c["why"]} for c in flagged],
        "engine_needs_human": sum(c["status"] == "NEEDS_HUMAN_CHECK" for c in receipt["claims"]),
        "engine_claims": len(receipt["claims"]),
        "tokens": [receipt["run"]["input_tokens"], receipt["run"]["output_tokens"]],
    }


def summarise(rows: list[dict], split: str) -> str:
    tp = sum(r["human_m5"] > 0 and bool(r["engine_flags"]) for r in rows)
    fn = sum(r["human_m5"] > 0 and not r["engine_flags"] for r in rows)
    fp = sum(r["human_m5"] == 0 and bool(r["engine_flags"]) for r in rows)
    tn = sum(r["human_m5"] == 0 and not r["engine_flags"] for r in rows)
    hq = sum(len(r["human_quotes"]) for r in rows)
    hm = sum(len(r["human_quotes_matched"]) for r in rows)
    tin = sum(r["tokens"][0] for r in rows)
    tout = sum(r["tokens"][1] for r in rows)
    lines = [
        f"# ARGUS benchmark, {split} split ({len(rows)} outputs)",
        "",
        "Ground truth: blind human coding (M5, unsupported assertions), frozen 10 Aug 2026.",
        "Engine flag = at least one claim verified as UNSUPPORTED or CONTRADICTED.",
        "",
        "| | Human found unsupported claims | Human found none |",
        "|---|---|---|",
        f"| Engine flagged | {tp} | {fp} |",
        f"| Engine did not flag | {fn} | {tn} |",
        "",
        f"Human-quoted unsupported claims also flagged by the engine: {hm} of {hq}.",
        f"Tokens: {tin:,} in, {tout:,} out.",
        "",
    ]
    if split != "heldout":
        lines += ["Development split: used to inspect and tune. Not a reportable accuracy figure.", ""]
    lines += ["## Item by item", ""]
    for r in rows:
        lines.append(f"### {r['case_id']} {r['output_id'][:8]}: human M5 = {r['human_m5']}, engine flags = {len(r['engine_flags'])}")
        for q in r["human_quotes"]:
            mark = "matched" if q in r["human_quotes_matched"] else "MISSED"
            lines.append(f"- Human ({mark}): “{q}”")
        for f in r["engine_flags"]:
            lines.append(f"- Engine {f['status']}: “{f['quote']}”. {f['why']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=("dev", "devset", "heldout"), required=True,
                    help="dev: draw a new sample and add it to the dev set; devset: rerun the whole dev set; heldout: everything else")
    ap.add_argument("--n", type=int, default=16, help="dev sample size, half with human-coded unsupported claims")
    ap.add_argument("--seed", type=int, default=20261028)
    ap.add_argument("--env-file")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    items = pick(load_items(), a.split, a.n, a.seed)
    client = anthropic.Anthropic(api_key=load_key(a.env_file))
    out = pathlib.Path("runs") / f"argus-{a.split}-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    (out / "receipts").mkdir(parents=True)

    def run(item):
        ctx = (
            f'The output is an AI assessment of the focal claim "{item["focal_claim"]}". '
            "The source is the case scenario the AI was given; it was told to rely only on that evidence. "
            "Standard financial reasoning concepts are not claims about the case."
        )
        res = check(item["output"], {"scenario": item["scenario"]}, context=ctx, client=client)
        (out / "receipts" / f"{item['output_id']}.json").write_text(json.dumps(res.receipt, indent=2, ensure_ascii=False))
        return score(item, res.receipt)

    with ThreadPoolExecutor(a.workers) as pool:
        rows = list(pool.map(run, items))
    (out / "results.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    (out / "summary.md").write_text(summarise(rows, a.split))
    print(summarise(rows, a.split).split("## Item by item")[0])
    print(f"Written to {out}")


if __name__ == "__main__":
    main()
