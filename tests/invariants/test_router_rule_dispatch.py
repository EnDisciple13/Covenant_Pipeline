"""Hypothesis property: router-rule-dispatch — single dispatch or abstain."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from hypothesis import example, given, settings
from hypothesis import strategies as st

from covenant_pipeline.phases.router import Tier1DeterministicRouter
from tests.conftest import REPO_ROOT
from tests.invariants.helpers import router_dispatch_violations

CONFIG_PATH = REPO_ROOT / "config" / "covenant_config.json"


def _load_rules() -> list[dict]:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return data.get("routing_rules", [])


def _make_chunk(
    article_title: str,
    section_title: str,
    raw_text: str,
) -> dict:
    return {
        "Article": "Article 7",
        "Article_Title": article_title,
        "Section": "Section 7.01",
        "Section_Title": section_title,
        "Raw_Text": raw_text,
        "Printed_Start_Page": 1,
        "Absolute_Start_Page": 1,
        "Absolute_End_Page": 2,
    }


@given(
    st.lists(
        st.tuples(
            st.sampled_from(["AFFIRMATIVE COVENANTS", "OTHER ARTICLE"]),
            st.sampled_from(["Financial Covenants", "Reserved", "Intentionally omitted"]),
            st.text(min_size=0, max_size=300),
        ),
        min_size=0,
        max_size=12,
    )
)
@settings(max_examples=40, deadline=None)
@example([])
@example([("AFFIRMATIVE COVENANTS", "Financial Covenants", "x" * 200)])
def test_single_dispatch_or_abstain(chunk_specs: list[tuple[str, str, str]]):
    """Each rule dispatches iff exactly one chunk survives the fiber product."""
    chunks = [
        _make_chunk(article, section, text if len(text) > 160 else text + " " + "x" * 180)
        for article, section, text in chunk_specs
    ]
    df = pd.DataFrame(chunks) if chunks else pd.DataFrame(
        columns=["Article", "Article_Title", "Section", "Section_Title", "Raw_Text"]
    )
    rules = _load_rules()
    router = Tier1DeterministicRouter(CONFIG_PATH)
    dispatch = router.route_document(df)
    violations = router_dispatch_violations(df, rules, dispatch)
    assert violations == [], f"dispatch violations: {violations}"
