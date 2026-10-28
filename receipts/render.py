"""Render a receipt as a printable document.

Modelled on documents people already trust for this job: a fact check (the
verdict is the headline; what was claimed sits beside what is true), an
assurance report (conclusion first, then subject, criteria, basis and
limits), and a file checker's marked-up report (numbered findings keyed to
the exact passages). Quotes are shown exactly as verified. Only the model's
own prose has long dashes evened out for display.
"""

from __future__ import annotations

import datetime
import html
import re

from receipts.verify import sha256

LABELS = {
    "CONTRADICTED": "Contradicted",
    "UNSUPPORTED": "Not established",
    "NEEDS_HUMAN_CHECK": "Check by hand",
    "SUPPORTED": "Consistent",
}
CLASS = {"CONTRADICTED": "con", "UNSUPPORTED": "uns", "NEEDS_HUMAN_CHECK": "chk", "SUPPORTED": "ok"}
ATTENTION = ("CONTRADICTED", "UNSUPPORTED", "NEEDS_HUMAN_CHECK")
FONTS = (
    "https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;500;700;800"
    "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400"
    "&family=JetBrains+Mono:wght@400;500&display=swap"
)


def _e(text: str) -> str:
    return html.escape(text)


def _prose(text: str) -> str:
    return html.escape(text.replace(" — ", ", ").replace("—", ", ").replace("–", "-"))


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def receipt_number(receipt: dict) -> str:
    h = receipt["receipt_sha256"].upper()
    return f"R-{h[:4]}-{h[4:8]}"


def default_source_phrase(receipt: dict) -> str:
    names = [s["name"] for s in receipt["inputs"]["sources"]]
    return f"the {names[0][0].lower()}{names[0][1:]}" if len(names) == 1 else "its sources"


def headline(receipt: dict, output_label: str, source_phrase: str) -> str:
    """The verdict as one sentence, built from the counts. No model writes it."""
    claims = receipt["claims"]
    n = {s: sum(c["status"] == s for c in claims) for s in LABELS}
    left_out = sum(o["status"] == "VERIFIED" for o in receipt["omissions"])
    parts = []
    if n["CONTRADICTED"]:
        parts.append(f"contradicts {source_phrase} in {_plural(n['CONTRADICTED'], 'place')}")
    if n["UNSUPPORTED"]:
        verb = "do" if len(receipt["inputs"]["sources"]) > 1 else "does"
        parts.append(f"makes {_plural(n['UNSUPPORTED'], 'claim')} {source_phrase} {verb} not support")
    if left_out:
        parts.append(f"leaves out {_plural(left_out, 'fact')}")
    if n["NEEDS_HUMAN_CHECK"]:
        parts.append(f"has {_plural(n['NEEDS_HUMAN_CHECK'], 'claim')} to check by hand")
    if not parts:
        return f"{output_label} is consistent with {source_phrase} on all {_plural(len(claims), 'claim')} checked."
    body = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return f"{output_label} {body}."


def _ordered(claims: list[dict], text: str | None) -> list[dict]:
    if not text:
        return claims
    pos = {id(c): (_locate(c["output_quote"], text) or (len(text), 0))[0] for c in claims}
    return sorted(claims, key=lambda c: pos[id(c)])


def _pattern(quote: str) -> str:
    out = []
    for token in quote.split():
        t = re.escape(token)
        t = t.replace("'", "['‘’]").replace('"', '["“”]').replace(r"\-", "[-–—]")
        out.append(t)
    return r"\s+".join(out)


def _locate(quote: str, text: str) -> tuple[int, int] | None:
    if not quote.strip():
        return None
    m = re.search(_pattern(quote), text)
    return (m.start(), m.end()) if m else None


def _passages(passages: list[dict]) -> str:
    return "".join(
        f"<blockquote class='src'><p>{_e(p['quote'])}</p><cite>{_e(p['source'])}</cite></blockquote>" for p in passages
    )


