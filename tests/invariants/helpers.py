"""Shared invariant check helpers and property-test oracles."""

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


# --- Property-test oracles (PE_Property_Test_Specs P3) ---


def apply_format_perturbation(text: str) -> str:
    """Whitespace reflow perturbation pi in Pi_format (spec metamorphic-stability P2)."""
    if not text:
        return text
    collapsed = re.sub(r"\s+", " ", text.strip())
    words = collapsed.split(" ")
    if len(words) <= 1:
        return f"  {collapsed}  \t"
    mid = len(words) // 2
    return " ".join(words[:mid]) + "\n\n\t" + "  ".join(words[mid:])


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip())


def partition_monotone_nonoverlap_violations(
    df: pd.DataFrame,
    *,
    max_page: int | None = None,
) -> list[str]:
    """chunker-partition oracle: monotonic spans, page bounds, text conservation."""
    violations: list[str] = []
    if df.empty:
        return violations

    work = df.reset_index(drop=True)
    spans: list[tuple[int, int, int]] = []
    for idx, row in work.iterrows():
        start = int(row.get("Absolute_Start_Page", 0) or 0)
        end = int(row.get("Absolute_End_Page", start) or start)
        if end < start:
            violations.append(f"row {idx}: end page {end} < start page {start}")
        if max_page is not None:
            if start < 1 or end > max_page:
                violations.append(
                    f"row {idx}: span [{start},{end}] outside [1,{max_page}]"
                )
        spans.append((idx, start, end))

    for i in range(len(spans) - 1):
        _idx_i, start_i, end_i = spans[i]
        _idx_j, start_j, _end_j = spans[i + 1]
        if end_i > start_j:
            violations.append(
                f"overlap: row {spans[i][0]} end {end_i} > row {spans[i + 1][0]} start {start_j}"
            )
        if start_j < start_i:
            violations.append(
                f"non-monotone: row {spans[i + 1][0]} start {start_j} < row {spans[i][0]} start {start_i}"
            )

    if "Raw_Text" in work.columns and len(work) > 1:
        ordered = work.sort_values(
            by=["Absolute_Start_Page", "Printed_Start_Page"],
            kind="mergesort",
        ).reset_index(drop=True)
        for i in range(len(ordered) - 1):
            start_i = int(ordered.iloc[i]["Absolute_Start_Page"])
            end_i = int(ordered.iloc[i]["Absolute_End_Page"])
            start_j = int(ordered.iloc[i + 1]["Absolute_Start_Page"])
            if end_i > start_j:
                violations.append(
                    f"sorted overlap: rows {i} and {i + 1} spans [{start_i},{end_i}] vs start {start_j}"
                )
            if start_j < start_i:
                violations.append("sorted order: non-monotone absolute start pages")

        index_order = list(work["Absolute_Start_Page"].astype(int))
        sorted_order = sorted(index_order)
        if index_order != sorted_order:
            violations.append(
                f"row order != monotone page order: {index_order} vs sorted {sorted_order}"
            )

    return violations


def body_scan_section_headers(raw_text: str) -> set[str]:
    """Independent body scan for section-style headers (coverage-audit stage 2)."""
    pattern = re.compile(
        r"(?:Article|Section)\s+\d+(?:\.\d+)?",
        re.IGNORECASE,
    )
    return {m.group(0).strip() for m in pattern.finditer(raw_text or "")}


def coverage_audit_reconciliation_violations(
    df: pd.DataFrame,
    warnings: list[str] | None = None,
) -> list[str]:
    """Soft-fail reconciliation: mismatches must appear in warnings, never raise."""
    violations: list[str] = []
    skeleton_sections = {
        str(row.get("Section", "")).strip()
        for _, row in df.iterrows()
        if str(row.get("Section", "")).strip()
    }
    body_text = " ".join(str(row.get("Raw_Text", "")) for _, row in df.iterrows())
    body_headers = body_scan_section_headers(body_text)
    warn_blob = " ".join(warnings or []).lower()

    for header in body_headers:
        normalized = header.lower().replace(" ", "")
        if not any(normalized in s.lower().replace(" ", "") for s in skeleton_sections):
            if normalized not in warn_blob and header.lower() not in warn_blob:
                violations.append(f"body header {header!r} not in skeleton or warnings")

    return violations


