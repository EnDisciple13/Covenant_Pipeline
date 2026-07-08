<!-- MIRROR: auto-synced from notes/projects/covenant/Covenant_Problem_and_Motivation.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_project_docs.py -->

---
id: projects-covenant-Covenant_Problem_and_Motivation
type: project_strategy
status: draft
dependencies:
  - projects/Problem_Matrix.md
  - projects/covenant/platform-engineering/PE_Roadmap_M1.md
  - projects/covenant/platform-engineering/PE_Roadmap_M2.md
tags: [covenant, rag, neuro-symbolic, problem-motivation, headroom]
invariants: []
---
# Covenant Extraction Pipeline: Domain Problem & Neuro-Symbolic Architecture (`M0`)

> **Rule of Thumb:** Ground every extraction pipeline in the concrete failure modes of the underlying domain before defining its infrastructure requirements.

This document serves as the canonical `Milestone 0` (`M0`) problem specification and architectural motivation for the Covenant Extraction Pipeline (`covenant_pipeline`). It defines the exact structural limitations of standard Large Language Model (LLM) approaches over complex financial contracts, details our neuro-symbolic extraction methodology, and establishes formal bridges to downstream financial headroom verification (`Feynman Problem #1`) and enterprise platform engineering (`Feynman Problem #2`).

**Scope relative to the Problem Matrix:** `Feynman Problem #3` is stated domain-generically — a copilot over regulated unstructured data (credit agreements, CRM, ledgers), including enterprise-only concerns (ACL trimming, entity resolution, freshness). This pipeline is the **credit-agreement instance** of that problem; the enterprise-only concerns remain open in the matrix row and are not addressed here.

---

## I. The Domain Problem: Why Credit Agreements Break Standard RAG (`Feynman Problem #3`)

> **Rule of Thumb:** Treat unstructured financial and legal contracts as zero-tolerance formal systems where probabilistic guessing is unacceptable.

Standard Retrieval-Augmented Generation (RAG) and unconstrained LLM prompting fail catastrophically when applied to corporate credit agreements (e.g., Syndicated Term Loans, Revolving Credit Facilities). These failures stem from two structural properties of legal financial documents:

### 1. Context Fragmentation & Cross-Reference Dependency
In a credit agreement, a financial covenant is almost never defined in a single localized paragraph. For example, Section 7.11 (`Financial Covenants`) may require the borrower to maintain a `Consolidated Leverage Ratio` of no greater than $4.50:1.00$. However, calculating or even understanding this ratio requires resolving nested definitions scattered across hundreds of pages:
- `Consolidated Leverage Ratio` depends on `Consolidated Total Debt` and `Consolidated EBITDA`, defined in Article I (`Definitions`).
- `Consolidated EBITDA` includes dozens of highly negotiated add-backs and carve-outs (e.g., non-recurring restructuring charges capped at $15\%$ of EBITDA over any $12$-month period).
- `Permitted Indebtedness` and `Restricted Payments` in Article VI (`Negative Covenants`) modify what debt can be incurred or how cash can be distributed based on pro forma compliance certificates in Article V (`Affirmative Covenants`).

Standard chunking and vector similarity search retrieve disjoint paragraphs, severing these critical legal dependencies and feeding incomplete definitions to the model.

### 2. Zero-Tolerance Financial Headroom
In corporate banking and treasury operations, covenant compliance is binary: a borrower either complies with the contract or triggers an Event of Default, potentially accelerating debt repayment and risking bankruptcy. Probabilistic approximations or hallucinated carve-outs (e.g., extracting a $4.55\times$ leverage threshold instead of $4.50\times$) create unacceptable legal, regulatory, and financial exposure. Standard LLMs lack internal deterministic mathematical verification to guarantee that extracted numerical constraints and dates are structurally valid.

---

## II. Neuro-Symbolic Extraction Architecture (The `M0` Solution)

> **Rule of Thumb:** Enforce strict typed contracts before model invocation and deterministic mathematical gates after extraction.

To solve the credit-agreement instance of `Feynman Problem #3` (verbatim row: *"How do you make a copilot over regulated unstructured data (credit agreements, CRM, ledgers) reliable — typed contracts before the model, deterministic gates after — including enterprise-only concerns (ACL trimming, entity resolution, freshness) with no Notes counterpart?"*), the Covenant Extraction Pipeline rejects pure probabilistic text generation in favor of a **neuro-symbolic architecture**:

### 1. Pre-Model Schema Enforcement (`Pydantic` / JSON Schema)
Rather than asking the LLM to return free-form summaries of covenants, the pipeline constrains the generative model using rigid `Pydantic` type contracts (`application/Pipeline_Invariants.md`). The model acts strictly as a semantic parser mapping unstructured text into formal domain objects (`CovenantDefinition`, `FinancialMetricCarveout`, `TestingPeriod`, `ThresholdStepdown`). If the model output fails schema validation, the execution instantly rejects the payload before it enters downstream data stores.

