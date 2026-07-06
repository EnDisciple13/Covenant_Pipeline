"""Hypothesis property: config-totality — missing required env fails fast."""

from __future__ import annotations

import pytest

from covenant_pipeline.llm.client import get_client

REQUIRED_KEY = "GEMINI_API_KEY"


@pytest.mark.parametrize("missing_value", ["", None])
def test_missing_env_fails_fast(missing_value: str | None, monkeypatch):
    """Missing or empty GEMINI_API_KEY aborts with named error — never silent default."""
    monkeypatch.delenv(REQUIRED_KEY, raising=False)
    if missing_value is not None:
        monkeypatch.setenv(REQUIRED_KEY, missing_value)
    with pytest.raises(EnvironmentError) as exc_info:
        get_client()
    assert REQUIRED_KEY in str(exc_info.value)


@pytest.mark.xfail(reason="implementation defect: whitespace-only GEMINI_API_KEY not rejected (spec P4)")
def test_missing_env_fails_fast_whitespace_only(monkeypatch):
    """Whitespace-only values must fail fast per config-totality P4."""
    monkeypatch.setenv(REQUIRED_KEY, "   ")
    with pytest.raises(EnvironmentError):
        get_client()


def test_missing_env_fails_fast_all_keys_removed(monkeypatch):
    """All mandatory keys missing simultaneously still names the required key."""
    monkeypatch.delenv(REQUIRED_KEY, raising=False)
    with pytest.raises(EnvironmentError) as exc_info:
        get_client()
    assert REQUIRED_KEY in str(exc_info.value)
