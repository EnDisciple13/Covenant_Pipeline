# Test fixtures

## Synthetic covenant PDF (committed)

`synthetic_covenant.pdf` is a small generated PDF for deterministic `--skip-llm` invariant tests. Regenerate with:

```bash
py tests/fixtures/build_synthetic_pdf.py
```

## Hallador golden PDF (Git LFS)

For full-fidelity tests against the production credit agreement, add:

```
tests/fixtures/Credit_Agreement_Hallador.pdf
```

Tracked via Git LFS (see repo `.gitattributes`). After clone:

```bash
git lfs pull
```

If the LFS object is not yet committed, place the file locally and run `git lfs track` is already configured for `tests/fixtures/*.pdf`.

## Golden artifacts

`golden/` holds committed baseline outputs for parity and provenance checks. Regenerate from a clean `--skip-llm` run into `golden_run/` then copy stable artifacts into `golden/`.
