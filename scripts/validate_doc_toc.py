#!/usr/bin/env python3
"""Validate and generate nested ToC for PROJECT_DOCUMENTATION.md."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "PROJECT_DOCUMENTATION.md"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
TOC_LINK_RE = re.compile(r"^\s*(?:-\s*)?\[([^\]]+)\]\(#([^)]+)\)\s*$")
MARKUP_RE = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*")
PANDOC_ID_RE = re.compile(r"\s*\{#[^}]+\}\s*$")
INLINE_CODE_RE = re.compile(r"`([^`]*)`")
TOC_TITLE = "Table of Contents"


def strip_heading_text(raw: str) -> str:
    text = PANDOC_ID_RE.sub("", raw).strip()
    text = INLINE_CODE_RE.sub(r"\1", text)

    def _strip_emphasis(match: re.Match[str]) -> str:
        return match.group(1) or match.group(2) or ""

    return MARKUP_RE.sub(_strip_emphasis, text).strip()


def github_slug(text: str) -> str:
    """GitHub heading slug: lowercase, strip punctuation, spaces to hyphens."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def iter_document_headings(
    lines: list[str], *, max_level: int = 6
) -> list[tuple[int, str, str]]:
    """Yield (level, title, slug) for each heading outside fenced code blocks."""
    seen: dict[str, int] = {}
    headings: list[tuple[int, str, str]] = []
    in_fence = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        match = HEADING_RE.match(line)
        if not match:
            continue

        level = len(match.group(1))
        if level > max_level:
            continue

        title = strip_heading_text(match.group(2))
        base = github_slug(title)
        if not base:
            continue

        count = seen.get(base, 0)
        slug = base if count == 0 else f"{base}-{count}"
        seen[base] = count + 1
        headings.append((level, title, slug))

    return headings


def build_heading_slugs(lines: list[str]) -> set[str]:
    return {slug for _, _, slug in iter_document_headings(lines)}


def parse_toc_links(lines: list[str]) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for line in lines:
        match = TOC_LINK_RE.match(line)
        if match:
            links.append((match.group(1), match.group(2)))
    return links


def generate_toc_lines(lines: list[str], *, max_level: int = 3) -> list[str]:
    """Build a nested bullet ToC indented by heading level (h1–h3)."""
    headings = iter_document_headings(lines, max_level=max_level)
    if not headings:
        return []

    min_level = min(level for level, _, _ in headings)
    toc_lines: list[str] = []
    prev_level: int | None = None

    for level, title, slug in headings:
        indent = "  " * (level - min_level)
        line = f"{indent}- [{title}](#{slug})"
        if prev_level is not None and level <= min_level:
            toc_lines.append("")
        toc_lines.append(line)
        prev_level = level

    return toc_lines


def replace_toc_block(lines: list[str], toc_lines: list[str]) -> list[str]:
    """Replace the manual ToC block beneath the title heading."""
    if not lines or not HEADING_RE.match(lines[0]):
        raise ValueError("document must start with the Table of Contents heading")

    body_start = 1
    while body_start < len(lines):
        match = HEADING_RE.match(lines[body_start])
        if match and len(match.group(1)) == 1:
            break
        body_start += 1

    return [lines[0], ""] + toc_lines + [""] + lines[body_start:]


def validate(lines: list[str]) -> int:
    heading_slugs = build_heading_slugs(lines)
    toc_links = parse_toc_links(lines)

    if not toc_links:
        print("ERROR: no ToC links found", file=sys.stderr)
        return 1

    missing: list[tuple[str, str]] = []
    for label, fragment in toc_links:
        if fragment not in heading_slugs:
            missing.append((label, fragment))

    if missing:
        print(f"ToC validation failed: {len(missing)} broken link(s) in {DOC_PATH.name}")
        for label, fragment in missing:
            print(f"  - [{label}](#{fragment})")
        return 1

    print(f"OK: {len(toc_links)} ToC links match heading slugs in {DOC_PATH.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Regenerate nested ToC from headings (h1–h3) and write back to the doc",
    )
    parser.add_argument(
        "--max-level",
        type=int,
        default=3,
        help="Maximum heading level to include when generating ToC (default: 3)",
    )
    args = parser.parse_args(argv)

    if not DOC_PATH.is_file():
        print(f"ERROR: missing {DOC_PATH}", file=sys.stderr)
        return 1

    lines = DOC_PATH.read_text(encoding="utf-8").splitlines()

    if args.generate:
        toc_lines = generate_toc_lines(lines, max_level=args.max_level)
        updated = replace_toc_block(lines, toc_lines)
        DOC_PATH.write_text("\n".join(updated) + "\n", encoding="utf-8")
        print(f"Wrote nested ToC ({len(toc_lines)} entries) to {DOC_PATH.name}")
        lines = updated

    return validate(lines)


if __name__ == "__main__":
    raise SystemExit(main())
