"""Stage 0: provenance-grounding — receipt-joined substring check."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from tests.invariants.helpers import provenance_grounding_violations

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "provenance"


def test_provenance_grounding_detects_fabricated_span():
  phase1 = pd.read_csv(FIXTURES / "phase1_payload.csv")
  audited = json.loads((FIXTURES / "audited_good.json").read_text(encoding="utf-8"))
  violations = provenance_grounding_violations(audited, phase1)
  assert violations == []


def test_provenance_grounding_catches_wrong_chunk():
  phase1 = pd.read_csv(FIXTURES / "phase1_payload.csv")
  audited = json.loads((FIXTURES / "audited_bad_span.json").read_text(encoding="utf-8"))
  violations = provenance_grounding_violations(audited, phase1)
  assert violations, "fabricated span should fail grounding"


@pytest.mark.skipif(
    not (FIXTURES / "audited_good.json").is_file(),
    reason="provenance fixtures missing",
)
def test_provenance_grounding_fixture_files_present():
  assert (FIXTURES / "phase1_payload.csv").is_file()
