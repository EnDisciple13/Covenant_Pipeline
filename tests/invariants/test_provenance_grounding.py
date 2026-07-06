"""Stage 0 + Hypothesis: provenance-grounding — receipt-joined substring check."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

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


@given(st.text(min_size=4, max_size=40, alphabet="abcdefghijklmnopqrstuvwxyz "))
@settings(max_examples=15, deadline=None)
@example("exact quote substring")
def test_provenance_grounding_detects_fabricated_span_property(quote: str):
    """Mutated quotes not in source chunk fail grounding oracle."""
    if not (FIXTURES / "phase1_payload.csv").is_file():
        pytest.skip("provenance fixtures missing")
    phase1 = pd.read_csv(FIXTURES / "phase1_payload.csv")
    receipt = phase1.iloc[0]["Section"] if len(phase1) else "Section 1.01"
    chunk_text = str(phase1.iloc[0].get("Raw_Text", "baseline covenant text"))
    fabricated = quote + "ZZZ_NOT_IN_SOURCE"
    if fabricated.strip().lower() in chunk_text.lower():
        return
    audited = {
        "Phase1_Extracted_Covenants": [
            {
                "Receipt": receipt,
                "Extracted_Data": {"note": fabricated},
            }
        ]
    }
    violations = provenance_grounding_violations(audited, phase1)
    assert violations


@pytest.mark.skipif(
    not (FIXTURES / "audited_good.json").is_file(),
    reason="provenance fixtures missing",
)
def test_provenance_grounding_fixture_files_present():
    assert (FIXTURES / "phase1_payload.csv").is_file()
