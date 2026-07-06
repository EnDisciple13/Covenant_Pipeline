"""Hypothesis property: staging-parity — staged CLI equals composed orchestrator."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from covenant_pipeline.config import PipelinePaths
from covenant_pipeline.orchestrator import run_full_pipeline
from tests.conftest import REPO_ROOT, SYNTHETIC_PDF
from tests.invariants.helpers import deterministic_prefix_fingerprint


def _run_staged_cli(out_dir: Path, pdf: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stages = [
        [
            sys.executable,
            "-m",
            "covenant_pipeline.cli",
            "chunk",
            "--output-dir",
            str(out_dir),
            "--pdf",
            str(pdf),
        ],
        [
            sys.executable,
            "-m",
            "covenant_pipeline.cli",
            "route",
            "--output-dir",
            str(out_dir),
        ],
        [
            sys.executable,
            "-m",
            "covenant_pipeline.cli",
            "glossary",
            "--output-dir",
            str(out_dir),
        ],
    ]
    for cmd in stages:
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    paths = PipelinePaths(output_dir=out_dir, pdf_path=pdf)
    return deterministic_prefix_fingerprint(paths)


@pytest.mark.skipif(not SYNTHETIC_PDF.is_file(), reason="synthetic PDF missing")
def test_staging_parity_deterministic_prefix(tmp_path):
    """Staged chunk/route/glossary CLI yields same P_det artifacts as run --skip-llm."""
    pdf = tmp_path / "input.pdf"
    shutil.copy(SYNTHETIC_PDF, pdf)

    staged_dir = tmp_path / "staged"
    composed_dir = tmp_path / "composed"
    fp_staged = _run_staged_cli(staged_dir, pdf)

    paths = PipelinePaths(output_dir=composed_dir, pdf_path=pdf)
    run_full_pipeline(paths, skip_llm=True)
    fp_composed = deterministic_prefix_fingerprint(paths)

    assert fp_staged == fp_composed
