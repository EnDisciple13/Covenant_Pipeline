"""Tests for grade_against_ledger.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from grade_against_ledger import (  # noqa: E402
    build_truth_index,
    find_truth_row,
    grade_covenant,
    grade_payload,
    load_ledger,
    main,
    normalize_value,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def _minimal_payload(ratio_limit: float | str = 4.5, agent: str = "TotalLeverageRatio") -> dict:
    return {
        "Phase1_Extracted_Covenants": [
            {
                "Agent": agent,
                "Receipt": "PDF Page 1",
                "Extracted_Data": {
                    "ratio_limit": ratio_limit,
                    "definition": "Leverage covenant",
                },
            }
        ]
    }


def test_normalize_value_sorts_dict_keys():
    assert normalize_value({"b": 2, "a": 1}) == '{"a": 1, "b": 2}'


def test_approved_match(tmp_path, capsys):
    ledger = tmp_path / "ledger.jsonl"
    payload_path = tmp_path / "payload.json"

    _write_jsonl(
        ledger,
        [
            {
                "document": "test.pdf",
                "covenant_agent": "TotalLeverageRatio",
                "receipt": "PDF Page 1",
                "verdict": "approved",
                "corrections": [],
                "analyst": "andy",
                "hat": "analyst",
                "reviewed_at": "2026-07-07T10:00:00Z",
            }
        ],
    )
    payload_path.write_text(json.dumps(_minimal_payload()), encoding="utf-8")

    exit_code = main(["--ledger", str(ledger), "--payload", str(payload_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "MATCH" in output
    assert "0 mismatch" in output


def test_corrected_match(tmp_path, capsys):
    ledger = tmp_path / "ledger.jsonl"
    payload_path = tmp_path / "payload.json"

    _write_jsonl(
        ledger,
        [
            {
                "document": "test.pdf",
                "covenant_agent": "TotalLeverageRatio",
                "receipt": "PDF Page 1",
                "verdict": "corrected",
                "corrections": [
                    {
                        "field_path": "ratio_limit",
                        "ai_value": "4.5",
                        "corrected_value": "5.0",
                    }
                ],
                "analyst": "andy",
                "hat": "analyst",
                "reviewed_at": "2026-07-07T10:00:00Z",
            }
        ],
    )
    payload_path.write_text(json.dumps(_minimal_payload(ratio_limit=5.0)), encoding="utf-8")

    exit_code = main(["--ledger", str(ledger), "--payload", str(payload_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "ratio_limit MATCH" in output


def test_corrected_mismatch(tmp_path, capsys):
    ledger = tmp_path / "ledger.jsonl"
    payload_path = tmp_path / "payload.json"

    _write_jsonl(
        ledger,
        [
            {
                "document": "test.pdf",
                "covenant_agent": "TotalLeverageRatio",
                "receipt": "PDF Page 1",
                "verdict": "corrected",
                "corrections": [
                    {
                        "field_path": "ratio_limit",
                        "ai_value": "4.5",
                        "corrected_value": "5.0",
                    }
                ],
                "analyst": "andy",
                "hat": "analyst",
                "reviewed_at": "2026-07-07T10:00:00Z",
            }
        ],
    )
    payload_path.write_text(json.dumps(_minimal_payload(ratio_limit=4.5)), encoding="utf-8")

    exit_code = main(["--ledger", str(ledger), "--payload", str(payload_path)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "ratio_limit MISMATCH" in output
    assert "1 mismatch" in output


def test_unreviewed_covenant(tmp_path, capsys):
    ledger = tmp_path / "ledger.jsonl"
    payload_path = tmp_path / "payload.json"

    _write_jsonl(ledger, [])
    payload_path.write_text(json.dumps(_minimal_payload()), encoding="utf-8")

    exit_code = main(["--ledger", str(ledger), "--payload", str(payload_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "1 unreviewed" in output
    assert "MATCH" not in output


def test_unreadable_inputs_exit_2(tmp_path):
    missing_ledger = tmp_path / "missing.jsonl"
    missing_payload = tmp_path / "missing.json"

    assert main(["--ledger", str(missing_ledger), "--payload", str(missing_payload)]) == 2


def test_latest_row_wins(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    _write_jsonl(
        ledger,
        [
            {
                "document": "test.pdf",
                "covenant_agent": "TotalLeverageRatio",
                "receipt": "PDF Page 1",
                "verdict": "corrected",
                "corrections": [
                    {
                        "field_path": "ratio_limit",
                        "ai_value": "4.5",
                        "corrected_value": "5.0",
                    }
                ],
                "analyst": "andy",
                "hat": "analyst",
                "reviewed_at": "2026-07-07T09:00:00Z",
            },
            {
                "document": "test.pdf",
                "covenant_agent": "TotalLeverageRatio",
                "receipt": "PDF Page 1",
                "verdict": "corrected",
                "corrections": [
                    {
                        "field_path": "ratio_limit",
                        "ai_value": "4.5",
                        "corrected_value": "6.0",
                    }
                ],
                "analyst": "andy",
                "hat": "analyst",
                "reviewed_at": "2026-07-07T11:00:00Z",
            },
        ],
    )

    rows = load_ledger(ledger)
    index = build_truth_index(rows)
    covenant = _minimal_payload(ratio_limit=6.0)["Phase1_Extracted_Covenants"][0]
    _, match_count, mismatch_count, unreviewed_count = grade_covenant(
        covenant,
        find_truth_row(index, "TotalLeverageRatio"),
    )

    assert mismatch_count == 0
    assert unreviewed_count == 0
    assert match_count == 2
