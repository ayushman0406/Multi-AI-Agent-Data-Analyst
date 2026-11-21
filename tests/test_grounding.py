from analyst.grounding import check, numbers_in, ungrounded_numbers


def test_numbers_in():
    assert numbers_in("Revenue was 1,234.5 and 37% [2] on 2026-01-02") == [1234.5, 37.0]
    assert numbers_in("about 12.9k units") == [12900.0]


def test_flags_unknown_and_accepts_known():
    src = {"summary": {"top_value": 12, "share": 0.5}}
    text = "South leads with 12 units [1], about 37% more than the rest."
    assert ungrounded_numbers(text, src) == [37.0]
    res = check(text, src)
    assert res["grounded_count"] == 1 and res["total_numbers"] == 2


def test_percent_fraction_equivalence():
    assert ungrounded_numbers("Discount averages 15.25% in the West", {"mean": 0.1525}) == []
    assert ungrounded_numbers("Share is 0.67", {"top_share_pct": 66.67}) == []


def test_rounding_to_two_significant_figures():
    assert ungrounded_numbers("Total is 12,873", {"total": 12873.46}) == []
    assert ungrounded_numbers("Total is 13k", {"total": 12873.46}) == []
    assert ungrounded_numbers("Total is 15k", {"total": 12873.46}) == [15000.0]


def test_ignores_small_ints_years_and_question_numbers():
    assert ungrounded_numbers("Top 5 regions in 2025, step 3", {}) == []
    assert ungrounded_numbers("Orders above 250 are rare", {}, question="orders above 250?") == []
    assert ungrounded_numbers("Orders above 250 are rare", {}) == [250.0]
