import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "bench"))

from argus import human_quotes, overlaps  # noqa: E402


def test_human_quotes_reads_straight_and_curly_quotes():
    note = 'One claim: "The implied payback period exceeds 15 years"; another “demand has not caught up”.'
    assert human_quotes(note) == ["The implied payback period exceeds 15 years", "demand has not caught up"]


def test_human_quotes_ignores_paraphrased_notes():
    assert human_quotes("No material unsupported assertions identified.") == []


def test_overlaps_accepts_containment_and_close_wording():
    assert overlaps("payback period on current-year capex alone exceeds 15 years",
                    "The implied payback period on current-year capex alone exceeds 15 years on a cash-flow basis.")
    assert overlaps("real revenue declined by approximately 0.85%", "Real revenue declined by approximately 0.85%.")
    assert not overlaps("capacity utilisation is partial", "the token price was flat over the year")
