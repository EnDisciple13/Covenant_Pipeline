<!-- MIRROR: auto-synced from notes/projects/covenant/platform-engineering/blueprints/PE_Property_Test_Specs.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_project_docs.py -->

---
id: projects-covenant-platform-engineering-blueprints-PE_Property_Test_Specs
type: blueprint
status: draft
dependencies:
  - projects/covenant/platform-engineering/PE_Invariant_Suite.md
  - math/platform-engineering/Math_Application_Pipeline.md
tags:
  - invariants
  - layer4
  - hypothesis
  - property-testing
invariants: []
inherited_invariants:
  - id: provenance-grounding
    from: projects/covenant/platform-engineering/PE_Invariant_Suite.md
    status: enforced
    enforced_by: "tests/invariants/test_provenance_grounding.py::test_provenance_grounding_detects_fabricated_span"
  - id: chunker-partition
    from: projects/covenant/platform-engineering/PE_Invariant_Suite.md
    status: enforced
    enforced_by: "tests/invariants/test_chunker_partition.py::test_partition_monotone_nonoverlap"
  - id: chunker-coverage-audit
    from: projects/covenant/platform-engineering/PE_Invariant_Suite.md
    status: enforced
    enforced_by: "tests/invariants/test_chunker_coverage_audit.py::test_chunker_coverage_audit_non_empty_extraction"
  - id: router-rule-dispatch
    from: projects/covenant/platform-engineering/PE_Invariant_Suite.md
    status: enforced
    enforced_by: "tests/invariants/test_router_rule_dispatch.py::test_single_dispatch_or_abstain"
  - id: glossary-acyclic
    from: projects/covenant/platform-engineering/PE_Invariant_Suite.md
    status: enforced
    enforced_by: "tests/invariants/test_glossary_acyclic.py::test_definition_graph_dag"
  - id: metamorphic-stability
    from: projects/covenant/platform-engineering/PE_Invariant_Suite.md
    status: enforced
    enforced_by: "tests/invariants/test_metamorphic_stability.py::test_reflow_prefix_invariant"
  - id: container-parity
    from: projects/covenant/platform-engineering/PE_Invariant_Suite.md
    status: enforced
    enforced_by: "tests/invariants/test_container_parity.py::test_container_parity_host_reproducible"
  - id: config-totality
    from: projects/covenant/platform-engineering/PE_Invariant_Suite.md
    status: enforced
    enforced_by: "tests/invariants/test_config_totality.py::test_missing_env_fails_fast"
  - id: phase-composition
    from: math/platform-engineering/Math_Application_Pipeline.md
    status: enforced
    enforced_by: "tests/invariants/test_phase_composition.py::test_phase_composition_associativity"
  - id: staging-parity
    from: math/platform-engineering/Math_Application_Pipeline.md
    status: enforced
    enforced_by: "tests/invariants/test_staging_parity.py::test_staging_parity_deterministic_prefix"
---
# PE Property Test Specs (Covenant Pipeline & Platform Layer)

> **Rule of Thumb:** Always derive property-test specifications strictly from formal mathematical invariants and domain boundaries without inspecting implementation internals.
>
> **Note on Schema Sequencing:** The `inherited_invariants:` frontmatter block presumes the chain-auditor plan's FM-015..FM-018 rules have landed in `scripts/validate_frontmatter.py`. Per plan instruction §IV.6, all rows are shipped as `status: planned` during initial Fable authorship and must not be stripped.
>
> **Theory & Mathematical Foundations:** Autoformalization of Layer 1 invariants from [PE_Invariant_Suite.md](../PE_Invariant_Suite.md) and categorical pipeline foundations from [Math_Application_Pipeline.md](../math/Math_Application_Pipeline.md) into universally quantified Hypothesis property tests. Governed by [Invariant_Authorship.md](../../../../Notes/meta/Invariant_Authorship.md) §VI.4 (progression to Hypothesis properties per module) and §VII.1 (test-writer non-circularity).

## I. Fable Autoformalization Strategy & Scope

> **Rule of Thumb:** Prioritize metamorphic properties first to maximize mutant kill rates across non-deterministic LLM pipeline stages without requiring ground-truth fixtures.

