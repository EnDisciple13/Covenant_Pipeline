"""Hypothesis property: chunker-partition — monotone non-overlap and page bounds."""

from __future__ import annotations

import fitz
import pandas as pd
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from tests.invariants.helpers import partition_monotone_nonoverlap_violations


def _max_pages_for_df(df: pd.DataFrame) -> int:
    if df.empty:
        return 1
    return int(df["Absolute_End_Page"].max())


@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=40),
            st.integers(min_value=0, max_value=200),
            st.text(min_size=1, max_size=80),
        ),
        min_size=1,
        max_size=15,
    )
)
@settings(max_examples=30, deadline=None)
@example([(1, 50, "covenant alpha text")])
@example([(1, 100, "unicode bullet \u2022 text"), (2, 80, "page boundary span")])
def test_partition_monotone_nonoverlap(spans: list[tuple[int, int, str]]):
    """Synthetic chunk sets within declared domain satisfy partition laws."""
    rows = []
    page = 1
    for idx, (_start_hint, text_len, label) in enumerate(spans):
        end_page = page + max(0, text_len // 100)
        rows.append(
            {
                "Section": f"Section 1.{idx + 1:02d}",
                "Section_Title": label[:40],
                "Article": "Article 1",
                "Article_Title": "TEST ARTICLE",
                "Printed_Start_Page": page,
                "Absolute_Start_Page": page,
                "Absolute_End_Page": max(page, end_page),
                "Raw_Text": (label + " ") * max(1, text_len // max(len(label), 1)),
            }
        )
        page = max(page, end_page)

    df = pd.DataFrame(rows)
    max_page = _max_pages_for_df(df) + 5
    violations = partition_monotone_nonoverlap_violations(df, max_page=max_page)
    assert violations == [], f"partition violations: {violations}"


@pytest.mark.usefixtures("synthetic_pdf")
def test_partition_monotone_nonoverlap_golden(synthetic_pdf):
    """Golden fixture phase1 payload satisfies partition oracle."""
    df = pd.read_csv(synthetic_pdf.phase1_payload)
    doc = fitz.open(synthetic_pdf.pdf_path)
    max_page = len(doc)
    doc.close()
    violations = partition_monotone_nonoverlap_violations(df, max_page=max_page)
    assert violations == [], f"golden partition violations: {violations}"


def test_partition_monotone_nonoverlap_m2_mutant_class():
    """M2 class: swapped chunk row order must fail partition oracle."""
    df = pd.DataFrame(
        [
            {
                "Section": "Section 1.01",
                "Printed_Start_Page": 1,
                "Absolute_Start_Page": 10,
                "Absolute_End_Page": 12,
                "Raw_Text": "first chunk text " * 20,
            },
            {
                "Section": "Section 1.02",
                "Printed_Start_Page": 2,
                "Absolute_Start_Page": 20,
                "Absolute_End_Page": 22,
                "Raw_Text": "second chunk text " * 20,
            },
        ]
    )
    swapped = df.iloc[[1, 0]].reset_index(drop=True)
    violations = partition_monotone_nonoverlap_violations(swapped, max_page=50)
    assert violations, "reordered chunks must violate monotonicity"
