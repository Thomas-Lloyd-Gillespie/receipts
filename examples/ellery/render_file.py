"""Print the fictional Ellery advice file (fact-find and draft report) as one PDF-ready page.

    uv run python examples/ellery/render_file.py > runs/ellery-file.html
"""

from __future__ import annotations

import html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from receipts.render import FONTS  # noqa: E402

HERE = pathlib.Path(__file__).parent


def _e(text: str) -> str:
    return html.escape(text)


def factfind(text: str) -> str:
    lines = [l for l in text.splitlines()[1:] if l.strip()]
    out, rows = [f"<p class='kicker'>{_e(lines[0])}</p><p class='meta'>{_e(lines[1])}</p>"], []

    def flush():
        if rows:
            out.append("<table>" + "".join(rows) + "</table>")
            rows.clear()

    for line in lines[2:]:
        if re.match(r"^\d+\. ", line):
            flush()
            num, title = line.split(". ", 1)
            out.append(f"<h3><span>{num}</span>{_e(title)}</h3>")
        elif re.match(r"^[a-c]\) ", line) or ":" not in line[:40]:
            rows.append(f"<tr><td colspan='2'>{_e(line)}</td></tr>")
        else:
            label, value = line.split(":", 1)
            rows.append(f"<tr><th>{_e(label)}</th><td>{_e(value.strip())}</td></tr>")
    flush()
    return "".join(out)


def report(text: str) -> str:
    lines = [l for l in text.splitlines()[1:] if l.strip()]
    out = [f"<p class='to'>{_e(lines[0])}</p>"]
    for line in lines[1:]:
        if not line.rstrip().endswith(".") and len(line) < 40:
            out.append(f"<h3>{_e(line)}</h3>")
        else:
            out.append(f"<p>{_e(line)}</p>")
    return "".join(out)


def page() -> str:
    ff = (HERE / "factfind.txt").read_text()
    sr = (HERE / "report.txt").read_text()
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>Fictional advice file: Ellery</title>
<link rel="stylesheet" href="{FONTS}">
<style>
:root {{ --ink:#121417; --muted:#59616b; --faint:#8a929c; --rule:#d7dbe0; --hair:#e9ecef;
  --sans:"Libre Franklin",Arial,sans-serif; --serif:"Source Serif 4",Georgia,serif; --mono:"JetBrains Mono",Menlo,monospace; }}
@page {{ size: A4; margin: 17mm 16mm 18mm;
  @bottom-left {{ content: "Fictional advice file. For demonstration only."; font: 7.5pt "Libre Franklin", Arial, sans-serif; color: #8a929c; }}
  @bottom-right {{ content: "Page " counter(page) " of " counter(pages); font: 7.5pt "Libre Franklin", Arial, sans-serif; color: #8a929c; }} }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ margin: 0 auto; max-width: 178mm; color: var(--ink); font: 10pt/1.5 var(--serif); }}
.mast {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2.2pt solid var(--ink); padding-bottom: 5pt; font: 800 11pt var(--sans); }}
.mast span {{ font-weight: 400; color: var(--muted); }}
.mast .r {{ font: 500 8.5pt var(--mono); color: var(--muted); }}
.notice {{ font: 8.8pt/1.45 var(--sans); border: .8pt solid var(--ink); padding: 2.4mm 3mm; margin: 6mm 0 2mm; }}
h1 {{ font: 800 20pt/1.1 var(--sans); margin: 9mm 0 1mm; }}
h2 {{ font: 800 15pt/1.2 var(--sans); margin: 0 0 1mm; }}
.part {{ font: 700 7pt var(--sans); letter-spacing: .14em; text-transform: uppercase; color: var(--muted); margin: 0 0 1mm; }}
.kicker {{ font: 700 7.6pt var(--sans); letter-spacing: .12em; text-transform: uppercase; margin: 4mm 0 0; }}
.meta {{ color: var(--muted); font-size: 9.4pt; margin: 0 0 3mm; }}
h3 {{ font: 700 9.4pt var(--sans); margin: 5mm 0 1.2mm; border-bottom: 1.2pt solid var(--ink); padding-bottom: 1mm; break-after: avoid; }}
h3 span {{ font: 500 8.4pt var(--mono); color: var(--muted); margin-right: 3mm; }}
table {{ width: 100%; border-collapse: collapse; }}
tr {{ break-inside: avoid; }}
th, td {{ text-align: left; vertical-align: top; padding: 1.3mm 3mm 1.3mm 0; border-bottom: .5pt solid var(--hair); font-size: 9.4pt; }}
th {{ font: 500 8.4pt/1.5 var(--sans); color: var(--muted); width: 52mm; }}
.report {{ break-before: page; }}
.report .letter {{ border-top: 1.4pt solid var(--ink); padding-top: 4mm; margin-top: 4mm; }}
.report h3 {{ border: none; padding: 0; margin: 5mm 0 1mm; font-size: 10pt; }}
.report p {{ margin: 0 0 1.6mm; font-size: 10.4pt; }}
.to {{ font-style: italic; color: var(--muted); }}
</style></head><body>
<header class="mast"><div>Ellery <span>Advice file</span></div><div class="r">FICTIONAL</div></header>
<div class="notice"><b>Made up for demonstration.</b> David and Margaret Ellery are fictional. The draft report was written with errors planted on purpose, to test the check. No real client data is used anywhere in this file.</div>
<h1>Lifetime mortgage enquiry</h1>
<p class="meta">Fact-find, then the AI-assisted draft suitability report that was checked against it.</p>
<p class="part">Part 1</p><h2>Fact-find</h2>
{factfind(ff)}
<section class="report"><p class="part">Part 2</p><h2>Suitability report, AI-assisted draft</h2>
<div class="letter">{report(sr)}</div></section>
</body></html>"""


if __name__ == "__main__":
    print(page())
