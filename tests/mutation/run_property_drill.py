"""Run mutation drill M1-M8 against property-test suite (2026-07-06)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _pytest() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/invariants/", "-q", "--tb=no"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def _git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=REPO, check=True)


def main() -> int:
    print("Baseline pytest...")
    code, out = _pytest()
    print(out)
    if code != 0:
        print("Baseline not green; abort drill.")
        return 1

    results: list[tuple[str, str, bool]] = []

    # M2: swap first two chunk rows (monotonicity)
    chunker = REPO / "covenant_pipeline" / "phases" / "chunker.py"
    original = chunker.read_text(encoding="utf-8")
    needle = "    payload_df.to_csv(payload_path, index=False)"
    mutant = (
        "    if len(payload_df) >= 2:\n"
        "        payload_df = payload_df.iloc[[1, 0] + list(range(2, len(payload_df)))].reset_index(drop=True)\n"
        "    elif len(payload_df) == 1:\n"
        "        payload_df.at[payload_df.index[0], \"Absolute_Start_Page\"] = (\n"
        "            int(payload_df.at[payload_df.index[0], \"Absolute_End_Page\"]) + 5\n"
        "        )\n"
        "    payload_df.to_csv(payload_path, index=False)"
    )
    chunker.write_text(original.replace(needle, mutant, 1), encoding="utf-8")
    code, _ = _pytest()
    killed = code != 0
    results.append(("M2", "chunker-partition / reorder", killed))
    chunker.write_text(original, encoding="utf-8")

    # M5: inject circular glossary via audit payload (glossary output path)
    glossary = REPO / "covenant_pipeline" / "phases" / "glossary.py"
    g_orig = glossary.read_text(encoding="utf-8")
    g_needle = "    save_json(paths.glossary, master_glossary, indent=2)"
    g_mutant = (
        "    master_glossary[\"MutA\"] = {\"raw_definition_text\": \"a\", \"nested_references\": [\"MutB\"]}\n"
        "    master_glossary[\"MutB\"] = {\"raw_definition_text\": \"b\", \"nested_references\": [\"MutA\"]}\n"
        "    save_json(paths.glossary, master_glossary, indent=2)"
    )
    glossary.write_text(g_orig.replace(g_needle, g_mutant, 1), encoding="utf-8")
    code, _ = _pytest()
    killed = code != 0
    results.append(("M5", "glossary-acyclic / cycle", killed))
    glossary.write_text(g_orig, encoding="utf-8")

    # M6: silent default for missing GEMINI_API_KEY
    client = REPO / "covenant_pipeline" / "llm" / "client.py"
    c_orig = client.read_text(encoding="utf-8")
    c_needle = (
        '        raise EnvironmentError(\n'
        '            "GEMINI_API_KEY is required for LLM stages (extract, validate). "\n'
        '            "Copy .env.example to .env in the project root and set your key, "\n'
        '            "or export GEMINI_API_KEY in your shell."\n'
        "        )"
    )
    c_mutant = '        api_key = "silent-default-key-for-mutation-drill"'
    client.write_text(c_orig.replace(c_needle, c_mutant, 1), encoding="utf-8")
    code, _ = _pytest()
    killed = code != 0
    results.append(("M6", "config-totality / silent default", killed))
    client.write_text(c_orig, encoding="utf-8")

    # M7: skew page span outside bounds
    chunker.write_text(original, encoding="utf-8")
    m7_needle = "    payload_df.to_csv(payload_path, index=False)"
    m7_mutant = (
        "    if len(payload_df) > 0:\n"
        "        payload_df.at[payload_df.index[0], \"Absolute_End_Page\"] = 99999\n"
        "    payload_df.to_csv(payload_path, index=False)"
    )
    chunker.write_text(original.replace(m7_needle, m7_mutant, 1), encoding="utf-8")
    code, _ = _pytest()
    killed = code != 0
    results.append(("M7", "chunker-partition / bbox-page", killed))
    chunker.write_text(original, encoding="utf-8")

    print("\n=== Kill matrix (M2/M5/M6/M7) ===")
    for mid, desc, killed in results:
        print(f"{mid} {desc}: {'KILLED' if killed else 'SURVIVED'}")

    survivors = [mid for mid, _, k in results if not k]
    return 1 if survivors else 0


if __name__ == "__main__":
    raise SystemExit(main())
