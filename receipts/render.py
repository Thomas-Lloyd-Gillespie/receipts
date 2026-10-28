"""Render a receipt as a printable HTML page.

Quotes are shown exactly as verified. Only the model's own prose (why,
uncertainty) has long dashes evened out for display.
"""

from __future__ import annotations

import html

ATTENTION = ("CONTRADICTED", "UNSUPPORTED", "NEEDS_HUMAN_CHECK")


def _e(text: str) -> str:
    return html.escape(text)


def _prose(text: str) -> str:
    return html.escape(text.replace(" — ", ", ").replace("—", ", ").replace("–", "-"))


def _quotes(passages: list[dict]) -> str:
    if not passages:
        return "<i>Nothing in the sources</i>"
    return "<br>".join(f"<span class='src'>{_e(p['source'])}</span> “{_e(p['quote'])}”" for p in passages)


def _claim_rows(claims: list[dict], extra: str = "why") -> str:
    rows = []
    for c in claims:
        note = _prose(c["why"])
        if c.get("uncertainty"):
            note += f"<br><span class='unc'>Open question: {_prose(c['uncertainty'])}</span>"
        if extra == "problems" and c["problems"]:
            note += "<br><span class='prob'>" + "; ".join(_e(p) for p in c["problems"]) + "</span>"
        counter = ""
        if c.get("counter_quotes"):
            counter = f"<br><span class='ctr'>Cuts against it:</span><br>{_quotes(c['counter_quotes'])}"
        rows.append(
            f"<tr><td>“{_e(c['output_quote'])}”</td><td>{_quotes(c['source_quotes'])}{counter}</td><td>{note}</td></tr>"
        )
    return "".join(rows)


def _section(title: str, claims: list[dict], extra: str = "why") -> str:
    if not claims:
        return ""
    head = "<tr><th style='width:31%'>The output says</th><th style='width:36%'>The sources say</th><th>Why it matters</th></tr>"
    return f"<h2>{title}</h2><table>{head}{_claim_rows(claims, extra)}</table>"


def render(receipt: dict, title: str = "Receipt for an AI output", subtitle: str = "", banner: str = "") -> str:
    claims = receipt["claims"]
    by = {s: [c for c in claims if c["status"] == s] for s in ("SUPPORTED", *ATTENTION)}
    omissions = [o for o in receipt["omissions"] if o["status"] == "VERIFIED"]
    rejected = [o for o in receipt["omissions"] if o["status"] == "REJECTED"]
    attention = sum(len(by[s]) for s in ATTENTION)
    run, inputs = receipt["run"], receipt["inputs"]

    omission_rows = "".join(
        f"<tr><td><span class='src'>{_e(o['source'])}</span> “{_e(o['quote'])}”</td><td>{_prose(o['why'])}</td></tr>"
        for o in omissions
    )
    omission_html = (
        f"<h2>In the sources, left out of the output</h2><table><tr><th style='width:45%'>The sources say</th><th>Why it matters</th></tr>{omission_rows}</table>"
        if omissions
        else ""
    )
    source_lines = "".join(
        f"<tr><td>Source: {_e(s['name'])}</td><td>{s['sha256'][:16]}… ({s['chars']:,} characters)</td></tr>" for s in inputs["sources"]
    )
    banner_html = f"<div class='banner'>{banner}</div>" if banner else ""
    sub_html = f"<p class='sub'>{_e(subtitle)}</p>" if subtitle else ""

    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{_e(title)}</title><style>
@page {{ size: A4; margin: 16mm 15mm; }}
body {{ font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 9.6pt; color: #1d1d1f; line-height: 1.38; max-width: 190mm; margin: 0 auto; }}
h1 {{ font-family: Georgia, serif; font-size: 19pt; margin: 0 0 2pt; }}
h2 {{ font-family: Georgia, serif; font-size: 12.5pt; margin: 16pt 0 5pt; color: #7a2e1f; }}
.sub {{ color: #555; margin: 0 0 9pt; }}
.banner {{ background: #f6efe6; border-left: 3pt solid #7a2e1f; padding: 6pt 9pt; margin: 8pt 0; }}
.nums {{ display: flex; gap: 8pt; margin: 9pt 0 4pt; }}
.n {{ flex: 1; border: 0.6pt solid #d8d2c8; border-radius: 4pt; padding: 6pt 8pt; }}
.n b {{ display: block; font-family: Georgia, serif; font-size: 17pt; color: #7a2e1f; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 3pt; }}
th {{ text-align: left; font-size: 8.4pt; text-transform: uppercase; letter-spacing: .04em; color: #666; border-bottom: 0.8pt solid #999; padding: 3pt 5pt; }}
td {{ vertical-align: top; border-bottom: 0.5pt solid #e2ddd5; padding: 4.5pt 5pt; }}
tr {{ page-break-inside: avoid; }}
h2, tr:first-child, tr:nth-child(2) {{ break-after: avoid; }}
.src {{ font-size: 7.6pt; text-transform: uppercase; letter-spacing: .04em; color: #7a6a55; }}
.unc {{ color: #6b4e00; }}
.prob {{ color: #8a1c10; }}
.ctr {{ font-size: 8pt; color: #6b4e00; }}
.receipt td {{ font-family: Menlo, monospace; font-size: 8pt; border: none; padding: 1.5pt 5pt; }}
.foot {{ margin-top: 14pt; color: #666; font-size: 8.4pt; border-top: 0.5pt solid #ccc; padding-top: 5pt; }}
</style></head><body>
<h1>{_e(title)}</h1>
{sub_html}{banner_html}
<div class="nums">
<div class="n"><b>{len(claims)}</b>claims checked</div>
<div class="n"><b>{attention}</b>need attention</div>
<div class="n"><b>{len(omissions)}</b>facts left out</div>
</div>
<p>Every claim the output makes about the case was compared with the sources. Code then checked each quote word for word against the text it came from. A claim whose quotes did not check out is listed under "Needs a human check" and is never treated as verified.</p>
{_section("Doesn't match the sources", by["CONTRADICTED"])}
{_section("Not established by the sources", by["UNSUPPORTED"])}
{_section("Needs a human check", by["NEEDS_HUMAN_CHECK"], extra="problems")}
{omission_html}
{_section("Matches the sources", by["SUPPORTED"])}
<h2>The receipt</h2>
<table class="receipt">
<tr><td>Checked at</td><td>{_e(run["created_at"])}</td></tr>
<tr><td>Model</td><td>{_e(run["model"])} (prompt {_e(run["prompt_version"])}, engine {_e(run["engine_version"])})</td></tr>
<tr><td>Output</td><td>{inputs["output"]["sha256"][:16]}… ({inputs["output"]["chars"]:,} characters)</td></tr>
{source_lines}
<tr><td>Omissions rejected by code</td><td>{len(rejected)}</td></tr>
<tr><td>Receipt fingerprint</td><td>{receipt["receipt_sha256"]}</td></tr>
</table>
<h2>What this check does not do</h2>
<p>It does not decide whether the output is right or suitable. That judgement stays with the reviewer. It shows, with quotes from both sides, where the output and its sources disagree, what the sources do not establish, and what was left out, so the reviewer can go straight to those points.</p>
<p class="foot">TLG Systems Ltd. Engine {_e(run["engine_version"])}.</p>
</body></html>"""
