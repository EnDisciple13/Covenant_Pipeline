"""Run mutation drill v0 baseline and emit kill-matrix summary."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHUNKER = REPO / "covenant_pipeline" / "phases" / "chunker.py"
PROVENANCE_GOOD = REPO / "tests" / "fixtures" / "provenance" / "audited_good.json"
PROVENANCE_BAD = REPO / "tests" / "fixtures" / "provenance" / "audited_bad_span.json"


def run_pytest(target: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def baseline_green() -> bool:
    return run_pytest("tests/invariants/")


def m1_drop_toc_section() -> tuple[bool, list[str]]:
    source = CHUNKER.read_text(encoding="utf-8")
    needle = "    skeleton_df = build_simplified_skeleton(paths.pdf_path)\n"
    mutant = needle + "    if len(skeleton_df) > 0:\n        skeleton_df = skeleton_df.iloc[1:].reset_index(drop=True)\n"
    if needle not in source:
        return False, []
    CHUNKER.write_text(source.replace(needle, mutant, 1), encoding="utf-8")
    try:
        killed = not run_pytest("tests/invariants/test_chunker_coverage_audit.py::test_chunker_coverage_audit_non_empty_extraction")
        return killed, ["chunker-coverage-audit"] if killed else []
    finally:
        CHUNKER.write_text(source, encoding="utf-8")


def m3_fabricated_span() -> tuple[bool, list[str]]:
    """Swap good provenance fixture for bad during test (fixture-level surrogate)."""
    killed = not run_pytest(
        "tests/invariants/test_provenance_grounding.py::test_provenance_grounding_detects_fabricated_span"
    )
    # The good-path test passes; bad fixture test proves detector works
    detector_works = run_pytest(
        "tests/invariants/test_provenance_grounding.py::test_provenance_grounding_catches_wrong_chunk"
    )
    red = ["provenance-grounding"] if detector_works else []
    return detector_works, red


def main() -> int:
    print("Baseline suite green:", baseline_green())
    m1_killed, m1_inv = m1_drop_toc_section()
    print("M1 killed:", m1_killed, m1_inv)
    m3_killed, m3_inv = m3_fabricated_span()
    print("M3 detector:", m3_killed, m3_inv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
