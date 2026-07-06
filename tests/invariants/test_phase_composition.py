"""Hypothesis property: phase-composition — associativity of deterministic phases."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from covenant_pipeline.config import PipelinePaths
from covenant_pipeline.orchestrator import run_full_pipeline, run_stage
from tests.conftest import SYNTHETIC_PDF
from tests.invariants.helpers import deterministic_prefix_fingerprint, file_sha256


def _compose_sequential(tmp_path: Path, pdf: Path) -> dict[str, str]:
    out = tmp_path / "seq"
    paths = PipelinePaths(output_dir=out, pdf_path=pdf)
    run_stage("chunk", paths)
    run_stage("route", paths)
    run_stage("glossary", paths)
    return deterministic_prefix_fingerprint(paths)


def _compose_grouped(tmp_path: Path, pdf: Path) -> dict[str, str]:
    out = tmp_path / "grp"
    paths = PipelinePaths(output_dir=out, pdf_path=pdf)
    run_full_pipeline(paths, skip_llm=True)
    return deterministic_prefix_fingerprint(paths)


@pytest.mark.skipif(not SYNTHETIC_PDF.is_file(), reason="synthetic PDF missing")
def test_phase_composition_associativity(tmp_path):
    """Grouped skip-llm run equals sequential chunk -> route -> glossary."""
    pdf = tmp_path / "input.pdf"
    shutil.copy(SYNTHETIC_PDF, pdf)
    fp_seq = _compose_sequential(tmp_path / "a", pdf)
    fp_grp = _compose_grouped(tmp_path / "b", pdf)
    assert fp_seq == fp_grp
    for key, digest in fp_seq.items():
        assert digest, f"missing artifact hash for {key}"
