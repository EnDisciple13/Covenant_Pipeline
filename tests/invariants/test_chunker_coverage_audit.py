"""Stage 0: chunker-coverage-audit — non-empty extraction per skeleton row."""

from __future__ import annotations

import pandas as pd

from tests.invariants.helpers import empty_raw_text_rows


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
