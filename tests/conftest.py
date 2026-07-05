"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
SYNTHETIC_PDF = FIXTURES_DIR / "synthetic_covenant.pdf"
HALLADOR_PDF = FIXTURES_DIR / "Credit_Agreement_Hallador.pdf"


def _docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=30,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.fixture
def synthetic_pdf(tmp_path):
    """Copy synthetic PDF and run skip-llm pipeline into tmp_path."""
    from covenant_pipeline.config import PipelinePaths
    from covenant_pipeline.orchestrator import run_full_pipeline

    if not SYNTHETIC_PDF.is_file():
        pytest.skip("synthetic_covenant.pdf missing — run tests/fixtures/build_synthetic_pdf.py")

    pdf_copy = tmp_path / "input.pdf"
    shutil.copy(SYNTHETIC_PDF, pdf_copy)
    paths = PipelinePaths(output_dir=tmp_path / "out", pdf_path=pdf_copy)
    run_full_pipeline(paths, skip_llm=True)
    return paths


@pytest.fixture
def docker_available():
    if not _docker_available():
        pytest.skip("Docker not available for container-parity test")
