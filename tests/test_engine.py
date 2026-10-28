import json
from types import SimpleNamespace

import pytest

from receipts.engine import check, verify_claim
from receipts.render import render
from receipts.verify import sha256

SOURCES = {"factfind": "Clients: David (77). David had a minor stroke in 2023. Mortgage balance £62,000."}
OUTPUT = "You are both in good health. Your mortgage balance is £62,000."


class FakeClient:
    def __init__(self, payload, stop_reason="end_turn"):
        self.payload, self.stop_reason, self.calls = payload, stop_reason, []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text=json.dumps(self.payload))],
            stop_reason=self.stop_reason,
            usage=SimpleNamespace(input_tokens=100, output_tokens=50),
        )


def claim(quote, status, sq=(), cq=()):
    p = lambda xs: [{"source": "factfind", "quote": q} for q in xs]
    return {"output_quote": quote, "status": status, "source_quotes": p(sq), "counter_quotes": p(cq), "uncertainty": "", "why": "w"}


def test_verified_claims_keep_their_status():
    payload = {
        "claims": [
            claim("You are both in good health.", "CONTRADICTED", ["David had a minor stroke in 2023."]),
            claim("Your mortgage balance is £62,000.", "SUPPORTED", ["Mortgage balance £62,000."]),
        ],
        "omissions": [],
    }
    r = check(OUTPUT, SOURCES, client=FakeClient(payload)).receipt
    assert [c["status"] for c in r["claims"]] == ["CONTRADICTED", "SUPPORTED"]
    assert all(c["problems"] == [] for c in r["claims"])


@pytest.mark.parametrize(
    "bad",
    [
        claim("You are in excellent health.", "CONTRADICTED", ["David had a minor stroke in 2023."]),  # not in output
        claim("You are both in good health.", "CONTRADICTED", ["David had a serious stroke."]),  # invented source quote
        claim("Your mortgage balance is £62,000.", "SUPPORTED"),  # supported with no evidence
        claim("Your mortgage balance is £62,000.", "SUPPORTED", ["Mortgage balance £62,000."], ["Invented objection."]),
    ],
)
def test_any_failed_check_sends_claim_to_a_human(bad):
    out = verify_claim(bad, OUTPUT, SOURCES)
    assert out["status"] == "NEEDS_HUMAN_CHECK"
    assert out["model_status"] == bad["status"]
    assert out["problems"]


def test_unknown_source_name_fails_verification():
    c = claim("You are both in good health.", "CONTRADICTED")
    c["source_quotes"] = [{"source": "transcript", "quote": "David had a minor stroke in 2023."}]
    assert verify_claim(c, OUTPUT, SOURCES)["status"] == "NEEDS_HUMAN_CHECK"


def test_omissions_with_invented_quotes_are_rejected_not_dropped():
    payload = {
        "claims": [],
        "omissions": [
            {"source": "factfind", "quote": "David had a minor stroke in 2023.", "why": "health"},
            {"source": "factfind", "quote": "Wants to gift £5,000.", "why": "made up"},
        ],
    }
    r = check(OUTPUT, SOURCES, client=FakeClient(payload)).receipt
    assert [o["status"] for o in r["omissions"]] == ["VERIFIED", "REJECTED"]
    assert r["summary"]["omissions"] == {"VERIFIED": 1, "REJECTED": 1}


def test_receipt_records_input_hashes_and_its_own_fingerprint():
    res = check(OUTPUT, SOURCES, client=FakeClient({"claims": [], "omissions": []}))
    r = res.receipt
    assert r["inputs"]["output"]["sha256"] == sha256(OUTPUT)
    assert r["inputs"]["sources"][0]["sha256"] == sha256(SOURCES["factfind"])
    assert r["run"]["raw_response_sha256"] == sha256(res.raw_response)
    body = {k: v for k, v in r.items() if k != "receipt_sha256"}
    assert r["receipt_sha256"] == sha256(json.dumps(body, sort_keys=True, ensure_ascii=False))


def test_schema_limits_sources_to_those_supplied():
    fake = FakeClient({"claims": [], "omissions": []})
    check(OUTPUT, SOURCES, client=fake)
    schema = fake.calls[0]["output_config"]["format"]["schema"]
    claim_schema = schema["properties"]["claims"]["items"]
    assert claim_schema["properties"]["source_quotes"]["items"]["properties"]["source"]["enum"] == ["factfind"]


def test_truncated_response_is_an_error_not_a_receipt():
    with pytest.raises(RuntimeError):
        check(OUTPUT, SOURCES, client=FakeClient({"claims": [], "omissions": []}, stop_reason="max_tokens"))


def test_render_shows_quotes_verbatim():
    payload = {"claims": [claim("You are both in good health.", "CONTRADICTED", ["David had a minor stroke in 2023."])], "omissions": []}
    page = render(check(OUTPUT, SOURCES, client=FakeClient(payload)).receipt)
    assert "You are both in good health." in page and "David had a minor stroke in 2023." in page
    assert "—" not in page


def test_render_marks_up_the_checked_text_and_refuses_other_text():
    payload = {"claims": [claim("You are both in good health.", "CONTRADICTED", ["David had a minor stroke in 2023."])], "omissions": []}
    receipt = check(OUTPUT, SOURCES, client=FakeClient(payload)).receipt
    page = render(receipt, output_text=OUTPUT, output_label="The draft")
    assert "<mark class='con'>You are both in good health.</mark><sup class='con'>F1</sup>" in page
    assert "The draft contradicts the factfind in 1 place." in page
    with pytest.raises(ValueError):
        render(receipt, output_text=OUTPUT + " edited")


def test_an_omission_already_used_to_contradict_a_claim_is_not_counted_twice():
    payload = {
        "claims": [claim("You are both in good health.", "CONTRADICTED", ["David had a minor stroke in 2023."])],
        "omissions": [
            {"source": "factfind", "quote": "David had a minor stroke in 2023.", "why": "health"},
            {"source": "factfind", "quote": "Mortgage balance £62,000.", "why": "debt"},
        ],
    }
    r = check(OUTPUT, SOURCES, client=FakeClient(payload)).receipt
    assert [o["status"] for o in r["omissions"]] == ["ALREADY_CONTRADICTED", "VERIFIED"]
    assert r["omissions"][0]["contradicts"] == "You are both in good health."
    page = render(r)
    assert "leaves out 1 fact." in page and "not counted again as left out" in page


def test_headline_verb_agrees_with_the_number_of_sources():
    from receipts.render import headline

    payload = {"claims": [claim("You are both in good health.", "UNSUPPORTED")], "omissions": []}
    one = check(OUTPUT, SOURCES, client=FakeClient(payload)).receipt
    two = check(OUTPUT, {**SOURCES, "terms": "x"}, client=FakeClient(payload)).receipt
    assert headline(one, "The output", "the factfind").endswith("the factfind does not support.")
    assert headline(two, "The output", "its sources").endswith("its sources do not support.")
