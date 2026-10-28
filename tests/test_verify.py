from receipts.verify import found, norm


def test_norm_evens_out_whitespace_and_typography():
    assert norm("  it’s “fine” — ok\n\tthen ") == "it's \"fine\" - ok then"


def test_found_requires_exact_words():
    text = "David has Type 2 diabetes and had a minor stroke in 2023."
    assert found("had a minor stroke in 2023", text)
    assert found("had a  minor\nstroke", text)
    assert not found("had a stroke in 2023", text)
    assert not found("Had a minor stroke", text)


def test_found_rejects_empty_quotes():
    assert not found("", "anything")
    assert not found("   ", "anything")
