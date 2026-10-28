"""The paste page: put in an AI output and its sources, get a receipt back.

    uv run python -m receipts serve --env-file PATH

Runs on this computer only. Each check is saved under runs/web/<receipt number>/
with its inputs, so any receipt can be shown again and its fingerprints rechecked.
"""

from __future__ import annotations

import datetime
import html
import json
import pathlib
import re

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from receipts.engine import ENGINE_VERSION, MODEL, check
from receipts.prompt import PROMPT_VERSION
from receipts.render import default_source_phrase, headline, receipt_number, render

HERE = pathlib.Path(__file__).parent
EXAMPLE = HERE.parent / "examples" / "ellery"
RECEIPT_ID = re.compile(r"R-[0-9A-F]{4}-[0-9A-F]{4}")
MAX_CHARS = 200_000
MAX_SOURCES = 6


class Source(BaseModel):
    name: str
    text: str


class CheckRequest(BaseModel):
    output: str
    sources: list[Source]
    title: str = ""
    context: str = ""
    output_label: str = ""
    banner: str = ""


def problems(req: CheckRequest) -> list[str]:
    """Everything wrong with a request, in the words the page shows."""
    out = []
    if not req.output.strip():
        out.append("Paste the AI output you want checked.")
    if not req.sources:
        out.append("Add at least one source.")
    if len(req.sources) > MAX_SOURCES:
        out.append(f"Use {MAX_SOURCES} sources or fewer.")
    for i, s in enumerate(req.sources, 1):
        if not s.name.strip():
            out.append(f"Give source {i} a name.")
        if not s.text.strip():
            out.append(f"Paste the text of source {i}.")
    names = [s.name.strip() for s in req.sources if s.name.strip()]
    twice = sorted({n for n in names if names.count(n) > 1})
    if twice:
        out.append("Each source needs its own name. Used more than once: " + ", ".join(twice) + ".")
    total = len(req.output) + sum(len(s.text) for s in req.sources)
    if total > MAX_CHARS:
        out.append(f"That is {total:,} characters in all. The limit is {MAX_CHARS:,}.")
    return out


def _banner(text: str) -> str:
    text = html.escape(text.strip())
    first, dot, rest = text.partition(". ")
    return f"<b>{first}.</b> {rest}" if dot else text


def _label(inputs: dict) -> str:
    return inputs["output_label"].strip() or "The output"


def _toolbar(rid: str) -> str:
    return (
        '<nav class="toolbar"><a href="/">New check</a><a href="/#past">Past receipts</a>'
        f'<a href="/r/{rid}/receipt.json">Download the record (JSON)</a>'
        '<button type="button" onclick="print()">Print or save as PDF</button>'
        f'<span class="end-bar">{rid}</span></nav>'
    )


def page(receipt: dict, inputs: dict, toolbar: str = "") -> str:
    return render(
        receipt,
        title=inputs["title"].strip() or "Receipt for an AI output",
        subtitle=inputs["context"].strip(),
        banner=_banner(inputs["banner"]) if inputs["banner"].strip() else "",
        output_text=inputs["output"],
        output_label=_label(inputs),
        toolbar=toolbar,
    )


def create_app(client, runs_dir: pathlib.Path | str = "runs/web", model: str = MODEL) -> FastAPI:
    runs = pathlib.Path(runs_dir)
    app = FastAPI(title="receipts", docs_url=None, redoc_url=None, openapi_url=None)

    def folder(rid: str) -> pathlib.Path:
        d = runs / rid
        if not RECEIPT_ID.fullmatch(rid) or not (d / "receipt.json").exists():
            raise HTTPException(404, "No receipt with that number.")
        return d

    def load(d: pathlib.Path) -> tuple[dict, dict]:
        return json.loads((d / "receipt.json").read_text()), json.loads((d / "inputs.json").read_text())

    @app.get("/", response_class=HTMLResponse)
    def form() -> str:
        return (HERE / "form.html").read_text()

    @app.get("/api/example")
    def example() -> dict:
        if not EXAMPLE.exists():
            raise HTTPException(404, "The example files are not on this computer.")
        return {
            "output": (EXAMPLE / "report.txt").read_text(),
            "sources": [{"name": "Fact-find", "text": (EXAMPLE / "factfind.txt").read_text()}],
            "title": "Advice file check",
            "context": "Draft suitability report for David and Margaret Ellery, equity release (lifetime mortgage), "
            "checked against the client fact-find.",
            "output_label": "The draft report",
            "banner": "Made-up file. The clients are fictional and the errors were planted on purpose to show what the check does.",
        }

    @app.get("/api/receipts")
    def past() -> dict:
        rows = []
        dirs = [d for d in runs.glob("R-*") if RECEIPT_ID.fullmatch(d.name) and (d / "inputs.json").exists()] if runs.exists() else []
        for d in sorted(dirs, key=lambda d: d.stat().st_mtime, reverse=True):
            receipt, inputs = load(d)
            rows.append(
                {
                    "id": d.name,
                    "title": inputs["title"].strip() or "Receipt for an AI output",
                    "verdict": headline(receipt, _label(inputs), default_source_phrase(receipt)),
                    "checked": receipt["run"]["created_at"],
                }
            )
        return {"receipts": rows, "engine": ENGINE_VERSION, "prompt": PROMPT_VERSION, "model": model}

    @app.post("/api/check")
    def make(req: CheckRequest):
        found = problems(req)
        if found:
            return JSONResponse({"problems": found}, status_code=422)
        sources = {s.name.strip(): s.text for s in req.sources}
        try:
            result = check(req.output, sources, context=req.context.strip(), client=client, model=model)
        except anthropic.APIStatusError as e:
            raise HTTPException(502, f"The model call failed (status {e.status_code}). Nothing was saved.")
        except anthropic.APIConnectionError:
            raise HTTPException(502, "Could not reach the model. Check the internet connection. Nothing was saved.")
        except RuntimeError:
            raise HTTPException(502, "The model's answer was cut off, so nothing was checked. Try a shorter output or fewer sources.")
        rid = receipt_number(result.receipt)
        d = runs / rid
        d.mkdir(parents=True)
        inputs = req.model_dump()
        inputs["sources"] = [{"name": n, "text": t} for n, t in sources.items()]
        inputs["saved_at"] = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
        (d / "inputs.json").write_text(json.dumps(inputs, indent=2, ensure_ascii=False))
        (d / "receipt.json").write_text(json.dumps(result.receipt, indent=2, ensure_ascii=False))
        (d / "raw_response.txt").write_text(result.raw_response)
        (d / "receipt.html").write_text(page(result.receipt, inputs))
        return {"id": rid, "url": f"/r/{rid}"}

    @app.get("/r/{rid}", response_class=HTMLResponse)
    def view(rid: str) -> str:
        receipt, inputs = load(folder(rid))
        return page(receipt, inputs, toolbar=_toolbar(rid))

    @app.get("/r/{rid}/receipt.json")
    def record(rid: str) -> FileResponse:
        return FileResponse(folder(rid) / "receipt.json", media_type="application/json", filename=f"{rid}.json")

    return app
