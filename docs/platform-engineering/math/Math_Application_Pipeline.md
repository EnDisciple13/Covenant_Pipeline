<!-- MIRROR: auto-synced from notes/projects/covenant/Math_Application_Pipeline.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_pe_docs.py -->

# Architectural Formalization: The Category-Theoretic Foundations of the Covenant Pipeline

This document formalizes the **application layer** of the Credit Agreement pipeline — the program morphism $P$ that [Math_Containerization.md](../../../../notes/math/Math_Containerization.md) treats as an abstract arrow $P : D \to Y$. Where containerization internalizes $P$ into the exponential object $Y^D$, this document decomposes $P$ itself into composed phase-morphisms over a category of pipeline artifacts.

**Companion:** [Reading the Pipeline Code.md](../learning/Reading%20the%20Pipeline%20Code.md) — line-by-line code walkthrough using this notation.

**Notation:** Reuses $D$, $Y$, $P$, $eval$, $\circ$ from the containerization notes. Introduces phase morphisms $f_*$, Kleisli arrows $\rightsquigarrow$, and the reference graph $G_{\text{ref}}$.

---

## 1. The Program Morphism and the Codomain Object $Y$

Let $\mathcal{C}$ be a Cartesian Closed Category as in the containerization formalization.

- **The Dependency Object ($D$):** Runtime requirements (Python, PyMuPDF, Pandas, Gemini SDK, Pydantic). In containerized execution, $D$ is baked into $Y^D$; in native execution, $D$ is projected from $\Gamma_{\text{host}}$.

- **The Codomain Object ($Y$):** The validated output state — specifically `final_compiled_payload_audited.json`: a product of structured covenant extractions, a master glossary, document metadata, and per-covenant `Validation_Audit` records.

- **The Program Morphism ($P$):** The full pipeline program:

$$P : D \times X_{\text{in}} \to Y$$

where $X_{\text{in}}$ is the input artifact (a credit agreement PDF plus routing configuration). For fixed inputs, write $P_\sigma : D \to Y$ where $\sigma$ encodes paths and config.

The global element selecting this release inside $Y^D$ is still $j_P : 1 \to Y^D$. Container evaluation $eval_{D,Y}(j_P, D) = P_\sigma(X_{\text{in}})$ applies $P$ to produce $Y$.

---

## 2. The Category of Pipeline Artifacts

Define a category $\mathcal{A}$ whose objects are **artifact types** at each pipeline stage:

$$\text{Ob}(\mathcal{A}) = \{ X_{\text{pdf}}, X_{\text{spatial}}, X_{\text{payload}}, X_{\text{dispatch}}, X_{\text{nodes}}, X_{\text{glossary}}, X_{\text{compiled}}, Y \}$$

Morphisms in $\mathcal{A}$ are **deterministic transformations** between artifact types. Each phase implements one or more such morphisms (possibly after currying over $D$).

**Medallion layering** (chunker output):

$$X_{\text{spatial}} \twoheadrightarrow X_{\text{payload}}$$

Silver CSV (`final_extracted_covenants.csv`) projects to Gold CSV (`final_extracted_covenants_phase1_payload.csv`) by dropping unscrubbed columns — a forgetful projection $\pi_{\text{gold}} : X_{\text{spatial}} \to X_{\text{payload}}$.

**Shared addressing:** `PipelinePaths` in `covenant_pipeline/config.py` is a single namespace object assigning filenames to paths in `output_dir`. Formally, a functor $\Phi : \mathcal{A} \to \mathbf{Path}$ that maps each artifact type to a filesystem location.

---

## 3. Phase Morphisms and Composition

The orchestrator (`covenant_pipeline/orchestrator.py`) defines the **canonical composition order**:

$$P_{\text{full}} = f_{\text{validate}} \circ f_{\text{audit}} \circ f_{\text{compile}} \circ f_{\text{extract}} \circ f_{\text{glossary}} \circ f_{\text{route}} \circ f_{\text{chunk}}$$

| Morphism | Domain | Codomain | Deterministic? |
|----------|--------|----------|----------------|
| $f_{\text{chunk}}$ | $X_{\text{pdf}}$ | $X_{\text{payload}}$ | Yes |
| $f_{\text{route}}$ | $X_{\text{payload}} \times \Sigma_{\text{rules}}$ | $X_{\text{dispatch}}$ | Yes |
| $f_{\text{glossary}}$ | $X_{\text{payload}}$ | $X_{\text{glossary}}$ | Yes |
| $f_{\text{extract}}$ | $X_{\text{dispatch}}$ | $X_{\text{nodes}}$ | Stochastic |
| $f_{\text{compile}}$ | $X_{\text{nodes}} \times X_{\text{glossary}} \times X_{\text{payload}}$ | $X_{\text{compiled}}$ | Yes |
| $f_{\text{audit}}$ | $X_{\text{compiled}}$ | $X_{\text{compiled}}$ | Yes (endomorphism) |
| $f_{\text{validate}}$ | $X_{\text{compiled}} \times X_{\text{payload}}$ | $Y$ | Stochastic |

