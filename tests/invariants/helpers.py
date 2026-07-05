"""Shared invariant check helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


def empty_raw_text_rows(df: pd.DataFrame) -> list[tuple[str, int]]:
    """Return (Section, row_index) for skeleton rows with empty Raw_Text."""
    violations: list[tuple[str, int]] = []
    for idx, row in df.iterrows():
        raw = row.get("Raw_Text")
        if pd.isna(raw) or str(raw).strip() == "":
            section = str(row.get("Section", idx))
            violations.append((section, int(idx)))
    return violations


def iter_leaf_strings(value: Any) -> Iterable[str]:
    """Yield string leaf values from nested dict/list structures."""
    if isinstance(value, dict):
        for child in value.values():
            yield from iter_leaf_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_leaf_strings(child)
    elif isinstance(value, str):
        stripped = value.strip()
        if stripped and not stripped.startswith("[$REF:"):
            yield stripped


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def provenance_grounding_violations(
    audited_payload: dict,
    phase1_df: pd.DataFrame,
) -> list[str]:
    """Receipt-joined substring check for extracted leaf strings."""
    from covenant_pipeline.phases.validation import build_rehydration_db

    lookup = build_rehydration_db(phase1_df)
    if not lookup:
        return ["empty rehydration database"]

    violations: list[str] = []
    covenants = audited_payload.get("Phase1_Extracted_Covenants", [])
    for covenant in covenants:
        receipt = str(covenant.get("Receipt", "")).strip()
        source = lookup.get(receipt)
        if source is None:
            normalized_keys = {normalize_text(k): k for k in lookup}
            source = lookup.get(normalized_keys.get(normalize_text(receipt), ""))
        if source is None:
            violations.append(f"missing receipt: {receipt[:80]}")
            continue
        norm_source = normalize_text(source)
        for leaf in iter_leaf_strings(covenant.get("Extracted_Data", {})):
            norm_leaf = normalize_text(leaf)
            if len(norm_leaf) < 4:
                continue
            if norm_leaf not in norm_source:
                violations.append(f"ungrounded leaf for {receipt[:40]}: {leaf[:60]}")
    return violations


def file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)