def compute_surviving_chunks(
    df: pd.DataFrame,
    rule: dict[str, Any],
) -> pd.DataFrame:
    """Independent oracle for router-rule-dispatch (spec P3)."""
    import re as _re

    work = df.copy()
    for col in ["Article_Title", "Section_Title", "Raw_Text"]:
        if col in work.columns:
            work[col] = work[col].fillna("")

    zone_mask = work["Article_Title"].str.upper().apply(
        lambda article: any(zone.upper() in article for zone in rule["valid_zones"])
    )
    regex_pattern = "|".join(rule["section_title_triggers"])
    trigger_mask = work["Section_Title"].str.contains(
        regex_pattern, flags=_re.IGNORECASE, regex=True
    )
    blacklist_pattern = "intentionally omitted|left blank|reserved"
    body_mask = ~work["Raw_Text"].str.contains(
        blacklist_pattern, flags=_re.IGNORECASE, regex=True
    )
    density_mask = work["Raw_Text"].str.len() > 150
    return work[zone_mask & trigger_mask & body_mask & density_mask]


def router_dispatch_violations(
    df: pd.DataFrame,
    rules: list[dict[str, Any]],
    dispatch_queue: list[dict[str, Any]],
) -> list[str]:
    """Exact recomputation oracle for single-dispatch-or-abstain."""
    violations: list[str] = []
    dispatched_targets = {item.get("Agent") for item in dispatch_queue}

    for rule in rules:
        target = rule["target_name"]
        surviving = compute_surviving_chunks(df, rule)
        count = len(surviving)
        has_envelope = target in dispatched_targets

        if count == 1 and not has_envelope:
            violations.append(f"{target}: |S_r|=1 but no envelope dispatched")
        if count != 1 and has_envelope:
            violations.append(f"{target}: |S_r|={count} but envelope dispatched (abstain expected)")

    return violations


def glossary_cycle_detection(glossary: dict[str, Any]) -> list[str]:
    """DFS cycle detection on nested_references graph (glossary-acyclic P3)."""
    circular_loops: set[str] = set()
    global_visited: set[str] = set()

    def dfs(current_term: str, current_path: list[str]) -> None:
        if current_term not in glossary:
            return
        if current_term in global_visited:
            return
        for nested_term in glossary[current_term].get("nested_references", []):
            if nested_term in current_path:
                loop_idx = current_path.index(nested_term)
                loop = current_path[loop_idx:] + [nested_term]
                circular_loops.add(" -> ".join(loop))
            else:
                dfs(nested_term, current_path + [nested_term])
        global_visited.add(current_term)

    for term in glossary:
        dfs(term, [term])

    return list(circular_loops)


def glossary_dangling_refs(
    covenants: list[dict[str, Any]],
    glossary: dict[str, Any],
) -> list[str]:
    """Detect unresolved [$REF: t] pointers (soft-fail classification)."""
    ref_pattern = re.compile(r"\[\$REF:\s*([^\]]+)\]")
    dangling: list[str] = []

    def find_pointers(node: Any) -> None:
        if isinstance(node, dict):
            for value in node.values():
                find_pointers(value)
        elif isinstance(node, list):
            for item in node:
                find_pointers(item)
        elif isinstance(node, str):
            for match in ref_pattern.findall(node):
                if match not in glossary:
                    dangling.append(match)

    find_pointers(covenants)
    return list(set(dangling))


def audit_payload_clean(audited_payload: dict) -> bool:
    """Golden-path audit status (M5 work item: warnings fail the suite)."""
    metadata = audited_payload.get("Document_Metadata", {})
    status = metadata.get("Audit_Status", "")
    warnings = metadata.get("Warnings", {})
    if status != "Clean":
        return False
    if isinstance(warnings, dict):
        return all(len(v) == 0 for v in warnings.values())
    return not warnings


def deterministic_prefix_fingerprint(paths: Any) -> dict[str, str]:
    """Hash artifacts for P_det = chunk, route, glossary (metamorphic / staging oracles)."""
    import hashlib

    def _hash_file(path: Path) -> str:
        if not path.is_file():
            return ""
        h = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    return {
        "phase1_payload": _hash_file(Path(paths.phase1_payload)),
        "dispatch_queue": _hash_file(Path(paths.dispatch_queue)),
        "glossary": _hash_file(Path(paths.glossary)),
    }
