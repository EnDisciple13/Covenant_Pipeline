"""Tests for the Covenant Viewer review ledger API."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "viewer" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: E402


@pytest.fixture
def client(monkeypatch, tmp_path):
    ledger_path = tmp_path / "review_ledger.jsonl"
    audited_path = tmp_path / "audited.json"
    pdf_path = tmp_path / "Credit_Agreement_Test.pdf"
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    audited_path.write_text(
        json.dumps(
            {
                "Phase1_Extracted_Covenants": [
                    {
                        "Agent": "TotalLeverageRatio",
                        "Receipt": "PDF Page 1 | Section 7.1",
                        "Extracted_Data": {"ratio_limit": 4.5},
                        "Validation_Audit": {
                            "is_verified": True,
                            "confidence_score": 0.95,
                            "flagged_discrepancies": None,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    pdf_path.write_bytes(b"%PDF-1.4 test")

    monkeypatch.setenv("COVENANT_REVIEW_LEDGER", str(ledger_path))
    monkeypatch.setenv("COVENANT_AUDITED_JSON", str(audited_path))
    monkeypatch.setenv("COVENANT_PDF_PATH", str(pdf_path))
    monkeypatch.setenv("COVENANT_OUTPUT_DIR", str(output_dir))

    return TestClient(app)


def test_post_approved_appends_valid_jsonl(client, tmp_path):
    ledger_path = tmp_path / "review_ledger.jsonl"

    response = client.post(
        "/api/review",
        json={
            "covenant_agent": "TotalLeverageRatio",
            "receipt": "PDF Page 1 | Section 7.1",
            "verdict": "approved",
            "corrections": [],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "approved"
    assert body["document"] == "Credit_Agreement_Test.pdf"
    assert body["covenant_agent"] == "TotalLeverageRatio"
    assert body["corrections"] == []
    assert body["analyst"] == "andy"
    assert body["hat"] == "analyst"
    assert body["critic_confidence"] == 0.95
    assert body["reviewed_at"].endswith("Z")

    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    stored = json.loads(lines[0])
    assert stored == body


def test_post_corrected_with_enrichment(client):
    response = client.post(
        "/api/review",
        json={
            "covenant_agent": "TotalLeverageRatio",
            "receipt": "PDF Page 1 | Section 7.1",
            "verdict": "corrected",
            "corrections": [
                {
                    "field_path": "ratio_limit",
                    "ai_value": "4.5",
                    "corrected_value": "5.0",
                    "diagnostic_layer": "L0",
                    "analyst_note": "Threshold misread from table footnote",
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "corrected"
    correction = body["corrections"][0]
    assert correction["diagnostic_layer"] == "L0"
    assert correction["analyst_note"] == "Threshold misread from table footnote"


def test_post_corrected_empty_corrections_returns_422(client):
    response = client.post(
        "/api/review",
        json={
            "covenant_agent": "TotalLeverageRatio",
            "receipt": "PDF Page 1 | Section 7.1",
            "verdict": "corrected",
            "corrections": [],
        },
    )

    assert response.status_code == 422


def test_post_missing_ledger_env_vars_returns_named_500(monkeypatch, tmp_path):
    audited_path = tmp_path / "audited.json"
    pdf_path = tmp_path / "test.pdf"
    audited_path.write_text(
        json.dumps({"Phase1_Extracted_Covenants": []}),
        encoding="utf-8",
    )
    pdf_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setenv("COVENANT_AUDITED_JSON", str(audited_path))
    monkeypatch.setenv("COVENANT_PDF_PATH", str(pdf_path))
    monkeypatch.delenv("COVENANT_REVIEW_LEDGER", raising=False)
    monkeypatch.delenv("COVENANT_OUTPUT_DIR", raising=False)

    test_client = TestClient(app)
    response = test_client.post(
        "/api/review",
        json={
            "covenant_agent": "TotalLeverageRatio",
            "receipt": "PDF Page 1",
            "verdict": "approved",
            "corrections": [],
        },
    )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert "COVENANT_REVIEW_LEDGER" in detail
    assert "COVENANT_OUTPUT_DIR" in detail


def test_get_returns_posted_rows_newest_last(client):
    first = client.post(
        "/api/review",
        json={
            "covenant_agent": "TotalLeverageRatio",
            "receipt": "PDF Page 1 | Section 7.1",
            "verdict": "approved",
            "corrections": [],
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/api/review",
        json={
            "covenant_agent": "InterestCoverageRatio",
            "receipt": "PDF Page 2 | Section 7.2",
            "verdict": "approved",
            "corrections": [],
        },
    )
    assert second.status_code == 200

    response = client.get("/api/review")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    assert rows[0]["covenant_agent"] == "TotalLeverageRatio"
    assert rows[1]["covenant_agent"] == "InterestCoverageRatio"
