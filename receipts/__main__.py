"""Command line.

    python -m receipts check --output FILE --source NAME=FILE [...]
    python -m receipts serve [--port 8765] [--env-file PATH]
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib

import anthropic

from receipts.engine import MODEL, check
from receipts.keys import load_key
from receipts.render import render


def main() -> None:
    ap = argparse.ArgumentParser(prog="receipts")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check one AI output against its sources")
    c.add_argument("--output", required=True, help="file holding the AI output")
    c.add_argument("--source", action="append", required=True, metavar="NAME=FILE", help="a source record (repeatable)")
    c.add_argument("--context", default="", help="one line telling the checker what the output is for")
    c.add_argument("--title", default="Receipt for an AI output")
    c.add_argument("--banner", default="", help="HTML shown in a box under the headline")
    c.add_argument("--output-label", default="The output", help='how to name the output in sentences, e.g. "The draft report"')
    c.add_argument("--source-phrase", help='how to name the sources in sentences, e.g. "the fact-find"')
    c.add_argument("--out", help="directory for receipt.json, receipt.html and raw_response.txt")
    c.add_argument("--env-file", help="a .env file holding ANTHROPIC_API_KEY")
    c.add_argument("--model", default=MODEL)
    s = sub.add_parser("serve", help="run the paste page on this computer")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--runs-dir", default="runs/web", help="where receipts are saved")
    s.add_argument("--env-file", help="a .env file holding ANTHROPIC_API_KEY")
    s.add_argument("--model", default=MODEL)
    a = ap.parse_args()

    if a.cmd == "serve":
        import uvicorn

        from receipts.web import create_app

        client = anthropic.Anthropic(api_key=load_key(a.env_file))
        print(f"Open http://127.0.0.1:{a.port} (Ctrl+C to stop)")
        uvicorn.run(create_app(client, a.runs_dir, a.model), host="127.0.0.1", port=a.port, log_level="warning")
        return

    output = pathlib.Path(a.output).read_text()
    sources = {}
    for spec in a.source:
        name, _, path = spec.partition("=")
        if not path:
            ap.error(f"--source needs NAME=FILE, got {spec!r}")
        sources[name] = pathlib.Path(path).read_text()

    client = anthropic.Anthropic(api_key=load_key(a.env_file))
    result = check(output, sources, context=a.context, client=client, model=a.model)

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = pathlib.Path(a.out or f"runs/check-{stamp}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "receipt.json").write_text(json.dumps(result.receipt, indent=2, ensure_ascii=False))
    (out / "raw_response.txt").write_text(result.raw_response)
    page = render(result.receipt, title=a.title, subtitle=a.context, banner=a.banner, output_text=output,
                  output_label=a.output_label, source_phrase=a.source_phrase)
    (out / "receipt.html").write_text(page)
    r = result.receipt
    print(json.dumps({"summary": r["summary"], "tokens": [r["run"]["input_tokens"], r["run"]["output_tokens"]], "out": str(out)}))


if __name__ == "__main__":
    main()
