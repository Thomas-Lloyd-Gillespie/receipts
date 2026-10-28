"""The single model request: claims and omissions, as JSON matching a schema.

The structure borrows from ARGUS's adversarial architecture: every supported
claim is tested against counter-evidence and case-specific uncertainty, with
an explicit instruction not to manufacture either.
"""

from __future__ import annotations

PROMPT_VERSION = "claims-1.1"

STATUSES = ("SUPPORTED", "CONTRADICTED", "UNSUPPORTED")

INSTRUCTIONS = """You are checking AI-generated output against the source records it was meant to be based on. A human reviewer will read your findings, and code will check every quote you give word for word, so copy quotes exactly.
{context}
Task 1: claims. List every statement in the output that presents something about this case as fact or uses it as a premise. That covers:
- facts about the people or entities involved, their circumstances, numbers, events, wishes, decisions, or what was said or agreed
- numbers the output derives from the sources (check the arithmetic)
- labels and characterisations applied to the sources' figures or facts (check they describe what the sources actually give)
- causes, explanations and motives the output attributes
- comparisons with anything outside the sources, such as market norms, typical levels or other firms
- statements about what the evidence shows, proves or rules out, and how strongly
Skip textbook definitions and standard mechanisms, recommendations, and possibilities stated with hedges such as "may", "could" or "might". Judge the output's final position: if it states something and later explicitly corrects it, check the corrected version and mention the correction in "why".
For each claim give:
- output_quote: the claim copied exactly from the output, character for character, as one short continuous passage. No ellipses and no joining of separate passages.
- status: SUPPORTED (the sources establish it), CONTRADICTED (the sources say something different, or the output's arithmetic on source figures is wrong), or UNSUPPORTED (the sources do not establish it: it relies on outside information, attributes causes or qualities the sources don't state, mislabels what a figure is, or concludes more strongly than the sources allow).
- source_quotes: the passages the status rests on, each copied exactly, with the name of its source. Leave empty only for an UNSUPPORTED claim when nothing in the sources bears on it.
- counter_quotes: for a SUPPORTED claim, any passage in the sources that cuts against or qualifies it. Usually empty. Do not invent objections.
- uncertainty: if the sources leave something genuinely open that affects this claim, say what in one sentence. Otherwise an empty string. No generic caveats.
- why: one plain-English sentence for the reviewer.

Task 2: omissions. List facts in the sources that matter to what the output is doing but that the output leaves out or fails to reflect. For each give the source name, the passage copied exactly, and one sentence on why a reviewer would care. Material omissions only.

{sources}

<output>
{output}
</output>"""


def build_prompt(output: str, sources: dict[str, str], context: str = "") -> str:
    blocks = "\n\n".join(f'<source name="{name}">\n{text}\n</source>' for name, text in sources.items())
    ctx = f"\nContext: {context}\n" if context else ""
    return INSTRUCTIONS.format(context=ctx, sources=blocks, output=output)


def build_schema(source_names: list[str]) -> dict:
    """JSON schema for the response. Source names are an enum, so the model
    cannot cite a source that was not supplied."""
    passage = {
        "type": "object",
        "properties": {
            "source": {"type": "string", "enum": source_names},
            "quote": {"type": "string"},
        },
        "required": ["source", "quote"],
        "additionalProperties": False,
    }
    claim = {
        "type": "object",
        "properties": {
            "output_quote": {"type": "string"},
            "status": {"type": "string", "enum": list(STATUSES)},
            "source_quotes": {"type": "array", "items": passage},
            "counter_quotes": {"type": "array", "items": passage},
            "uncertainty": {"type": "string"},
            "why": {"type": "string"},
        },
        "required": ["output_quote", "status", "source_quotes", "counter_quotes", "uncertainty", "why"],
        "additionalProperties": False,
    }
    omission = {
        "type": "object",
        "properties": {
            "source": {"type": "string", "enum": source_names},
            "quote": {"type": "string"},
            "why": {"type": "string"},
        },
        "required": ["source", "quote", "why"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "claims": {"type": "array", "items": claim},
            "omissions": {"type": "array", "items": omission},
        },
        "required": ["claims", "omissions"],
        "additionalProperties": False,
    }