This blueprint establishes the Layer 2 implementation contract for upgrading the Covenant Pipeline's verification harness from static golden-fixture unit tests (Stage 0) to universally quantified property tests using Python's `hypothesis` library. 

### 1. Authorship Independence & Non-Circularity
To preserve the verification integrity required by `Invariant_Authorship.md` §VII.1, all specifications in this document are derived strictly from:
1. The formal invariant statements and Layer 0 audit notes in `PE_Invariant_Suite.md`.
2. The category-theoretic phase decompositions, Kleisli arrows, and fiber-product semantics in `Math_Application_Pipeline.md`.
3. Containerization functor laws in `Math_Containerization.md`.

**Hard Constraint:** No phase implementation internals (`phases/*.py`, `orchestrator.py`) were inspected during authorship. Test developers implementing this blueprint must code against the interface contracts and property definitions defined below without referencing internal algorithmic shortcuts.

### 2. Binding Layer 0 Resolutions
Per the K1 audit resolutions recorded in `PE_Invariant_Suite.md`, two domain boundaries are immutable and must not be strengthened by test implementations:
* **TOC-Driven Partial Coverage (`chunker-partition`, `chunker-coverage-audit`):** Partial coverage of Credit Agreement PDFs is confirmed design intent. The chunker is not required to tile 100% of the document pages. `chunker-partition` applies strictly within the declared covered domain. To defend against silent section omission (where the extraction engine exports empty sections without warning), `chunker-coverage-audit` enforces non-empty text extraction per skeleton section and performs an independent body scan for section headers. Discrepancies between the body scan and TOC skeleton must be recorded in `Document_Metadata.Warnings` (detect-and-report); they must **never** trigger a hard test failure.
* **Glossary Reference Closure (`glossary-acyclic`):** While definition graph acyclicity is a strict topological requirement (hard fail on cycles), reference closure remains **detect-and-report** (soft fail). Hard-failing on dangling references would break on legitimate legal cross-references to excluded appendices (e.g., "as defined in Exhibit B"). The property test must verify that the audit endomorphism $f_{\text{audit}}$ detects all dangling pointers, reports them, and correctly classifies them as excluded-domain (expected) versus in-domain (genuine defect) in metadata warnings.

### 3. Priority Ordering: Metamorphic First
Among the missing invariant tests, `metamorphic-stability` is prioritized first for implementation. Because metamorphic properties evaluate invariants across perturbation relations (e.g., whitespace reflows, page-break shifts) without requiring access to ground-truth answers, they provide the highest ratio of mutant kills per line of test code—particularly across the pipeline's deterministic prefix $P_{\text{det}} = f_{\text{glossary}} \circ f_{\text{route}} \circ f_{\text{chunk}}$.

---

## II. Missing Invariant Property Specifications

> **Rule of Thumb:** Implement universally quantified Hypothesis properties for all missing invariants to eradicate surviving mutants M2, M5, M6, and M7.

This section defines the P1–P7 contract for the five missing Covenant invariants plus Stage 2 of the chunker coverage audit.

### 1. Metamorphic Stability (`metamorphic-stability`)

> **Rule of Thumb:** Evaluate pipeline phase invariance against whitespace reflows and page-break shifts by asserting exact equality over the deterministic prefix before any LLM invocation.

