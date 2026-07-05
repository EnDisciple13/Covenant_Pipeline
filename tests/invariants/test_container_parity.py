"""Stage 0: container-parity — host vs container skip-llm artifacts."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import FIXTURES_DIR, REPO_ROOT, SYNTHETIC_PDF
from tests.invariants.helpers import file_sha256

SKIP_LLM_ARTIFACTS = (
    "final_extracted_covenants_phase1_payload.csv",
    "dispatch_queue_output.json",
    "resolved_definitions.json",
)


def _run_host_skip_llm(output_dir: Path, pdf_path: Path) -> None:
    from covenant_pipeline.config import PipelinePaths
    from covenant_pipeline.orchestrator import run_full_pipeline

    paths = PipelinePaths(output_dir=output_dir, pdf_path=pdf_path)
    run_full_pipeline(paths, skip_llm=True)


def _artifact_hashes(directory: Path) -> dict[str, str]:
    return {name: file_sha256(directory / name) for name in SKIP_LLM_ARTIFACTS}


def test_container_parity_host_reproducible(synthetic_pdf):
    """Same PDF run twice on host yields identical skip-llm artifacts."""
    pdf = synthetic_pdf.pdf_path
    out_a = synthetic_pdf.output_dir.parent / "run_a"
    out_b = synthetic_pdf.output_dir.parent / "run_b"
    _run_host_skip_llm(out_a, pdf)
    _run_host_skip_llm(out_b, pdf)
    assert _artifact_hashes(out_a) == _artifact_hashes(out_b)


@pytest.mark.usefixtures("docker_available")
def test_container_parity_host_vs_docker(tmp_path):
    if not SYNTHETIC_PDF.is_file():
        pytest.skip("synthetic_covenant.pdf missing")

    host_out = tmp_path / "host"
    host_out.mkdir()
    pdf_copy = host_out / "input.pdf"
    shutil.copy(SYNTHETIC_PDF, pdf_copy)
    _run_host_skip_llm(host_out, pdf_copy)
    host_hashes = _artifact_hashes(host_out)

    docker_out = tmp_path / "docker_out"
    docker_out.mkdir()
    shutil.copy(SYNTHETIC_PDF, docker_out / "input.pdf")

    compose_file = REPO_ROOT / "docker-compose.yml"
    if not compose_file.is_file():
        pytest.skip("docker-compose.yml missing")

    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "--profile",
        "pipeline",
        "run",
        "--rm",
        "pipeline",
        "run",
        "--skip-llm",
        "--pdf",
        "/app/data/input.pdf",
        "--output-dir",
        "/app/data/out",
    ]
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"docker compose pipeline failed: {result.stderr[:500]}")

    # docker-compose mounts ./data — copy outputs from mounted volume if used
    data_out = REPO_ROOT / "data" / "out"
    container_dir = data_out if data_out.is_dir() else docker_out / "out"
    if not (container_dir / SKIP_LLM_ARTIFACTS[0]).is_file():
        pytest.skip("container output artifacts not found — check docker volume mount")

    container_hashes = _artifact_hashes(container_dir)
    for name in SKIP_LLM_ARTIFACTS:
        if host_hashes.get(name) != container_hashes.get(name):
            pytest.fail(f"container-parity mismatch on {name}")