**Glossary ordering note:** Glossary runs before extract in code but does not feed extract at runtime. It parallelizes with routing from $X_{\text{payload}}$ and ensures $X_{\text{glossary}}$ exists before $f_{\text{compile}}$.

**Partial composition (--skip-llm):**

$$P_{\text{det}} = f_{\text{glossary}} \circ f_{\text{route}} \circ f_{\text{chunk}} : X_{\text{pdf}} \to X_{\text{glossary}}$$

The LLM suffix is omitted; codomain is $X_{\text{payload}}$ artifacts only (no audited JSON).

---

## 4. Chunking as Spatial Coordinatization

Let $\mathcal{P}$ be the set of printed page numbers and $\mathcal{A}$ the set of absolute PDF page indices.

The chunker constructs a partial map:

$$\phi : \mathcal{P} \rightharpoonup \mathcal{A} \times \mathcal{A}$$

(printed page $\to$ absolute start/end) via `build_page_spread_map`, then refines section boundaries via TOC skeleton + window search.

**Normalization morphism** $\eta : \text{String} \to \text{String}$:

$$\eta(s) = \text{lower}(\text{remove\_whitespace}(s))$$

implemented as `compress_string` — makes section header matching invariant under EDGAR whitespace artifacts.

**Receipt functor:** Each chunk row carries metadata $(\text{Article}, \text{Section}, \text{Pages})$ that propagates as an immutable **provenance label** $\rho$ through all downstream stages. Extraction envelopes and validation rehydration both key on $\rho$.

---

## 5. Routing as Characteristic-Function Filtering

Let $C = \{c_1, \ldots, c_n\}$ be the set of document chunks (rows of $X_{\text{payload}}$).

For each routing rule $r \in \Sigma_{\text{rules}}$ (from `config/covenant_config.json`), define four **characteristic functions** on $C$:

$$\chi_{\text{zone}}^r, \chi_{\text{trigger}}^r, \chi_{\text{body}}^r, \chi_{\text{density}}^r : C \to \{0, 1\}$$

The **surviving set** for rule $r$:

$$S_r = \{ c \in C \mid \chi_{\text{zone}}^r(c) \cdot \chi_{\text{trigger}}^r(c) \cdot \chi_{\text{body}}^r(c) \cdot \chi_{\text{density}}^r(c) = 1 \}$$

**Tier 1 dispatch condition:** $|S_r| = 1$. Then $f_{\text{route}}$ selects the unique element and wraps it in an extraction envelope. If $|S_r| \neq 1$, no envelope is emitted (Tier 2 cascade — not implemented).