### 2. Deterministic Post-Extraction Validation Gates
Once the semantic layer extracts the candidate data structures, deterministic Python verification gates take over:
- **Mathematical Integrity:** If a covenant defines a multi-tier threshold stepdown schedule, deterministic validators check chronological order and numerical bounds.
- **Cross-Reference Completeness:** If an extracted covenant references a defined term not present in the extraction symbol table, the system flags an incomplete extraction graph rather than guessing the definition.
- **Human-in-the-Loop (`[Human]`) Routing:** Extractions that fail deterministic validation gates do not propagate silently; they are flagged with exact failure traces and routed to domain specialists for targeted triage and ratification.

---

## III. Bridge to Downstream Financial Headroom (`Feynman Problem #1`)

> **Rule of Thumb:** Couple extracted covenant boundaries directly to deterministic supply-chain cash flow trajectories to forecast compliance before capital deployment.

Extracting a covenant is not an end in itself; it provides the formal boundary conditions required for enterprise decision-making (`Feynman Problem #1`: *"Given a proposed supply-chain action like an MRP safety-stock increase triggering purchase orders, how do we deterministically forecast a borrower's covenant headroom at the next testing date?"*).

### The Synergy Between `projects/covenant/` and `projects/mrp/`
1. **The Cash-Flow Trajectory (`projects/mrp/`):** When an Enterprise Resource Planning (ERP) or Material Requirements Planning (MRP) engine proposes an inventory purchase order (`inbox/_processed/2026-07-07-tcb-embedded-treasury-erp-and-mrp-supply-planning.md`), that capital outflow directly reduces cash reserves and affects working capital and `Consolidated EBITDA` forecasts.
2. **The Invariant Upper Bound (`projects/covenant/`):** Our `M0` extraction pipeline supplies the exact, verified numerical thresholds (`Leverage Ratio $\le 4.50\times$`, `Minimum Interest Coverage $\ge 2.50\times$`) and testing dates (`Fiscal Quarter End`).
3. **Deterministic Headroom Verification:** By evaluating the `projects/mrp/` cash-flow trajectory against the `projects/covenant/` extracted invariants within a deterministic checker, the enterprise can verify whether a proposed supply-chain action preserves sufficient covenant headroom or risks breaching credit terms *before* issuing the purchase order.

---

## IV. Bridge to Platform Engineering (`M1` & `M2`, `Feynman Problem #2`)

> **Rule of Thumb:** Host zero-tolerance neuro-symbolic pipelines on immutable containerized runtimes and secretless enterprise developer platforms.

A reliable neuro-symbolic pipeline requires a rigorous, verifiable execution substrate. The `M0` application strategy cleanly decouples from—yet fundamentally relies upon—our two platform engineering milestones:

### 1. Milestone 1 (`M1`): Localized Containerization & CI/CD
Because neuro-symbolic extraction depends on exact Python dependency trees (`Pydantic`, document parsing engines, OCR drivers), `M1` containerization (`Docker_Documentation.md`, `platform-engineering/PE_Roadmap_M1.md`) guarantees that the extraction pipeline executes identically across local developer laptops, automated CI/CD validation workflows (`GitHub Actions`), and cloud containers. All `M1` container specifications (`Dockerfile`, `docker-compose.yml`) live directly inside the `covenant_pipeline` repository alongside the application source code.

### 2. Milestone 2 (`M2`): Universal Internal Developer Platform (`IDP`)
In a regulated enterprise cloud environment (`Feynman Problem #2`: *"How does a post-migration regulated bank govern its cloud platform end-to-end through one IDP golden path?"*), the extraction pipeline cannot manage its own infrastructure. `M2` (`platform-engineering/PE_Roadmap_M2.md`) abstracts cloud hosting into reusable, hardened Terraform modules (`standard_enterprise_api` in `platform-infra-modules`) and golden repository templates (`enterprise-api-template`):
- **Policy-as-Code (`tfsec` / `trivy`):** Guarantees that container images entering production have zero unaddressed CVEs and that networking boundaries enforce strict private subnet isolation.
- **Secretless Hybrid Identity:** Ensures the pipeline accesses credit agreement document stores and vector databases via temporary, IAM-attested role assumptions rather than static API keys.
- **Self-Service Execution:** Application developers (`M0`/`M1`) push Python extraction logic to `covenant_pipeline/src/`, while the `M2` IDP factory automatically provisions compute, runs security gates, and manages production rollout.
