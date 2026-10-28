import json

import pytest
from fastapi.testclient import TestClient

from receipts.web import create_app
from tests.test_engine import OUTPUT, FakeClient, claim

PAYLOAD = {
    "claims": [
        claim("You are both in good health.", "CONTRADICTED", ["David had a minor stroke in 2023."]),
        claim("Your mortgage balance is £62,000.", "SUPPORTED", ["Mortgage balance £62,000."]),
    ],
    "omissions": [],
}
REQUEST = {
    "output": OUTPUT,
    "sources": [{"name": "factfind", "text": "Clients: David (77). David had a minor stroke in 2023. Mortgage balance £62,000."}],
    "title": "Advice file check",
    "output_label": "The draft report",
    "banner": "Made-up file. Fictional clients.",
}


@pytest.fixture
def web(tmp_path):
    fake = FakeClient(PAYLOAD)
    return TestClient(create_app(fake, tmp_path)), fake, tmp_path


def test_form_page_loads(web):
    client, _, _ = web
    r = client.get("/")
    assert r.status_code == 200 and "Check an AI output against its records" in r.text


def test_check_saves_a_receipt_that_can_be_shown_again(web):
    client, fake, runs = web
    r = client.post("/api/check", json=REQUEST)
    assert r.status_code == 200
    rid = r.json()["id"]
    saved = runs / rid
    assert {p.name for p in saved.iterdir()} == {"inputs.json", "receipt.json", "raw_response.txt", "receipt.html"}
    assert json.loads((saved / "inputs.json").read_text())["output"] == OUTPUT
    assert "toolbar" not in (saved / "receipt.html").read_text().split("</style>")[1]

    page = client.get(f"/r/{rid}").text
    assert "The draft report contradicts the factfind in 1 place." in page
    assert '<nav class="toolbar">' in page
    assert "<b>Made-up file.</b> Fictional clients." in page
    assert client.get(f"/r/{rid}/receipt.json").json()["receipt_sha256"]

    listed = client.get("/api/receipts").json()["receipts"]
    assert [x["id"] for x in listed] == [rid]
    assert len(fake.calls) == 1


@pytest.mark.parametrize(
    "change, expected",
    [
        ({"output": "  "}, "Paste the AI output you want checked."),
        ({"sources": []}, "Add at least one source."),
        ({"sources": [{"name": "", "text": "x"}]}, "Give source 1 a name."),
        ({"sources": [{"name": "A", "text": "x"}, {"name": " A ", "text": "y"}]}, "Used more than once: A."),
        ({"output": "x" * 200_001}, "The limit is 200,000."),
    ],
)
def test_bad_requests_are_explained_and_never_reach_the_model(web, change, expected):
    client, fake, runs = web
    r = client.post("/api/check", json={**REQUEST, **change})
    assert r.status_code == 422
    assert any(expected in p for p in r.json()["problems"])
    assert fake.calls == [] and not list(runs.iterdir())


@pytest.mark.parametrize("rid", ["R-0000-0000", "%2E%2E", "..%2Finputs", "R-ABCD-EFGH", "r-abcd-0123", "R-0000-00000"])
def test_unknown_or_malformed_receipt_numbers_are_not_found(web, rid):
    client, _, _ = web
    assert client.get(f"/r/{rid}").status_code == 404
    assert client.get(f"/r/{rid}/receipt.json").status_code == 404


def test_example_is_the_ellery_file(web):
    client, _, _ = web
    ex = client.get("/api/example").json()
    assert ex["sources"][0]["name"] == "Fact-find" and "Ellery" in ex["output"]
