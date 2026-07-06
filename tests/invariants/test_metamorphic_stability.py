"""Hypothesis property: metamorphic-stability — P_det invariant under format perturbation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from covenant_pipeline.config import PipelinePaths
from covenant_pipeline.orchestrator import run_full_pipeline
from covenant_pipeline.phases.glossary import run_glossary
from covenant_pipeline.phases.router import Tier1DeterministicRouter
from tests.conftest import SYNTHETIC_PDF
from tests.invariants.helpers import (
    apply_format_perturbation,
    deterministic_prefix_fingerprint,
    normalize_whitespace,
)


def _run_det_prefix(tmp_path: Path, pdf_path: Path) -> dict[str, str]:
    paths = PipelinePaths(output_dir=tmp_path / "out", pdf_path=pdf_path)
    run_full_pipeline(paths, skip_llm=True)
    return deterministic_prefix_fingerprint(paths)


@given(st.text(min_size=1, max_size=500, alphabet=st.characters(blacklist_categories=("Cs",))))
@settings(max_examples=25, deadline=None)
@example("Section 7.01  Maximum Total Leverage Ratio covenant text here.")
@example("Article 1 Definitions\n\n  means  the  Borrower  ")
def test_reflow_prefix_invariant(text: str):
    """P_det outputs identical under whitespace reflow on route inputs."""
    from tests.conftest import REPO_ROOT

    config_path = REPO_ROOT / "config" / "covenant_config.json"
    base_df = pd.DataFrame(
        [
            {
                "Article": "Article 7",
                "Article_Title": "AFFIRMATIVE COVENANTS",
                "Section": "Section 7.01",
                "Section_Title": "Financial Covenants",
                "Raw_Text": text * 3 if len(text) < 60 else text,
                "Printed_Start_Page": 1,
                "Absolute_Start_Page": 1,
                "Absolute_End_Page": 2,
            }
        ]
    )
    perturbed = base_df.copy()
    perturbed["Raw_Text"] = perturbed["Raw_Text"].map(apply_format_perturbation)

    router = Tier1DeterministicRouter(config_path)
    dispatch_a = router.route_document(base_df)
    dispatch_b = router.route_document(perturbed)

    norm_a = json.dumps(dispatch_a, sort_keys=True, default=str)
    norm_b = json.dumps(dispatch_b, sort_keys=True, default=str)
    assert norm_a == norm_b, "route dispatch must be invariant under whitespace reflow"


@pytest.mark.skipif(not SYNTHETIC_PDF.is_file(), reason="synthetic PDF missing")
def test_reflow_prefix_invariant_integration(tmp_path):
    """Full P_det fingerprint stable across two skip-llm runs on golden fixture."""
    pdf_copy = tmp_path / "input.pdf"
    shutil.copy(SYNTHETIC_PDF, pdf_copy)
    fp_a = _run_det_prefix(tmp_path / "a", pdf_copy)
    fp_b = _run_det_prefix(tmp_path / "b", pdf_copy)
    assert fp_a == fp_b
    assert all(fp_a.values()), "P_det artifacts must be non-empty"