| Field | Content |
| :--- | :--- |
| **P1. Property statement** | For any valid document input $X_{\text{pdf}}$ and any formatting perturbation $\pi \in \Pi_{\text{format}}$ (whitespace reflow, line wrapping, page-break shift), the deterministic prefix morphism $P_{\text{det}} : X_{\text{pdf}} \to X_{\text{glossary}}$ satisfies $P_{\text{det}}(\pi(X_{\text{pdf}})) = P_{\text{det}}(X_{\text{pdf}})$. For LLM stages modeled as Kleisli arrows $f : A \rightsquigarrow B$, stability holds modulo declared stochasticity at temperature 0. |
| **P2. Strategy design** | Composite Hypothesis strategy `st.text()` and synthetic document builders generating multi-section legal text. A transformation strategy generates perturbation pairs $(d, d')$ where $d'$ injects random line breaks, replaces spaces with multiple spaces/tabs, or shifts section boundaries across synthetic page breaks while preserving alphanumeric sequences. |
| **P3. Oracle** | **Metamorphic relation.** Execute $P_{\text{det}}$ (via `--skip-llm` CLI scoping) on both $d$ and $d'$. Assert exact equality of resulting chunk payloads, routing dispatch envelopes, and resolved glossary adjacency lists. |
| **P4. Edge cases pinned** | `@example` inputs with: (a) section headers split across line breaks; (b) definitions spanning page breaks; (c) excessive leading/trailing whitespace in EDGAR HTML-to-text conversions; (d) empty sections. |
| **P5. Stochasticity handling** | Strict architectural decoupling: enforce deterministic prefix $P_{\text{det}}$ first using `--skip-llm`. For stochastic extraction/validation stages ($f_{\text{extract}}, f_{\text{validate}}$), evaluate at temperature 0 and assert structural equality of JSON schemas and non-stochastic metadata fields. |
| **P6. Kill targets** | Eradicates cross-cutting resilience defects and surviving mutants **M2** (chunk boundary leakage) and **M7** (ordering/formatting dependency). |
| **P7. Test function name** | `tests/invariants/test_metamorphic_stability.py::test_reflow_prefix_invariant` |

### 2. Chunker Partition & Domain Conservation (`chunker-partition`)

> **Rule of Thumb:** Assert that extracted text blocks within the TOC-declared domain are strictly non-overlapping, monotonically ordered by page and position, and exactly conserve source characters.

| Field | Content |
| :--- | :--- |
| **P1. Property statement** | Let $\mathcal{D} \subseteq \mathcal{P} \times \mathcal{A}$ be the explicitly declared covered domain of a document. For any chunk set $C = f_{\text{chunk}}(X_{\text{pdf}})$, all chunks $c_i, c_j \in C$ within $\mathcal{D}$ are strictly non-overlapping ($\text{span}(c_i) \cap \text{span}(c_j) = \emptyset$ for $i \neq j$), monotonically ordered by page and character offset, have bounding boxes contained within physical page dimensions, and exactly conserve source text: $\bigcup_{c \in C} \text{text}(c) = \text{text}(X_{\text{pdf}})\rvert_{\mathcal{D}}$. |
| **P2. Strategy design** | Generate synthetic PDF spreads with randomized page counts ($N \in [1, 50]$), article/section hierarchies, and bounding box coordinates $(x_0, y_0, x_1, y_1)$ bounded by standard letter/A4 dimensions. Generate explicit TOC skeletons defining covered vs. excluded page ranges. |
| **P3. Oracle** | **Exact recomputation & structural assertion.** Sort chunks by start offset; assert $\text{end}_i \le \text{start}_{i+1}$ (non-overlap and monotonicity). Check bbox coordinate bounds against page size. Concatenate chunk text within $\mathcal{D}$ and assert character-for-character equality with source text over $\mathcal{D}$. |
| **P4. Edge cases pinned** | `@example` inputs featuring: (a) single-page documents; (b) chunks starting on page boundary $N$ and ending on $N+1$; (c) Unicode bullet points and non-breaking spaces; (d) out-of-order TOC declarations. |
| **P5. Stochasticity handling** | None required. $f_{\text{chunk}}$ is a strictly deterministic morphism over $\mathcal{A}$. |
| **P6. Kill targets** | Eradicates surviving mutants **M2** (boundary overlap/gap mutations) and **M7** (monotone ordering drop mutants). |
| **P7. Test function name** | `tests/invariants/test_chunker_partition.py::test_partition_monotone_nonoverlap` |

### 3. Chunker Coverage Audit Stage 2 (`chunker-coverage-audit`)

> **Rule of Thumb:** Reconcile independent body scans against the TOC skeleton without hard-failing on omissions, recording all structural discrepancies in document warning metadata.

| Field | Content |
| :--- | :--- |
| **P1. Property statement** | For every section $s$ declared in the TOC skeleton, extraction yields non-empty text ($\rvert\text{Raw\_Text}(s)\rvert > 0$). An independent body scan for section headers reconciles with the skeleton: any header found in body text but missing from TOC (or vice versa) is recorded in `Document_Metadata.Warnings`, and deliberately omitted sections appear in an exclusion manifest. |
| **P2. Strategy design** | Generate structured document bodies with randomized section headings (e.g., "Article 1", "Section 1.01") and corresponding TOC skeletons. Invert alignment randomly: generate skeletons missing body headers, bodies missing skeleton headers, and explicit exclusion lists. |
| **P3. Oracle** | **Reconciliation & soft-fail assertion.** Inspect `Raw_Text` length for all skeleton rows ($>0$). Inspect `Document_Metadata.Warnings`: assert that every synthetic mismatch between body scan and TOC skeleton is explicitly recorded as a warning discrepancy. Assert zero test exceptions thrown on mismatch (verifying soft-fail detect-and-report behavior). |
| **P4. Edge cases pinned** | `@example` inputs with: (a) skeleton headers formatted with Roman numerals vs. Arabic body headers; (b) section headers inside footnotes or tables; (c) 100% excluded document domains. |
| **P5. Stochasticity handling** | None required. Header regex scanning and skeleton reconciliation are deterministic. |
| **P6. Kill targets** | Eradicates silent omission bugs and surviving mutant **M2** (silent section drop without warning emission). |
| **P7. Test function name** | `tests/invariants/test_chunker_coverage_audit.py::test_chunker_coverage_audit_non_empty_extraction` |

### 4. Router Rule Dispatch (`router-rule-dispatch`)

> **Rule of Thumb:** Assert that each routing rule evaluates independently over document chunks via fiber products, dispatching exactly one envelope if and only if the surviving set contains a single element.

| Field | Content |
| :--- | :--- |
| **P1. Property statement** | Let $C$ be the set of document chunks and $\Sigma_{\text{rules}}$ be the routing rules. For each rule $r \in \Sigma_{\text{rules}}$ with characteristic functions $\chi_{\text{zone}}^r, \chi_{\text{trigger}}^r, \chi_{\text{body}}^r, \chi_{\text{density}}^r$, let $S_r = \{c \in C \mid \prod \chi_i^r(c) = 1\}$. The router morphism $f_{\text{route}}$ dispatches exactly one extraction envelope for rule $r$ if and only if $\rvert S_r\rvert = 1$, else performs deterministic abstention. Rule evaluations are independent across chunks (fiber product over $C$). |
| **P2. Strategy design** | Generate random lists of chunk objects ($N \in [1, 30]$) with randomized textual attributes and metadata zones. Generate rule sets $\Sigma_{\text{rules}}$ with randomized boolean mask criteria such that for specific rules $\rvert S_r\rvert = 0$, $\rvert S_r\rvert = 1$, and $\rvert S_r\rvert > 1$. |
| **P3. Oracle** | **Exact recomputation.** Calculate $S_r$ independently via list comprehension over characteristic masks. Assert that the output dispatch list contains an envelope for rule $r$ if and only if $\rvert S_r\rvert = 1$. When $\rvert S_r\rvert \neq 1$, assert exact absence of envelope (deterministic abstention). Assert that modifying rule $r_1$ masks has zero effect on dispatch of rule $r_2$. |
| **P4. Edge cases pinned** | `@example` inputs with: (a) empty chunk list $C = \emptyset$; (b) identical chunks satisfying multiple rules simultaneously; (c) rules where all chunks match ($\rvert S_r\rvert = \rvert C\rvert$); (d) zero rules defined. |
| **P5. Stochasticity handling** | None required. Characteristic function filtering via boolean masks is strictly deterministic. |
| **P6. Kill targets** | Eradicates routing logic faults and surviving mutant **M2** (mask conjunction corruption / Tier 1 abstention drop). |
| **P7. Test function name** | `tests/invariants/test_router_rule_dispatch.py::test_single_dispatch_or_abstain` |

### 5. Glossary Acyclicity & Reference Closure (`glossary-acyclic`)

> **Rule of Thumb:** Enforce definition graph acyclicity via depth-first search while softly classifying unresolved reference tags as expected excluded-domain occurrences or in-domain defects.

| Field | Content |
| :--- | :--- |
| **P1. Property statement** | Let $G_{\text{ref}} = (V, E)$ be the term definition dependency graph where $(u, v) \in E$ iff term $u$'s definition text references term $v$. $G_{\text{ref}}$ is a Directed Acyclic Graph (DAG), and multi-hop resolution operator $R : \mathcal{T} \to \mathcal{T}$ terminates within declared depth $K$. For all reference tags `[$REF: t]` in compiled JSON, the audit endomorphism $f_{\text{audit}}$ detects unresolved pointers ($t \notin V$), reports them, and classifies them as excluded-domain (expected) or in-domain (defect) without raising an exception. |
| **P2. Strategy design** | Generate directed graphs using `hypothesis.strategies.recursive` and lists of edges $(u, v)$ over term alphabets. Explicitly generate three classes of graphs: (1) strict trees/DAGs; (2) graphs containing directed cycles of length $L \in [1, 5]$ (e.g., $A \to B \to A$); (3) DAGs containing dangling pointers `[$REF: Unknown]`, paired with domain exclusion manifests. |
| **P3. Oracle** | **Structural assertion & exception classification.** For DAG inputs, assert cycle detection returns False and resolution operator $R$ terminates in $\le K$ hops. For cyclic inputs, assert DFS cycle detector flags the exact cycle and records $W_{\text{cycle}}$ warning. For dangling pointer inputs, assert zero exception is raised (soft fail), and verify $W_{\text{dangle}}$ warning metadata correctly classifies the dangle based on exclusion manifest presence. |
| **P4. Edge cases pinned** | `@example` inputs with: (a) self-referential terms ($A \to A$); (b) mutual recursion across 5+ hops; (c) terms with identical substrings where prefix-free length sorting is required; (d) empty glossary $V = \emptyset$. |
| **P5. Stochasticity handling** | None required. Graph traversal and reference resolution are deterministic tree-map endofunctors. |
| **P6. Kill targets** | Eradicates definition infinite loops and surviving mutant **M5** (cycle detection bypass and resolution ordering faults). |
| **P7. Test function name** | `tests/invariants/test_glossary_acyclic.py::test_definition_graph_dag` |

### 6. Config Totality & Fail-Fast (`config-totality`)

> **Rule of Thumb:** Assert that container initialization fails fast with a named error exception upon encountering a missing required environment variable rather than falling back to silent defaults.

| Field | Content |
| :--- | :--- |
| **P1. Property statement** | Let $\mathcal{E}_{\text{req}}$ be the set of mandatory environment variables required by the container runtime. For any environment state $\Gamma$ where there exists an key $k \in \mathcal{E}_{\text{req}}$ such that $k \notin \Gamma$ or $\Gamma[k] = \text{null}$, pipeline initialization aborts immediately with a named configuration exception. It never initiates execution or falls back to silent default values. |
| **P2. Strategy design** | Generate dictionaries representing environment variables. Use `st.sampled_from` over mandatory configuration keys (e.g., API keys, model names, database paths) and generate test states where selected keys are deleted, set to empty strings `""`, or assigned `None`. |
| **P3. Oracle** | **Exception assertion.** Invoke configuration loader/pipeline startup inside `pytest.raises(ConfigurationError)`. Assert that the caught exception message explicitly names the missing key $k$. Assert that no filesystem paths or side-effect artifacts are created. |
| **P4. Edge cases pinned** | `@example` inputs with: (a) all mandatory keys missing simultaneously; (b) whitespace-only string values `"   "`; (c) case-sensitivity mismatches in environment key names. |
| **P5. Stochasticity handling** | None required. Configuration loading is deterministic. |
| **P6. Kill targets** | Eradicates silent initialization drift and surviving mutant **M6** (silent default fallback and missing env check bypass). |
| **P7. Test function name** | `tests/invariants/test_config_totality.py::test_missing_env_fails_fast` |

---

## III. Inherited Invariant Upgrade Specifications

> **Rule of Thumb:** Upgrade existing Stage 0 unit tests and mathematical pipeline theorems to universally quantified Hypothesis properties across randomized document structures and environments.

This section defines the property-test upgrade specifications for the four remaining invariants inherited from `PE_Invariant_Suite.md` and `Math_Application_Pipeline.md`.

### 7. Provenance Grounding (`provenance-grounding`)

> **Rule of Thumb:** Verify that every extracted covenant field cites a character span verifiably present as an exact substring within the referenced source chunk.

| Field | Content |
| :--- | :--- |
| **P1. Property statement** | For every extracted covenant node $y \in Y$ produced by $f_{\text{extract}}$, every field carrying a provenance receipt $\rho = (\text{Article}, \text{Section}, \text{Span})$ satisfies exact substring inclusion: the cited string span exists verbatim within the source chunk text identified by $\rho$. |
| **P2. Strategy design** | Generate synthetic text chunks and simulated Pydantic extraction models containing textual quotes and offset indices. Inject synthetic mutations that alter 1–3 characters in the cited quote or shift offset indices by $\pm 1$. |
| **P3. Oracle** | **Exact substring verification.** For valid extractions, assert `quote in chunk_text[start:end]`. For mutated extractions, assert validation critic $f_{\text{validate}}$ rejects the payload or flags a provenance grounding failure in `Validation_Audit`. |
| **P4. Edge cases pinned** | `@example` inputs with: (a) quotes at exact start/end of chunk; (b) quotes containing normalized whitespace vs. raw linebreak whitespace; (c) empty quote strings. |
| **P5. Stochasticity handling** | When evaluating LLM actor output, apply critic morphism $f_{\text{validate}}$ as an objective post-condition check at temperature 0. |
| **P6. Kill targets** | Eradicates hallucinated span acceptance and M1/M3 class regression. |
| **P7. Test function name** | `tests/invariants/test_provenance_grounding.py::test_provenance_grounding_detects_fabricated_span` |

### 8. Container Parity (`container-parity`)

> **Rule of Thumb:** Assert that pipeline evaluation on golden fixtures inside containerized environments produces identical output artifacts to native host evaluation across randomized configurations.

| Field | Content |
| :--- | :--- |
| **P1. Property statement** | Let $eval_{D,Y}(j_P, D)$ be containerized evaluation of pipeline program $P$ and $P_{\text{host}}(X_{\text{in}})$ be native host evaluation. For any golden fixture input $X_{\text{fixture}}$ and randomized valid runtime configuration $\sigma$, $eval(j_P, X_{\text{fixture}}) \equiv P_{\text{host}}(X_{\text{fixture}})$ bitwise across all output JSON payloads and CSV reports. |
| **P2. Strategy design** | Sample across valid environment configurations (e.g., thread counts, temporary directory paths, optional logging flags) while holding the input fixture $X_{\text{fixture}}$ constant. |
| **P3. Oracle** | **Round-trip / parity assertion.** Execute pipeline in host subprocess and Docker container subprocess. Compute SHA-256 hashes of `final_compiled_payload_audited.json` and `final_extracted_covenants.csv`; assert hash identity. |
| **P4. Edge cases pinned** | `@example` inputs testing: (a) Windows vs. Linux line endings (`\r\n` vs `\n`); (b) file permission boundaries; (c) mounted volume path mappings. |
| **P5. Stochasticity handling** | Restrict parity verification to deterministic prefix $P_{\text{det}}$ or execute full pipeline using recorded VCR/cassette LLM responses to eliminate network stochasticity. |
| **P6. Kill targets** | Eradicates environment drift, path resolution bugs, and dependency skew. |
| **P7. Test function name** | `tests/invariants/test_container_parity.py::test_container_parity_host_reproducible` |

### 9. Phase Composition Associativity (`phase-composition`)

> **Rule of Thumb:** Assert that left-to-right composition of deterministic pipeline phase morphisms is associative and type-compatible across randomized artifact payloads.

| Field | Content |
| :--- | :--- |
| **P1. Property statement** | For any deterministic phase morphisms $f_1, f_2, f_3$ in category $\mathcal{A}$ and valid initial artifact $X$, composition is associative: $((f_3 \circ f_2) \circ f_1)(X) = (f_3 \circ (f_2 \circ f_1))(X)$, and the codomain type of $f_n$ strictly matches the domain type of $f_{n+1}$. |
| **P2. Strategy design** | Generate randomized intermediate artifact objects ($X_{\text{spatial}}, X_{\text{payload}}, X_{\text{dispatch}}$) populated with synthetic covenant data conforming to Pydantic schemas. |
| **P3. Oracle** | **Exact identity & type assertion.** Execute step-by-step composition versus grouped execution. Assert `type(output_step) == expected_schema` at each boundary and assert deep dictionary equality between grouped composition structures. |
| **P4. Edge cases pinned** | `@example` inputs with: (a) empty artifact collections; (b) artifacts with missing optional metadata fields; (c) maximum boundary payload sizes. |
| **P5. Stochasticity handling** | Restrict associativity evaluation strictly to deterministic phase morphisms ($f_{\text{chunk}}, f_{\text{route}}, f_{\text{glossary}}, f_{\text{compile}}, f_{\text{audit}}$). |
| **P6. Kill targets** | Eradicates inter-phase contract breakage and data dropping across pipeline wiring. |
| **P7. Test function name** | `tests/invariants/test_phase_composition.py::test_phase_composition_associativity` |

### 10. Staging Parity (`staging-parity`)

> **Rule of Thumb:** Verify that executing pipeline phases individually via command-line invocations over the deterministic prefix yields byte-identical artifacts to a single composed orchestrator run.

| Field | Content |
| :--- | :--- |
| **P1. Property statement** | For any valid document $X_{\text{pdf}}$, sequential execution of CLI stage commands (`agy chunk`, `agy route`, `agy glossary`) producing intermediate filesystem artifacts yields a final state byte-identical to executing the composed orchestrator in a single run: `agy run --skip-llm`. |
| **P2. Strategy design** | Generate random synthetic PDF documents and routing configuration files across diverse temporary workspace directories. |
| **P3. Oracle** | **Byte-identity assertion.** Run staged CLI sequence in workspace A; run composed orchestrator in workspace B. Diff all resulting files in `output_dir/` and assert zero binary or textual discrepancies. |
| **P4. Edge cases pinned** | `@example` inputs with: (a) custom `--output-dir` flag paths; (b) overwriting existing workspace files from a prior run; (c) relative versus absolute file paths. |
| **P5. Stochasticity handling** | Enforce `--skip-llm` flag across both execution modes to evaluate purely deterministic transformations. |
| **P6. Kill targets** | Eradicates hidden in-memory state dependencies between phases and filesystem serialization flaws. |
| **P7. Test function name** | `tests/invariants/test_staging_parity.py::test_staging_parity_deterministic_prefix` |

---

## IV. Implementation & Verification Contract (Composer Hand-Off)

> **Rule of Thumb:** Implement test suites strictly from this blueprint without referencing implementation internals, confirming success only when mutation drill survivors M2, M5, M6, and M7 are killed.

### 1. Execution Rules for Composer
1. **Model Boundary Enforcement:** Composer must implement the test functions named in `inherited_invariants:` inside `covenant_pipeline/tests/invariants/` using **only** this blueprint note and the repository's existing test scaffolding. Composer must not read application implementation code in `phases/` or `orchestrator.py` during test authoring.
2. **One Invariant per Commit:** Implement each property test suite in an isolated commit, verifying that pytest executes cleanly and Hypothesis runs without strategy health-check failures.
3. **No Ad-Hoc Patching:** If a newly implemented property test fails against the current codebase, report the failure as an revealed defect or spec gap. Do not ad-hoc patch the pipeline implementation or weaken the property test to force a green CI build.

### 2. Exit Condition & Mutation Drill Verification
Once all 10 property tests are implemented:
1. Execute the mutation testing harness across `covenant_pipeline/`.
2. Compare the resulting kill matrix against the baseline recorded in `tests/mutation/reports/2026-07-05-baseline.md`.
3. **Mandatory Exit Condition:** Surviving mutants **M2**, **M5**, **M6**, and **M7** must be killed. Any mutant in these classes that survives represents an incomplete strategy domain or weak oracle and must be remediated in the test specification.
4. Upon confirmation of mutant death, update `PE_Property_Test_Specs.md` frontmatter to flip all `inherited_invariants:` rows from `status: planned` to `status: enforced`, and sync enforcement status blocks across project documentation.
