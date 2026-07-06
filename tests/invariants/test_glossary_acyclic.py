"""Hypothesis property: glossary-acyclic — DAG + dangling reference detection."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from covenant_pipeline.phases.audit import run_database_audit
from tests.invariants.helpers import (
    audit_payload_clean,
    glossary_cycle_detection,
    glossary_dangling_refs,
)


def _glossary_entry(refs: list[str], text: str = "definition text") -> dict:
    return {"raw_definition_text": text, "nested_references": refs}


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=8, alphabet="ABCDEFGH"),
            st.lists(st.sampled_from(["A", "B", "C", "D"]), max_size=3),
        ),
        min_size=0,
        max_size=8,
        unique_by=lambda x: x[0],
    ).filter(
        lambda terms: all(ref in {t for t, _ in terms} for _, refs in terms for ref in refs)
        and all(ref != term for term, refs in terms for ref in refs)
    )
)
@settings(max_examples=30, deadline=None)
def test_definition_graph_dag(terms: list[tuple[str, list[str]]]):
    """Acyclic glossary graphs produce no cycle warnings under audit oracle."""
    glossary = {term: _glossary_entry(refs) for term, refs in terms}
    cycles = glossary_cycle_detection(glossary)
    assert cycles == [], f"unexpected cycles in DAG input: {cycles}"

    payload = {
        "Document_Metadata": {"Audit_Status": "Pending", "Warnings": {}},
        "Phase1_Extracted_Covenants": [],
        "Phase2_Master_Glossary": glossary,
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "payload.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        run_database_audit(path)
        audited = json.loads(path.read_text(encoding="utf-8"))
    assert audit_payload_clean(audited)


def test_definition_graph_dag_detects_cycle():
    """Cyclic glossary fails audit clean status (M5 kill target)."""
    glossary = {"A": _glossary_entry(["B"]), "B": _glossary_entry(["A"])}
    cycles = glossary_cycle_detection(glossary)
    assert cycles, "cycle detector must flag A <-> B"

    payload = {
        "Document_Metadata": {"Audit_Status": "Pending", "Warnings": {}},
        "Phase1_Extracted_Covenants": [],
        "Phase2_Master_Glossary": glossary,
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "payload.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        run_database_audit(path)
        audited = json.loads(path.read_text(encoding="utf-8"))
    assert not audit_payload_clean(audited)
    assert audited["Document_Metadata"]["Warnings"]["Circular_References"]


def test_definition_graph_dangling_soft_fail():
    """Dangling refs detected without exception (soft-fail)."""
    glossary = {"Known": _glossary_entry([])}
    covenants = [{"Extracted_Data": {"field": "[$REF: UnknownTerm]"}}]
    dangling = glossary_dangling_refs(covenants, glossary)
    assert "UnknownTerm" in dangling


def test_definition_graph_golden_pipeline_glossary(synthetic_pdf):
    """Golden skip-llm glossary must be acyclic (M5 integration kill target)."""
    import json

    glossary = json.loads(synthetic_pdf.glossary.read_text(encoding="utf-8"))
    cycles = glossary_cycle_detection(glossary)
    assert cycles == [], f"golden glossary cycles: {cycles}"
