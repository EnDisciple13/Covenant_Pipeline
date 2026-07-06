# Mutation drill harness (v0 — agent-driven runbook)

Runtime counterpart of the Notes trap-fixture harnesses: inject a deliberate, subtle Type B bug; the invariant suite must go red. Every **surviving mutant names a missing invariant** — a work item by construction, and a priority input to `/invariant-propose`.

Theory: Notes `meta/Invariant_Authorship.md` §VI.2 (drills, kill rate) and §VIII (mechanical anchor role). Plan: Notes `inbox/2026-07-04-invariant-loop-plan.md` §II.2. Philosophy + fixture/drill symmetry: Notes `tests/README.md`.

**Precondition (Stage 0):** priority invariant tests implemented in `tests/invariants/` (2026-07-05): `chunker-coverage-audit`, `provenance-grounding`, `container-parity` (host reproducibility; docker parity skips if unavailable).

## Protocol (per drill)

1. Clean baseline: full deterministic-prefix run (`--skip-llm`) on the golden fixture; invariant suite green; `git status` clean.
2. Apply ONE mutation from the canned list (single-site, minimal diff).
3. Run the invariant suite (and the audit phase where relevant).
4. Record in the kill matrix: which invariant(s) went red. **All green = surviving mutant** → open a work item naming the missing invariant.
5. `git checkout -- .` (revert). Verify clean baseline again before the next drill.

Design rule for any new mutation: **subtle, single-site, Type B** — plausible output, wrong content; something code review would miss. A mutation that crashes the pipeline is testing the wrong thing (that's a Type A error; the suite exists for the silent ones).

## Canned mutation list (v0 — frontier-authored 2026-07-05)

| # | Mutation | Target | Should be killed by |
|---|----------|--------|---------------------|
| M1 | Silently drop one TOC section during skeleton build | `covenant_pipeline/phases/chunker.py` | `chunker-coverage-audit` (non-empty + TOC reconciliation) |
| M2 | Reorder two chunks (swap positions, keep content) | chunker output path | `chunker-partition` (monotonicity) |
| M3 | Fabricate a citation span: plausible offset, wrong chunk | extraction/compile boundary | `provenance-grounding` |
| M4 | Cast one numeric covenant field to string | compile step | audit type-safety predicate |
| M5 | Introduce a circular glossary reference two hops deep | glossary output | `glossary-acyclic` (audit DFS) |
| M6 | Remove a required env var; supply a plausible silent default | container config | `config-totality` |
| M7 | Skew one bbox outside page bounds | chunker spatial output | `chunker-partition` (bbox-in-page) |
| M8 | Point one chunk's (Article, Section) receipt at the adjacent section | chunker metadata | `provenance-grounding` via receipt rehydration |

Expected initial result: **M2, M6, M7 likely survive** until their invariant tests are implemented (suite gap known — Enforcement status in PE_Invariant_Suite). That is the point: the kill matrix measures the suite, not the pipeline.

## Kill matrix (copy per run into `reports/YYYY-MM-DD-<label>.md`)

| Mutant | Applied cleanly? | Invariants red | Killed? | Surviving-mutant work item |
|--------|------------------|----------------|---------|----------------------------|
| M1 | | | | |
| ... | | | | |

**Kill rate per invariant** (append): for each invariant, count of mutants it killed / mutants targeting it. Invariant strength as measurement, not aesthetics.

## Reports

| Date | Report | Model/agent | Kill rate | Survivors |
|------|--------|-------------|-----------|-----------|
| 2026-07-05 | [2026-07-05-baseline.md](reports/2026-07-05-baseline.md) | Composer 2.5 | M1/M3/M8 class killed; M2/M5/M6/M7 survived (expected) | M2, M5, M6, M7 |
| 2026-07-06 | [2026-07-06-property-tests.md](reports/2026-07-06-property-tests.md) | Composer | M2/M5/M6/M7 killed (property suite) | — |

Re-run after: new invariant tests, suite changes, model change (if drills are agent-applied). Each re-run should add ≥1 new mutation matching current failure sophistication — a static mutation list decays into a passed test.

## Work items from baselines

- **2026-07-05 — M5 adjudication (frontier; corrected after reading the baseline report):** M5 was `N/A` in v0 — no `glossary-acyclic` test exists, so "survived" means *untested*, not *evaded*. Design analysis for whoever implements it: `f_audit` fails **soft** (warnings recorded, payload still written — per PE_Invariant_Suite enforcement notes), so a future test that merely runs the pipeline would stay green even when the DFS detects the cycle. The test must assert `Audit_Status == Clean` / empty warnings on the golden fixture — the missing invariant is **audit-warnings-fail-the-suite**, candidate for PE_Invariant_Suite (user ratifies); feed to `/invariant-propose covenant_pipeline/phases/audit.py`.
- **M2 / M7 survivors:** implement `chunker-partition` tests (monotonicity; bbox-in-page).
- **M6 survivor:** implement `config-totality` test (missing required env var ⇒ named error, never a silent default).

## Rules

- One mutation at a time; always revert before the next.
- Never commit a mutation. Work on a scratch branch if paranoid: `git switch -c mutation-drill && ... && git switch - && git branch -D mutation-drill`.
- Drills run on the **golden fixture** and `--skip-llm` prefix wherever possible — deterministic, fast, free.
- v1 (scripted mutations, CI-schedulable) waits until this list has stabilized across two full runs — do not script an unstable list.
