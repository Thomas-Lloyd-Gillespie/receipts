# receipts

A receipt for every AI output in financial services. TLG Systems Ltd. Working name.

Give it a piece of AI output (a suitability report, an assessment, a chatbot answer) and the source records it should rest on. It returns a receipt:

- every claim the output makes about the case, marked SUPPORTED, CONTRADICTED or UNSUPPORTED, with the source passages it rests on
- for supported claims, any passage that cuts against them and any genuine open question (the ARGUS structure: test against counter-evidence, never manufacture it)
- facts in the sources that the output left out
- hashes of every input, the model, prompt and engine versions, the request id, and a fingerprint of the receipt itself

## The rule

The model proposes. Code verifies. Every quote must appear word for word in the text it claims to come from. A claim with any failed check becomes NEEDS_HUMAN_CHECK, and an omission with a failed quote becomes REJECTED. Nothing is dropped silently: the receipt keeps what the model said, what survived, and why.

## Run it

```bash
uv sync
uv run pytest -q
uv run python -m receipts check \
  --output examples/ellery/report.txt \
  --source factfind=examples/ellery/factfind.txt \
  --context "AI-assisted draft suitability report for equity release, checked against the fact-find" \
  --env-file PATH/TO/.env
```

The key comes from `ANTHROPIC_API_KEY` in the environment or the `.env` file. It is never printed. Output goes to `runs/` (gitignored): `receipt.json`, `receipt.html`, `raw_response.txt`.

## The paste page

```bash
uv run python -m receipts serve --env-file PATH/TO/.env
```

Open http://127.0.0.1:8765. Paste an AI output and one or more named sources (or press "Fill in the Ellery example"), and the page returns the receipt, with links to print it or download the JSON record. Past receipts are listed on the front page.

It listens on this computer only. Each receipt is saved in `runs/web/<receipt number>/` with its inputs, the model's raw response and the printable page, so it can be shown again and its fingerprints rechecked. Use made-up or anonymised documents only: what you paste is sent to Anthropic's API.

## Benchmark against the ARGUS blind coding

`bench/argus.py` runs the engine over the 144 outputs from the MSc benchmark and compares its flags with the frozen blind human coding of unsupported assertions (M5, coded 10 Aug 2026). The engine sees only what the ARGUS model saw plus the output. It never sees the coding.

Same discipline as the dissertation: items used for development are recorded in `bench/argus_dev_set.json`, and only the held-out run (everything else) is reportable.

```bash
uv run python bench/argus.py --split devset --env-file PATH   # rerun the 16 development items
uv run python bench/argus.py --split heldout --env-file PATH  # the reportable run, 128 items
```

## Status (28 Oct 2026)

- Engine 0.1.0, prompt claims-1.1. 32 tests pass.
- Made-up Ellery file: all 8 planted contradictions and the planted omission found, no quote failures.
- ARGUS development set (16 items, not reportable): prompt 1.0 flagged 3 of the 8 outputs the coder marked and 1 of the 8 they did not. Prompt 1.1, which adds causes, labels, outside comparisons and overstatement to what counts as a claim, flagged 6 of 8 and 3 of 8. The extra flags are arguable, and one (S20) is a wrong headline verdict the output never withdraws.
- Held-out run: not done yet.
- Paste page: the Ellery example through the page took 28 seconds. Same 8 contradictions and the planted gift found, 6 facts left out (7 on the earlier run), no quote failures.

## What it does not do

It does not judge whether the output is right or suitable. It shows where the output and its sources disagree, what the sources do not establish and what was left out, so a reviewer can go straight to those points.
