# receipts

Checks AI-written financial documents, claim by claim, against the records they should rest on.

Give it a piece of AI output, such as a draft suitability report, and its source records, such as the client fact-find. It returns a receipt: every claim the output makes about the case, marked as supported, contradicted or unsupported by the sources, with the source passages quoted, plus the facts the output left out. A language model proposes the findings. Code then checks that every quoted passage appears word for word in the text it claims to come from, so no finding can rest on an invented quote.

**Status:** version 0.1 (engine 0.1.1, prompt claims-1.1), built October 2026 by Thomas Lloyd-Gillespie under TLG Systems Ltd. Research code, not a product.

## Why it exists

Advice firms are starting to use AI to draft suitability reports and file notes. Someone still has to check each statement against the fact-find before the file goes out, and that check is done by hand. receipts does the first pass and shows its working, so the reviewer can go straight to the places where the output and its sources disagree. It grew out of my MSc dissertation, [ARGUS](https://github.com/Thomas-Lloyd-Gillespie/argus-financial-ai-assurance), which tested whether AI explanations of financial questions can be audited.

## What has been tested so far

- **Made-up Ellery file.** A draft equity release suitability report with 8 statements that contradict the fact-find and one client objective left out, written on purpose to test the check. The engine marked all 8 as contradicted, listed the left-out objective (a £5,000 gift to a granddaughter) among the facts the report omits, and had no quote failures. The errors are listed in [`examples/ellery/ANSWER_KEY.md`](examples/ellery/ANSWER_KEY.md) and one full run is in [`examples/ellery/sample-receipt/`](examples/ellery/sample-receipt/). Limit: the file and its errors were written with an AI model (Claude) for this test, so this shows the mechanism works. It does not show how accurate the check is on real advice files.
- **ARGUS development set.** 16 of the 144 model outputs from my dissertation benchmark, compared with my human coding of unsupported assertions. With prompt claims-1.0 the engine flagged 3 of the 8 outputs I had marked and 1 of the 8 I had not. With prompt claims-1.1 it flagged 6 of 8 and 3 of 8. Some of the extra flags are arguable, and one is a wrong headline verdict the output never withdraws. These items were used to develop the prompt, so these are not accuracy figures. Tables in [`bench/dev-runs/`](bench/dev-runs/).
- **ARGUS held-out run (the other 128 outputs).** Not run yet. This is the only run that would give a reportable number.
- **Tests.** 34 unit tests, no API calls: `uv run pytest -q`.

## What a receipt contains

- every claim the output makes about the case, marked SUPPORTED, CONTRADICTED or UNSUPPORTED, with the source passages it rests on
- for supported claims, any passage that cuts against them and any genuine open question (the ARGUS structure: test against counter-evidence, never manufacture it)
- facts in the sources that the output left out
- hashes of every input, the model, prompt and engine versions, the request id, and a fingerprint of the receipt itself

## The rule

The model proposes. Code verifies. Every quote must appear word for word in the text it claims to come from. A claim with any failed check becomes NEEDS_HUMAN_CHECK, and an omission with a failed quote becomes REJECTED. Nothing is dropped silently: the receipt keeps what the model said, what survived, and why.

## Run it

You need Python 3.12 or later, [uv](https://docs.astral.sh/uv/) and an Anthropic API key.

```bash
uv sync
uv run pytest -q
cp .env.example .env    # then put your key after ANTHROPIC_API_KEY=
uv run python -m receipts check \
  --output examples/ellery/report.txt \
  --source factfind=examples/ellery/factfind.txt \
  --context "AI-assisted draft suitability report for equity release, checked against the fact-find"
```

The key comes from `ANTHROPIC_API_KEY` in the environment, or from `.env` in the repository root (pass `--env-file PATH` to use another file). It is never printed. Output goes to `runs/` (gitignored): `receipt.json`, `receipt.html`, `raw_response.txt`.

## The paste page

```bash
uv run python -m receipts serve
```

Open http://127.0.0.1:8765. Paste an AI output and one or more named sources (or press "Fill in the Ellery example"), and the page returns the receipt, with links to print it or download the JSON record. Past receipts are listed on the front page.

It listens on this computer only. Each receipt is saved in `runs/web/<receipt number>/` with its inputs, the model's raw response and the printable page, so it can be shown again and its fingerprints rechecked. Use made-up or anonymised documents only: what you paste is sent to Anthropic's API.

## Benchmark against the ARGUS human coding

`bench/argus.py` runs the engine over the 144 outputs from the MSc benchmark and compares its flags with the frozen human coding of unsupported assertions (M5, coded 10 Aug 2026; the dissertation describes its blinding as partial, because the two explanation formats look different). The engine sees only what the ARGUS model saw plus the output. It never sees the coding.

Same discipline as the dissertation: items used for development are recorded in `bench/argus_dev_set.json`, and only the held-out run (everything else) is reportable.

The coding files live in the ARGUS repository. Clone it next to this one, or point `--argus-dir` (or `ARGUS_ANALYSIS_DIR`) at its `analysis` folder:

```bash
git clone https://github.com/Thomas-Lloyd-Gillespie/argus-financial-ai-assurance ../argus-financial-ai-assurance
uv run python bench/argus.py --split devset    # rerun the 16 development items
uv run python bench/argus.py --split heldout   # the reportable run, 128 items
```

## What it does not do

It does not judge whether the output is right or suitable. It shows where the output and its sources disagree, what the sources do not establish and what was left out, so a reviewer can go straight to those points.

## Licence

MIT. See [LICENSE](LICENSE).
