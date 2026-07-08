#!/usr/bin/env python3
"""Grade pipeline payload Extracted_Data against the analyst review ledger."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SKIP_FIELD_KEYS = frozenset(
    {"is_false_flag", "false_flag_reason", "is_applicable", "confidence_score"}
)


def load_ledger(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def parse_reviewed_at(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def build_truth_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["document"], row["covenant_agent"])
        existing = index.get(key)
        if existing is None:
            index[key] = row
            continue
        if parse_reviewed_at(row["reviewed_at"]) >= parse_reviewed_at(existing["reviewed_at"]):
            index[key] = row
    return index


def flatten_extracted_data(data: Any, prefix: str = "") -> list[str]:
    if isinstance(data, dict):
        paths: list[str] = []
        for key, value in data.items():
            if key.lower() in SKIP_FIELD_KEYS:
                continue
            path = f"{prefix}.{key}" if prefix else key
            paths.extend(flatten_extracted_data(value, path))
        return paths

    if isinstance(data, list):
        paths: list[str] = []
        for index, value in enumerate(data):
            path = f"{prefix}.{index}" if prefix else str(index)
            if isinstance(value, (dict, list)):
                paths.extend(flatten_extracted_data(value, path))
            else:
                paths.append(path)
        return paths

    return [prefix] if prefix else []


def get_value_at_path(data: Any, path: str) -> Any:
    current = data
    for segment in path.split("."):
        if isinstance(current, list):
            current = current[int(segment)]
        else:
            current = current[segment]
    return current


def normalize_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def find_truth_row(
    index: dict[tuple[str, str], dict[str, Any]],
    covenant_agent: str,
) -> dict[str, Any] | None:
    matches = [row for (_, agent), row in index.items() if agent == covenant_agent]
    if not matches:
        return None
    return max(matches, key=lambda row: parse_reviewed_at(row["reviewed_at"]))


def truth_for_path(
    row: dict[str, Any],
    extracted_data: dict[str, Any],
    field_path: str,
) -> str:
    corrections_by_path = {item["field_path"]: item for item in row.get("corrections", [])}

    if row["verdict"] == "corrected" and field_path in corrections_by_path:
        return corrections_by_path[field_path]["corrected_value"]

    return normalize_value(get_value_at_path(extracted_data, field_path))


def grade_covenant(
    covenant: dict[str, Any],
    truth_row: dict[str, Any] | None,
) -> tuple[list[str], int, int, int]:
    lines: list[str] = []
    agent = covenant.get("Agent", "unknown")
    extracted = covenant.get("Extracted_Data") or {}

    if truth_row is None:
        return lines, 0, 0, 1

    match_count = 0
    mismatch_count = 0

    for field_path in flatten_extracted_data(extracted):
        actual = normalize_value(get_value_at_path(extracted, field_path))
        expected = truth_for_path(truth_row, extracted, field_path)
        status = "MATCH" if actual == expected else "MISMATCH"
        lines.append(f"{agent}::{field_path} {status}")
        if status == "MATCH":
            match_count += 1
        else:
            mismatch_count += 1

    return lines, match_count, mismatch_count, 0


def grade_payload(
    payload: dict[str, Any],
    index: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[str], int, int, int]:
    all_lines: list[str] = []
    total_match = 0
    total_mismatch = 0
    total_unreviewed = 0

    for covenant in payload.get("Phase1_Extracted_Covenants", []):
        truth_row = find_truth_row(index, covenant.get("Agent", ""))
        lines, match_count, mismatch_count, unreviewed_count = grade_covenant(covenant, truth_row)
        all_lines.extend(lines)
        total_match += match_count
        total_mismatch += mismatch_count
        total_unreviewed += unreviewed_count

    return all_lines, total_match, total_mismatch, total_unreviewed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, help="Path to review_ledger.jsonl")
    parser.add_argument("--payload", required=True, help="Path to audited JSON payload")
    args = parser.parse_args(argv)

    ledger_path = Path(args.ledger)
    payload_path = Path(args.payload)

    try:
        rows = load_ledger(ledger_path)
        with open(payload_path, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unreadable input: {exc}", file=sys.stderr)
        return 2

    index = build_truth_index(rows)
    lines, match_count, mismatch_count, unreviewed_count = grade_payload(payload, index)

    for line in lines:
        print(line)
    print(f"{match_count} match / {mismatch_count} mismatch / {unreviewed_count} unreviewed")

    return 1 if mismatch_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