def _finding(ref: str, c: dict, output_label: str) -> str:
    status = c["status"]
    extra = ""
    if c.get("counter_quotes"):
        extra += f"<p class='sub-label'>Cuts against it</p>{_passages(c['counter_quotes'])}"
    if c.get("uncertainty"):
        extra += f"<p class='note'><b>Open question.</b> {_prose(c['uncertainty'])}</p>"
    if status == "NEEDS_HUMAN_CHECK" and c.get("problems"):
        extra += "<p class='note'><b>Why it failed verification.</b> " + "; ".join(_e(p) for p in c["problems"]) + ".</p>"
    sources = _passages(c["source_quotes"]) or "<p class='none'>Nothing in the sources bears on this.</p>"
    return f"""<section class="finding {CLASS[status]}">
<div class="gutter"><span class="ref">{ref}</span><span class="tag">{LABELS[status]}</span></div>
<div class="body">
<p class="sub-label">{_e(output_label)} says</p>
<blockquote class="claim"><p>{_e(c['output_quote'])}</p></blockquote>
<p class="sub-label">The sources say</p>
{sources}
<p class="why"><b>{LABELS[status]}.</b> {_prose(c['why'])}</p>
{extra}
</div></section>"""


def _markup(text: str, marks: list[tuple[str, str, str]]) -> str:
    spans = []
    for ref, status, quote in marks:
        loc = _locate(quote, text)
        if loc:
            spans.append((loc[0], loc[1], ref, status))
    spans.sort()
    out, cursor = [], 0
    for start, end, ref, status in spans:
        if start < cursor:
            continue
        out.append(_e(text[cursor:start]))
        out.append(f"<mark class='{CLASS[status]}'>{_e(text[start:end])}</mark><sup class='{CLASS[status]}'>{ref}</sup>")
        cursor = end
    out.append(_e(text[cursor:]))
    return "".join(out)


def render(
    receipt: dict,
    title: str = "Receipt for an AI output",
    subtitle: str = "",
    banner: str = "",
    output_text: str | None = None,
    output_label: str = "The output",
    source_phrase: str | None = None,
    toolbar: str = "",
) -> str:
    """toolbar is HTML shown above the receipt on screen only, never in print."""
    if output_text is not None and sha256(output_text) != receipt["inputs"]["output"]["sha256"]:
        raise ValueError("output_text is not the text this receipt was made from")
    run, inputs = receipt["run"], receipt["inputs"]
    if source_phrase is None:
        source_phrase = default_source_phrase(receipt)

    claims = receipt["claims"]
    attention = [c for s in ATTENTION for c in _ordered([c for c in claims if c["status"] == s], output_text)]
    consistent = _ordered([c for c in claims if c["status"] == "SUPPORTED"], output_text)
    omissions = [o for o in receipt["omissions"] if o["status"] == "VERIFIED"]
    rejected = [o for o in receipt["omissions"] if o["status"] == "REJECTED"]
    doubled = [o for o in receipt["omissions"] if o["status"] == "ALREADY_CONTRADICTED"]
    refs = {id(c): f"F{i}" for i, c in enumerate(attention, 1)}
    refs.update({id(c): f"C{i}" for i, c in enumerate(consistent, 1)})

    checked = datetime.datetime.fromisoformat(run["created_at"])
    when = f"{checked:%-d %B %Y}, {checked:%H:%M} UTC"
    number = receipt_number(receipt)
    verdict = headline(receipt, output_label, source_phrase)

    index = "".join(
        f"<li class='{CLASS[c['status']]}'><span class='ref'>{refs[id(c)]}</span><span class='tag'>{LABELS[c['status']]}</span>"
        f"<span class='q'>{_e(c['output_quote'])}</span></li>"
        for c in attention
    )
    if omissions:
        index += (
            f"<li class='left'><span class='ref'>L1\u2013{len(omissions)}</span><span class='tag'>Left out</span>"
            f"<span class='q'>{_plural(len(omissions), 'fact')} in {_e(source_phrase)}, listed in full below</span></li>"
            if len(omissions) > 1
            else f"<li class='left'><span class='ref'>L1</span><span class='tag'>Left out</span><span class='q'>{_e(omissions[0]['quote'])}</span></li>"
        )
    findings = "".join(_finding(refs[id(c)], c, output_label) for c in attention)
    left_out = "".join(
        f"""<section class="finding left"><div class="gutter"><span class="ref">L{i}</span><span class="tag">Left out</span></div>
<div class="body">{_passages([o])}<p class="why"><b>Left out.</b> {_prose(o['why'])}</p></div></section>"""
        for i, o in enumerate(omissions, 1)
    )
    consistent_rows = "".join(
        f"<tr><td class='ref'>{refs[id(c)]}</td><td>{_e(c['output_quote'])}</td><td>"
        + "<br>".join(f"{_e(p['quote'])} <cite>{_e(p['source'])}</cite>" for p in c["source_quotes"])
        + (f"<div class='note'><b>Open question.</b> {_prose(c['uncertainty'])}</div>" if c.get("uncertainty") else "")
        + (
            "<div class='note'><b>Cuts against it.</b> "
            + "; ".join(f"{_e(p['quote'])} <cite>{_e(p['source'])}</cite>" for p in c["counter_quotes"])
            + "</div>"
            if c.get("counter_quotes")
            else ""
        )
        + "</td></tr>"
        for c in consistent
    )
    source_meta = "".join(
        f"<dt>Checked against</dt><dd>{_e(s['name'])}<span class='hash'>{s['sha256'][:12]}</span></dd>" for s in inputs["sources"]
    )
    source_rows = "".join(
        f"<tr><th>Source: {_e(s['name'])}</th><td>sha256 {s['sha256']}<br>{s['chars']:,} characters</td></tr>" for s in inputs["sources"]
    )
    appendix = ""
    if output_text is not None:
        marks = [(refs[id(c)], c["status"], c["output_quote"]) for c in attention + consistent]
        appendix = f"""<section class="appendix"><h2><span class="num">Part {{n}}</span>{_e(output_label)}, marked up</h2>
<p class="lede">The full text that was checked. Each marked passage carries the number of its finding: red contradicts the sources, amber is not established by them, green is consistent.</p>
<div class="doc">{_markup(output_text, marks)}</div></section>"""
    parts = iter(range(1, 10))
    if appendix:
        appendix = appendix.replace("{n}", str(next(parts)))
    attention_part, left_part = next(parts), next(parts) if omissions else None
    consistent_part, basis_part, verify_part = next(parts), next(parts), next(parts)
    banner_html = f"<div class='banner'>{banner}</div>" if banner else ""
    subtitle_html = f"<p class='subject'>{_e(subtitle)}</p>" if subtitle else ""

    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{_e(title)} ({number})</title>
