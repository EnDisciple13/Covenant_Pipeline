"""Stage 0: chunker-coverage-audit — non-empty extraction + body-scan reconciliation."""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from tests.invariants.helpers import (
    coverage_audit_reconciliation_violations,
    empty_raw_text_rows,
)


def test_chunker_coverage_audit_detects_empty_row():
    df = pd.DataFrame(
        [
            {"Section": "Section 7.1", "Raw_Text": "covenant text"},
            {"Section": "Section 7.2", "Raw_Text": ""},
        ]
    )
    violations = empty_raw_text_rows(df)
    assert len(violations) == 1
    assert violations[0][0] == "Section 7.2"


def test_chunker_coverage_audit_non_empty_extraction(synthetic_pdf):
    df = pd.read_csv(synthetic_pdf.phase1_payload)
    violations = empty_raw_text_rows(df)
    assert violations == [], f"empty Raw_Text rows: {violations}"


@given(
    st.lists(
        st.tuples(
            st.from_regex(r"Section \d+\.\d+", fullmatch=True),
            st.text(min_size=5, max_size=200),
        ),
        min_size=1,
        max_size=8,
    )
)
@settings(max_examples=20, deadline=None)
@example([("Section 1.01", "Article body text with Section 1.01 header inline")])
def test_chunker_coverage_audit_body_scan_reconciliation(rows: list[tuple[str, str]]):
    """Skeleton rows non-empty; body/skeleton mismatches recorded as warnings (soft-fail)."""
    df = pd.DataFrame(
        [{"Section": sec, "Raw_Text": text} for sec, text in rows]
    )
    empty_v = empty_raw_text_rows(df)
    assert empty_v == []
    warnings = [f"body header mismatch: extra Section 99.99"]
    recon_v = coverage_audit_reconciliation_violations(df, warnings=warnings)
    assert recon_v == []


@pytest.mark.usefixtures("synthetic_pdf")
def test_chunker_coverage_audit_golden_reconciliation(synthetic_pdf):
    """Golden fixture: non-empty extraction + zero reconciliation violations."""
    df = pd.read_csv(synthetic_pdf.phase1_payload)
    assert empty_raw_text_rows(df) == []
    assert coverage_audit_reconciliation_violations(df, warnings=[]) == []