**Independent rule evaluation:** Rules are evaluated in a loop; one chunk $c$ may appear in $S_r$ and $S_{r'}$ for distinct rules — **fiber product** over chunk indices, not a partition of $C$.

---

## 6. The Glossary as a Reference Graph

Let $G_{\text{ref}} = (V, E)$ where:

- $V$ = set of defined terms extracted from Article 1
- $(u, v) \in E$ iff term $u$'s definition text contains term $v$ as a word-boundary match

**Construction:** Terms are sorted by length descending before edge detection — a **prefix-free resolution order** preventing shorter terms from shadowing longer composite terms during substring matching.

$G_{\text{ref}}$ is stored as adjacency lists (`nested_references`) in `resolved_definitions.json`. This graph is the domain for audit cycle detection (Section 8).

---

## 7. Kleisli Morphisms for LLM Stages

LLM calls are not pure morphisms $\mathcal{A}(X, Y)$ — they are **stochastic** and may fail. Model this with a monad $T$ on $\mathcal{A}$ (e.g., $T(X) = X \times \mathbb{P}(\text{error})$ or a probability distribution over outputs).

A **Kleisli arrow** from $A$ to $B$:

$$f : A \rightsquigarrow B \quad \Leftrightarrow \quad f : A \to T(B)$$

**Extraction** $f_{\text{extract}} : X_{\text{dispatch}} \rightsquigarrow X_{\text{nodes}}$:

- Input: envelope with `Payload_Text`, `Agent`, `Definition_Guardrail`
- Output: Pydantic-validated `Extracted_Data` or skip on failure
- Schema constraint: $\text{im}(f) \subseteq S_{\text{agent}}$ where $S_{\text{agent}}$ is the subobject carved out by `SCHEMA_ROUTER[agent]`

**Temperature $= 0$:** Collapses the output distribution toward a point mass (greedy decoding) — approximating determinism while remaining Kleisli.

**Reference tags** `[$REF: Term]` are **free variables** in the extracted JSON — placeholders for terms not resolved until $f_{\text{compile}}$.

---

## 8. Compilation as Fixed-Point Reference Resolution

Let $\mathcal{T}$ be the set of term names. The compiler maintains a glossary map $G : \mathcal{T} \to \text{Definition}$ that **grows monotonically** via dynamic TOC injection.

For each unresolved reference $\tau \in \mathcal{T}$, define a resolution operator:

$$R : \mathcal{T} \to \mathcal{T}$$

with five-hop fallback chain (exact glossary $\to$ exact TOC $\to$ fuzzy TOC $\to$ plural strip $\to$ fuzzy glossary $\to$ identity on failure).

**Traverse-and-mutate** is an **endofunctor** on the JSON tree: recursively maps over all string leaves, applying $R$ to each `[$REF: $\cdot$]` occurrence.

**Fixed-point intuition:** If references form a DAG after resolution, repeated application of $R$ on all leaves terminates. Cycles in $G_{\text{ref}}$ are detected later by $f_{\text{audit}}$, not by the compiler.

---

## 9. Audit as Graph Integrity Endomorphism

$f_{\text{audit}} : X_{\text{compiled}} \to X_{\text{compiled}}$ is an **endomorphism** that annotates metadata without changing extracted covenant values.

Three predicates on the compiled payload:

1. **Acyclicity:** $G_{\text{ref}}$ has no directed cycles (DFS with path memoization)
2. **Pointer closure:** Every `[$REF: t]` in covenant JSON satisfies $t \in \text{keys}(G)$
3. **Type safety:** Keys containing `"limit"` map to $\mathbb{R}$ (int or float)

$$f_{\text{audit}}(x) = x' \text{ where } x'.\text{Document\_Metadata.Warnings} = (W_{\text{cycle}}, W_{\text{dangle}}, W_{\text{type}})$$

Fails **soft:** warnings are recorded; payload is still written.

---

## 10. Validation as the Critic Morphism (Actor-Critic)

The **actor** is $f_{\text{extract}}$ — generates structured JSON from source text.

The **critic** is $f_{\text{validate}}$ — a second Kleisli arrow:

$$f_{\text{validate}} : X_{\text{compiled}} \times X_{\text{payload}} \rightsquigarrow Y$$

**Rehydration** builds a join morphism:

$$h : \text{Receipt} \to \text{Raw\_Text}$$

from CSV metadata, enabling the critic to compare actor output against original source.

**Non-destructive append:** Critic output is written to `Validation_Audit` on each covenant node; `Extracted_Data` is not overwritten. Formally, a **product projection**:

$$\pi_{\text{data}} : Y \to X_{\text{compiled}}$$

preserves actor output; the critic fiber $\text{Validation\_Audit}$ is appended.

**Pullback diagram (informal):**

```
    Source_Text ──────► Extracted_Data  (actor)
         │                    │
         │                    │ π_data
         ▼                    ▼
    Validation_Audit ◄── compare ──► Y
                    (critic)
```

---

## 11. CLI as Evaluation Interface

The CLI (`covenant_pipeline/cli.py`) exposes **partial evaluations** of $P$:

| Command | Morphism evaluated |
|---------|-------------------|
| `run` | $P_{\text{full}}$ or $P_{\text{det}}$ |
| `chunk` | $f_{\text{chunk}}$ |
| `route` | $f_{\text{route}}$ |
| `extract` | $f_{\text{extract}}$ |
| `glossary` | $f_{\text{glossary}}$ |
| `compile` | $f_{\text{compile}}$ |
| `audit` | $f_{\text{audit}}$ |
| `validate` | $f_{\text{validate}}$ |

`run_stage(name, paths)` selects a single morphism from the composition chain — useful for debugging intermediate artifacts.

---

## 12. Structural Mapping Table

| **Concept** | **Mathematical object** | **Code realization** |
|-------------|-------------------------|----------------------|
| Program morphism $P$ | $P : D \times X_{\text{in}} \to Y$ | `run_full_pipeline()` |
| Phase composition | $f_n \circ \cdots \circ f_1$ | `orchestrator.py` stage sequence |
| Artifact namespace | Functor $\Phi : \mathcal{A} \to \mathbf{Path}$ | `PipelinePaths` |
| Characteristic filter | $\chi : C \to \{0,1\}$ | Pandas boolean masks in `router.py` |
| Reference graph | $G_{\text{ref}} = (V,E)$ | `nested_references` in glossary JSON |
| Kleisli arrow | $A \rightsquigarrow B$ | `extraction.py`, `validation.py` |
| Schema subobject | $S_{\text{agent}} \subset Y$ | Pydantic models in `SCHEMA_ROUTER` |
| Resolution operator | $R : \mathcal{T} \to \mathcal{T}$ | `_resolve_term()` five-hop chain |
| Audit endomorphism | $X \to X$ | `run_database_audit()` in-place update |
| Actor-critic | Pullback over source + extraction | `AUDITOR_SYSTEM_PROMPT` validation |
| Partial eval | $P$ restricted to prefix | `--skip-llm` |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [Reading the Pipeline Code.md](../learning/Reading%20the%20Pipeline%20Code.md) | Line-by-line application code walkthrough |
| [Math_Containerization.md](../../../../notes/math/Math_Containerization.md) | $Y^D$, $eval$, internalization |
| [Math_Notes_Platform_Engineer.md](../../../../notes/math/Math_Notes_Platform_Engineer.md) | Broader platform math (IaC, CI/CD) |
| [Reading the Docker Code.md](../learning/Reading%20the%20Docker%20Code.md) | Infrastructure layer walkthrough |
| [PROJECT_DOCUMENTATION.md](../../../PROJECT_DOCUMENTATION.md) | Operational architecture reference |
