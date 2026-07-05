"""Generate a minimal covenant PDF for invariant tests (Hallador-tuned spread map)."""

from __future__ import annotations

from pathlib import Path

import fitz


def build_synthetic_covenant_pdf(path: Path) -> None:
    """Build a multi-page PDF with one covenant section and non-empty extraction."""
    doc = fitz.open()

    for i in range(10):
        page = doc.new_page()
        page.insert_text((72, 72), f"Front matter page {i + 1}")

    toc = doc.new_page()
    toc.insert_text(
        (72, 72),
        "TABLE OF CONTENTS\n\n"
        "Article 7. Covenants 5\n"
        "Section 7.1. Total Leverage Ratio 5\n",
    )
    toc.insert_text((72, 750), "1", fontsize=10)

    p12 = doc.new_page()
    p12.insert_text((72, 72), "Continuation of table of contents.")
    p12.insert_text((72, 750), "2", fontsize=10)

    for printed in (3, 4):
        pad = doc.new_page()
        pad.insert_text((72, 72), f"Intermediate page {printed}")
        pad.insert_text((72, 750), str(printed), fontsize=10)

    # Pad past max_toc_pages (20) so body headers are not mistaken for TOC entries.
    for i in range(6):
        pad = doc.new_page()
        pad.insert_text((72, 72), f"Boilerplate page {i + 1}")

    body = doc.new_page()
    body.insert_text((72, 72), "Section 7.1")
    body.insert_text((72, 96), "Total Leverage Ratio")
    body.insert_text(
        (72, 120),
        "The Borrower shall not permit the Total Leverage Ratio to exceed 4.50 to 1.00.",
    )
    body.insert_text((72, 750), "5", fontsize=10)

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    doc.close()


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "synthetic_covenant.pdf"
    build_synthetic_covenant_pdf(out)
    print(f"Wrote {out}")
