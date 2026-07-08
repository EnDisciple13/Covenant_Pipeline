"""FastAPI backend for the Covenant Pipeline viewer."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

app = FastAPI(title="Covenant Viewer Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DiagnosticLayer = Literal["L0", "L1", "L2", "L3", "unknown"]
Verdict = Literal["approved", "corrected"]


class CorrectionIn(BaseModel):
    field_path: str
    ai_value: str
    corrected_value: str
    diagnostic_layer: DiagnosticLayer | None = None
    analyst_note: str | None = None


class ReviewRequest(BaseModel):
    covenant_agent: str
    receipt: str
    verdict: Verdict
    corrections: list[CorrectionIn] = Field(default_factory=list)
    analyst: str = "andy"
    hat: str = "analyst"

    @model_validator(mode="after")
    def validate_corrections_for_verdict(self) -> ReviewRequest:
        if self.verdict == "corrected" and not self.corrections:
            raise ValueError("corrected verdict requires at least one correction")
        return self


def _audited_json_path() -> Path:
    raw = os.environ.get("COVENANT_AUDITED_JSON")
    if not raw:
        raise HTTPException(
            status_code=500,
            detail="COVENANT_AUDITED_JSON environment variable is not set.",
        )
    return Path(raw).resolve()


def _pdf_path() -> Path:
    raw = os.environ.get("COVENANT_PDF_PATH")
    if not raw:
        raise HTTPException(
            status_code=500,
            detail="COVENANT_PDF_PATH environment variable is not set.",
        )
    return Path(raw).resolve()


def _output_dir() -> Path | None:
    raw = os.environ.get("COVENANT_OUTPUT_DIR")
    return Path(raw).resolve() if raw else None


def _dispatch_queue_path() -> Path | None:
    raw = os.environ.get("COVENANT_DISPATCH_QUEUE_JSON")
    if raw:
        return Path(raw).resolve()
    output_dir = _output_dir()
    if output_dir:
        return output_dir / "dispatch_queue_output.json"
    return None


def _review_ledger_path() -> Path:
    raw = os.environ.get("COVENANT_REVIEW_LEDGER")
    if raw:
        return Path(raw).resolve()
    output_dir = _output_dir()
    if output_dir:
        return output_dir / "review" / "review_ledger.jsonl"
    raise HTTPException(
        status_code=500,
        detail=(
            "COVENANT_REVIEW_LEDGER or COVENANT_OUTPUT_DIR must be set "
            "to resolve review ledger path."
        ),
    )


def _load_audited_payload() -> dict:
    path = _audited_json_path()
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Audited payload not found: {path}",
        )
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _find_critic_confidence(payload: dict, covenant_agent: str, receipt: str) -> float | None:
    for covenant in payload.get("Phase1_Extracted_Covenants", []):
        if covenant.get("Agent") == covenant_agent and covenant.get("Receipt") == receipt:
            audit = covenant.get("Validation_Audit") or {}
            score = audit.get("confidence_score")
            return float(score) if score is not None else None
    return None


def _serialize_correction(correction: CorrectionIn) -> dict[str, Any]:
    row: dict[str, Any] = {
        "field_path": correction.field_path,
        "ai_value": correction.ai_value,
        "corrected_value": correction.corrected_value,
    }
    if correction.diagnostic_layer is not None:
        row["diagnostic_layer"] = correction.diagnostic_layer
    if correction.analyst_note is not None:
        row["analyst_note"] = correction.analyst_note
    return row


def _build_review_row(request: ReviewRequest) -> dict[str, Any]:
    payload = _load_audited_payload()
    row: dict[str, Any] = {
        "document": _pdf_path().name,
        "covenant_agent": request.covenant_agent,
        "receipt": request.receipt,
        "verdict": request.verdict,
        "corrections": [_serialize_correction(c) for c in request.corrections],
        "analyst": request.analyst,
        "hat": request.hat,
        "reviewed_at": _utc_now_iso(),
    }
    critic_confidence = _find_critic_confidence(payload, request.covenant_agent, request.receipt)
    if critic_confidence is not None:
        row["critic_confidence"] = critic_confidence
    return row


def _append_review_row(row: dict[str, Any]) -> None:
    ledger_path = _review_ledger_path()
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as file:
        file.write(json.dumps(row) + "\n")


def _read_review_rows() -> list[dict[str, Any]]:
    ledger_path = _review_ledger_path()
    if not ledger_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with open(ledger_path, "r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


@app.get("/api/document-data")
def get_document_data():
    return _load_audited_payload()


@app.get("/api/pdf")
def get_source_pdf():
    file_path = _pdf_path()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF not found: {file_path}")
    return FileResponse(file_path, media_type="application/pdf")


@app.get("/api/pipeline-summary")
def get_pipeline_summary():
    from covenant_pipeline.report.summary import build_pipeline_summary

    payload = _load_audited_payload()
    return build_pipeline_summary(
        payload,
        dispatch_path=_dispatch_queue_path(),
        audited_json_path=str(_audited_json_path()),
        pdf_path=str(_pdf_path()),
    )


@app.post("/api/review")
def post_review(request: ReviewRequest):
    row = _build_review_row(request)
    _append_review_row(row)
    return row


@app.get("/api/review")
def get_reviews():
    return _read_review_rows()