<link rel="stylesheet" href="{FONTS}">
<style>
:root {{ --ink:#121417; --muted:#59616b; --faint:#8a929c; --rule:#d7dbe0; --hair:#e9ecef; --paper:#fff;
  --con:#b0241b; --con-bg:#fbe6e3; --uns:#8f5d00; --uns-bg:#fbefd5; --chk:#5b3fa0; --chk-bg:#ece6f7; --ok:#2c6a4a; --ok-bg:#e3f0e8; --left:#1d4f8f; --left-bg:#e3ecf7;
  --sans:"Libre Franklin","Franklin Gothic Medium","Helvetica Neue",Arial,sans-serif; --serif:"Source Serif 4",Charter,"Iowan Old Style",Georgia,serif; --mono:"JetBrains Mono",Menlo,monospace; }}
@page {{ size: A4; margin: 17mm 16mm 18mm 16mm;
  @bottom-left {{ content: "{number}"; font: 7.5pt "JetBrains Mono", Menlo, monospace; color: #8a929c; }}
  @bottom-right {{ content: "Page " counter(page) " of " counter(pages); font: 7.5pt "Libre Franklin", Arial, sans-serif; color: #8a929c; }} }}
* {{ box-sizing: border-box; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ margin: 0 auto; max-width: 178mm; background: var(--paper); color: var(--ink); font: 10pt/1.5 var(--serif); }}
.mast {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2.2pt solid var(--ink); padding-bottom: 5pt; }}
.mark {{ font: 800 11pt var(--sans); letter-spacing: .02em; }}
.mark span {{ font-weight: 400; color: var(--muted); }}
.mast .no {{ font: 500 8.5pt var(--mono); color: var(--muted); }}
.top {{ display: grid; grid-template-columns: 47mm 1fr; gap: 0 8mm; margin-top: 9mm; }}
.rail {{ font: 8.4pt/1.45 var(--sans); color: var(--muted); border-top: .6pt solid var(--rule); padding-top: 3mm; }}
.rail dt {{ font-weight: 700; color: var(--ink); text-transform: uppercase; font-size: 6.8pt; letter-spacing: .09em; margin-top: 4mm; }}
.rail dt:first-child {{ margin-top: 0; }}
.rail dd {{ margin: 1pt 0 0; }}
.rail .hash {{ display: block; font: 7.4pt var(--mono); color: var(--faint); }}
.kicker {{ font: 700 7.6pt var(--sans); letter-spacing: .14em; text-transform: uppercase; color: var(--con); margin: 0 0 3mm; }}
h1 {{ font: 800 23pt/1.08 var(--sans); letter-spacing: -.012em; margin: 0 0 4mm; }}
.subject {{ font: italic 11pt/1.45 var(--serif); color: var(--muted); margin: 0 0 5mm; }}
.banner {{ font: 8.6pt/1.45 var(--sans); border: .8pt solid var(--ink); padding: 2.4mm 3mm; margin: 0 0 5mm; }}
.conclusion {{ border-top: .6pt solid var(--rule); padding-top: 3mm; }}
.label {{ font: 700 6.8pt var(--sans); letter-spacing: .09em; text-transform: uppercase; margin: 0 0 1.5mm; }}
.conclusion p {{ margin: 0 0 2.5mm; }}
.index {{ list-style: none; margin: 7mm 0 0; padding: 0; border-top: 1.4pt solid var(--ink); }}
.index li {{ display: grid; grid-template-columns: 11mm 26mm 1fr; gap: 3mm; padding: 1.3mm 0; border-bottom: .5pt solid var(--hair); font: 8.8pt/1.4 var(--sans); break-inside: avoid; }}
.index .ref {{ font: 500 8.4pt var(--mono); color: var(--muted); }}
.index .tag {{ font-weight: 700; font-size: 7.4pt; text-transform: uppercase; letter-spacing: .07em; padding-top: .6pt; }}
.index .q {{ font-family: var(--serif); font-size: 9.4pt; }}
li.con .tag, .finding.con .tag {{ color: var(--con); }} li.uns .tag, .finding.uns .tag {{ color: var(--uns); }}
li.chk .tag, .finding.chk .tag {{ color: var(--chk); }} li.left .tag, .finding.left .tag {{ color: var(--left); }}
h2 {{ font: 800 14pt/1.2 var(--sans); margin: 11mm 0 1.5mm; break-after: avoid; break-inside: avoid; }}
h2 .num {{ display: block; font: 700 7pt var(--sans); letter-spacing: .14em; text-transform: uppercase; color: var(--muted); margin-bottom: 1.2mm; }}
.lede {{ color: var(--muted); margin: 0 0 4mm; font-size: 9.6pt; }}
.finding {{ display: grid; grid-template-columns: 26mm 1fr; gap: 0 6mm; border-top: .6pt solid var(--rule); padding: 4mm 0 3mm; break-inside: avoid; }}
.gutter .ref {{ display: block; font: 800 17pt/1 var(--sans); }}
.gutter .tag {{ display: block; margin-top: 1.6mm; font: 700 7pt var(--sans); letter-spacing: .08em; text-transform: uppercase; }}
.sub-label {{ font: 700 6.8pt var(--sans); letter-spacing: .09em; text-transform: uppercase; color: var(--muted); margin: 0 0 1.2mm; }}
blockquote {{ margin: 0 0 3mm; }}
blockquote p {{ margin: 0; }}
.claim p {{ font-size: 11.6pt; line-height: 1.4; padding-left: 3mm; border-left: 2.2pt solid var(--ink); }}
.finding.con .claim p {{ border-color: var(--con); }} .finding.uns .claim p {{ border-color: var(--uns); }} .finding.chk .claim p {{ border-color: var(--chk); }}
.src p {{ padding-left: 3mm; border-left: .8pt solid var(--rule); }}
.src cite, td cite {{ display: block; padding-left: 3mm; font: normal 700 6.6pt var(--sans); letter-spacing: .09em; text-transform: uppercase; color: var(--faint); margin-top: .8mm; }}
td cite {{ display: inline; padding: 0; }}
.none {{ font-style: italic; color: var(--muted); margin: 0 0 3mm; }}
.why {{ margin: 0 0 2mm; }}
.note {{ font-size: 9.2pt; color: var(--muted); margin: 1mm 0 2mm; }}
.note b {{ color: var(--ink); }}
table {{ width: 100%; border-collapse: collapse; }}
.consistent td {{ vertical-align: top; padding: 2.2mm 2.5mm 2.2mm 0; border-bottom: .5pt solid var(--hair); font-size: 9.2pt; line-height: 1.42; }}
.consistent tr {{ break-inside: avoid; }}
.consistent td.ref {{ font: 500 8.2pt var(--mono); color: var(--ok); width: 9mm; }}
.consistent td:nth-child(2) {{ width: 44%; }}
.basis {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0 8mm; font-size: 9.4pt; }}
.basis h3 {{ font: 700 8.6pt var(--sans); margin: 0 0 1.5mm; }}
.basis p {{ margin: 0 0 3mm; }}
.verify th {{ text-align: left; font: 700 7.6pt var(--sans); padding: 1.4mm 4mm 1.4mm 0; width: 38mm; vertical-align: top; border-bottom: .5pt solid var(--hair); }}
.verify td {{ font: 7.8pt/1.5 var(--mono); padding: 1.4mm 0; border-bottom: .5pt solid var(--hair); word-break: break-all; }}
.appendix, h2.first {{ break-before: page; }}
.appendix h2 {{ margin-top: 0; }} h2.first {{ margin-top: 0; }}
.doc {{ white-space: pre-wrap; font-size: 9.8pt; line-height: 1.62; border-top: 1.4pt solid var(--ink); padding-top: 4mm; }}
mark {{ color: inherit; padding: .3pt 0; }}
mark.con {{ background: var(--con-bg); box-shadow: inset 0 -1.2pt var(--con); }} mark.uns {{ background: var(--uns-bg); box-shadow: inset 0 -1.2pt var(--uns); }}
mark.chk {{ background: var(--chk-bg); box-shadow: inset 0 -1.2pt var(--chk); }} mark.ok {{ background: none; box-shadow: inset 0 -.8pt var(--ok); }}
sup {{ font: 700 6.4pt var(--sans); margin-left: .6pt; }}
sup.con {{ color: var(--con); }} sup.uns {{ color: var(--uns); }} sup.chk {{ color: var(--chk); }} sup.ok {{ color: var(--ok); }}
.end {{ margin-top: 9mm; border-top: .6pt solid var(--rule); padding-top: 2mm; font: 7.8pt var(--sans); color: var(--faint); }}
.toolbar {{ display: flex; flex-wrap: wrap; gap: 4px 18px; align-items: baseline; padding: 10px 0; margin-bottom: 18px; border-bottom: .6pt solid var(--rule); font: 9pt var(--sans); }}
.toolbar a, .toolbar button {{ font: inherit; color: var(--ink); background: none; border: 0; padding: 0; cursor: pointer; text-decoration: underline; text-underline-offset: 2px; }}
.toolbar .end-bar {{ margin-left: auto; color: var(--faint); font-family: var(--mono); }}
@media screen {{ body {{ padding: 0 16px 48px; }} .mast {{ padding-top: 14px; }}
  .appendix, h2.first {{ margin-top: 16mm; padding-top: 5mm; border-top: 2.2pt solid var(--ink); }} }}
@media screen and (max-width: 720px) {{
  body {{ font-size: 10.5pt; }}
  .top, .finding, .basis {{ grid-template-columns: 1fr; }}
  .rail {{ order: 2; margin-top: 6mm; }}
  h1 {{ font-size: 19pt; }}
  .index li {{ grid-template-columns: 11mm 1fr; }}
  .index .q {{ grid-column: 2; }}
  .gutter {{ display: flex; align-items: baseline; gap: 10px; margin-bottom: 2mm; }}
  .gutter .tag {{ margin-top: 0; }}
  .consistent tr {{ display: grid; grid-template-columns: 9mm 1fr; }}
  .consistent td:nth-child(2) {{ width: auto; }}
  .consistent td:nth-child(3) {{ grid-column: 2; padding-top: 0; }}
  .verify th {{ width: 28mm; }}
}}
@media print {{ .toolbar {{ display: none; }} }}
</style></head><body>
{toolbar}
<header class="mast"><div class="mark">TLG Systems <span>Receipt</span></div><div class="no">{number}</div></header>
<div class="top">
<dl class="rail">
<dt>Receipt</dt><dd>{number}</dd>
<dt>Checked</dt><dd>{when}</dd>
<dt>Subject</dt><dd>{_e(output_label)}<span class="hash">{inputs['output']['sha256'][:12]}</span></dd>
{source_meta}
<dt>Method</dt><dd>One model reading, then every quote checked word for word by code</dd>
<dt>Model</dt><dd>{_e(run['model'])}<span class="hash">prompt {_e(run['prompt_version'])}, engine {_e(run['engine_version'])}</span></dd>
</dl>
<main>
<p class="kicker">{_e(title)}</p>
<h1>{_e(verdict)}</h1>
{subtitle_html}{banner_html}
<div class="conclusion"><p class="label">Conclusion</p>
<p>Of {_plural(len(claims), 'claim')} {_e(output_label[0].lower() + output_label[1:])} makes about the case, {len(attention)} need attention and {len(consistent)} are consistent with {_e(source_phrase)}. {_plural(len(omissions), 'fact')} in {_e(source_phrase)} {'is' if len(omissions) == 1 else 'are'} left out. Every quote in this receipt was matched word for word against the document it comes from.</p>
<p>This receipt does not judge whether the output is right or suitable. That decision stays with the reviewer.</p></div>
<ol class="index">{index}</ol>
</main></div>
{appendix}
<h2 class="first"><span class="num">Part {attention_part}</span>What needs attention</h2>
<p class="lede">Each finding sets what {_e(output_label[0].lower() + output_label[1:])} says beside what the sources say.</p>
{findings}
{f'<h2><span class="num">Part {left_part}</span>In the sources, left out</h2><p class="lede">Facts the sources record that {_e(output_label[0].lower() + output_label[1:])} does not reflect.</p>' + left_out if omissions else ''}
<h2><span class="num">Part {consistent_part}</span>Consistent with the sources</h2>
<table class="consistent">{consistent_rows}</table>

<h2><span class="num">Part {basis_part}</span>Basis and limits</h2>
<div class="basis">
<div><h3>How this was checked</h3><p>A language model read the output and the sources and proposed each claim, its status and the passages it rests on. Code then matched every quote word for word against the document it names. A claim whose quotes did not match is listed as "Check by hand", never as a finding. {"No proposed omission failed that test." if not rejected else _plural(len(rejected), "proposed omission") + " failed that test and " + ("was" if len(rejected) == 1 else "were") + " left out of this receipt."}{"" if not doubled else " " + _plural(len(doubled), "proposed omission") + (" was" if len(doubled) == 1 else " were") + " already the evidence for a contradiction above, so " + ("it is" if len(doubled) == 1 else "they are") + " not counted again as left out."}</p></div>
<div><h3>What this receipt does not cover</h3><p>It does not decide whether the output is right, suitable or compliant. It does not check facts against anything outside the sources listed. A claim marked consistent means the sources say the same, not that the sources are correct.</p></div>
</div>
<h2><span class="num">Part {verify_part}</span>Verification</h2>
<p class="lede">Anyone holding the same files can recompute these fingerprints. If a file changes by one character, its fingerprint will not match.</p>
<table class="verify">
<tr><th>Receipt</th><td>{number}<br>sha256 {receipt['receipt_sha256']}</td></tr>
<tr><th>Output checked</th><td>sha256 {inputs['output']['sha256']}<br>{inputs['output']['chars']:,} characters</td></tr>
{source_rows}
<tr><th>Model response</th><td>sha256 {run['raw_response_sha256']}<br>{run['input_tokens']:,} tokens in, {run['output_tokens']:,} out{('<br>request ' + _e(run['request_id'])) if run.get('request_id') else ''}</td></tr>
</table>
<p class="end">TLG Systems Ltd. Receipt {number}. Engine {_e(run['engine_version'])}.</p>
</body></html>"""
