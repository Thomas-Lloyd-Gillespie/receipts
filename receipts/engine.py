"""Run one check and build its receipt.

One model call returns claims and omissions as JSON. Code then checks every
quote word for word. A claim with any failed check becomes NEEDS_HUMAN_CHECK
and an omission with a failed quote becomes REJECTED. An omission the
output does not leave out but contradicts (its passage is already the
evidence for a CONTRADICTED claim) becomes ALREADY_CONTRADICTED, so one
error is not counted twice. All of them stay on the
receipt with the reason, so the record shows what the model said as well as
what survived.
"""

from __future__ import annotations

import datetime
import json
from collections import Counter
from dataclasses import dataclass

from receipts.prompt import PROMPT_VERSION, build_prompt, build_schema
from receipts.verify import found, norm, sha256

ENGINE_VERSION = "0.1.1"
MODEL = "claude-opus-5-5"
MAX_TOKENS = 16000


@dataclass
class Result:
    receipt: dict
    raw_response: str


def check(output: str, sources: dict[str, str], *, context: str = "", client=None, model: str = MODEL) -> Result:
    if not sources:
        raise ValueError("at least one source is required")
    if client is None:
        import anthropic

        client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        output_config={"format": {"type": "json_schema", "schema": build_schema(list(sources))}},
        messages=[{"role": "user", "content": build_prompt(output, sources, context)}],
    )
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("model response was cut off at max_tokens; nothing was checked")
    raw = "".join(b.text for b in msg.content if b.type == "text")
    data = json.loads(raw)

    claims = [verify_claim(c, output, sources) for c in data["claims"]]
    omissions = [already_contradicted(verify_omission(o, sources), claims) for o in data["omissions"]]
    body = {
        "summary": {
            "claims": dict(Counter(c["status"] for c in claims)),
            "omissions": dict(Counter(o["status"] for o in omissions)),
        },
        "claims": claims,
        "omissions": omissions,
        "inputs": {
            "context": context,
            "output": {"sha256": sha256(output), "chars": len(output)},
            "sources": [{"name": n, "sha256": sha256(t), "chars": len(t)} for n, t in sources.items()],
        },
        "run": {
            "engine_version": ENGINE_VERSION,
            "prompt_version": PROMPT_VERSION,
            "model": model,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "request_id": getattr(msg, "_request_id", None),
            "input_tokens": msg.usage.input_tokens,
            "output_tokens": msg.usage.output_tokens,
            "raw_response_sha256": sha256(raw),
        },
    }
    body["receipt_sha256"] = sha256(json.dumps(body, sort_keys=True, ensure_ascii=False))
    return Result(receipt=body, raw_response=raw)


def verify_claim(claim: dict, output: str, sources: dict[str, str]) -> dict:
    problems = []
    if not found(claim["output_quote"], output):
        problems.append("output quote not found word for word in the output")
    for field, label in (("source_quotes", "source quote"), ("counter_quotes", "counter quote")):
        for p in claim[field]:
            if not found(p["quote"], sources.get(p["source"], "")):
                problems.append(f"{label} not found word for word in source '{p['source']}'")
    if claim["status"] in ("SUPPORTED", "CONTRADICTED") and not claim["source_quotes"]:
        problems.append(f"{claim['status']} claim has no source quote")
    out = dict(claim, model_status=claim["status"], problems=problems)
    if problems:
        out["status"] = "NEEDS_HUMAN_CHECK"
    return out


def verify_omission(omission: dict, sources: dict[str, str]) -> dict:
    ok = found(omission["quote"], sources.get(omission["source"], ""))
    problems = [] if ok else [f"quote not found word for word in source '{omission['source']}'"]
    return dict(omission, status="VERIFIED" if ok else "REJECTED", problems=problems)


def already_contradicted(omission: dict, claims: list[dict]) -> dict:
    if omission["status"] != "VERIFIED":
        return omission
    quote = norm(omission["quote"])
    for c in claims:
        if c["status"] != "CONTRADICTED":
            continue
        for p in c["source_quotes"]:
            cited = norm(p["quote"])
            if p["source"] == omission["source"] and (quote in cited or cited in quote):
                return dict(omission, status="ALREADY_CONTRADICTED", contradicts=c["output_quote"])
    return omission
