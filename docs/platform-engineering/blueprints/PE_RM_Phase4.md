<!-- MIRROR: auto-synced from notes/projects/covenant/platform-engineering/blueprints/PE_RM_Phase4.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_pe_docs.py -->

# Technical Blueprint: Phase 4 - CI/CD Orchestration (The Control Loop)

## I. Objective

**CS / English:** Automate the full path from a Git push to a live AWS deployment. A developer merges application or infrastructure code; GitHub Actions runs integrity checks, builds Docker images, pushes them to ECR, and triggers a Terraform apply to roll out the new images to ECS Fargate — with no manual steps.

**Mathematical Formalization:** Continuous Integration is a strict composition of validation morphisms on the code category $\mathcal{C}$:

$$CI_{eval} = f_3 \circ f_2 \circ f_1$$

Where:

- $f_1 : X_0 \to X_{linted}$ — static analysis / unit tests
- $f_2 : X_{linted} \to X_{audited}$ — deterministic integrity audit (`audit.py`)
- $f_3 : X_{audited} \to X_{built}$ — Docker image build

**The Bottom Type ($\bot$):** If $f_2$ fails (dangling pointers, circular references, type violations in compiled payload), the morphism evaluates to $\bot$. Because $f_3$ requires domain $X_{audited}$ and $\bot \neq X_{audited}$, the composition $CI_{eval}$ is **undefined** — the pipeline halts. Unproven code cannot proceed to build or deploy.

**The Deployment Functor:** Let $\mathcal{C}_{valid} \subset \mathcal{C}$ be the subcategory of commits that passed $CI_{eval}$. The CD pipeline is a functor:

$$F_{deploy} : \mathcal{C}_{valid} \to \mathcal{D}_{AWS}$$

restricted to validated code only. Phase 3's Terraform functor $F$ executes the infrastructure update; Phase 4 orchestrates when $F$ is invoked.

**Prerequisites:** Phase 1 (Docker images), Phase 2 (AWS topology designed), Phase 3 (Terraform modules designed). See [PE_RM_Phase2.md](PE_RM_Phase2.md) and [PE_RM_Phase3.md](PE_RM_Phase3.md).

## II. Target Architecture & File Tree

```
/ (Project Root)
├── .github/
│   └── workflows/
│       ├── ci.yml                  # PR checks: test + audit (no deploy)
│       └── deploy.yml              # Main branch: full CI + build + push + terraform apply
├── infra/
│   └── terraform/                  # Phase 3 Terraform (target of deploy job)
└── (existing application + Docker files from Phase 1)
```

**GitHub repository secrets required (not committed):**

| Secret | Purpose |
|--------|---------|
| `AWS_ACCESS_KEY_ID` | CI role for ECR push + Terraform apply |
| `AWS_SECRET_ACCESS_KEY` | Paired with above |
| `AWS_REGION` | e.g. `us-east-1` |
| `GEMINI_API_KEY` | Optional: for integration test stage (not stored in repo) |

**Recommended:** Replace long-lived access keys with **OIDC federation** (`aws-actions/configure-aws-credentials` + `id-token: write` permission) for production. Design-level PoC may use access keys initially.

## III. Component Specifications

### Step A: Workflow Triggers

**Purpose:** Define when automation runs and what code paths activate which jobs.

#### `ci.yml` — Pull Request Gate

- **Trigger:** `pull_request` to `main` (and optionally `infra/docker`)
- **Jobs:** Test + Audit only (no build, no deploy)
- **Purpose:** Fail fast on PRs before merge; protect `main`

#### `deploy.yml` — Main Branch Deploy

- **Trigger:** `push` to `main`
- **Jobs:** Full pipeline — Audit → Build → Push → Deploy
- **Concurrency:** `group: deploy-${{ github.ref }}` with `cancel-in-progress: true` (prevent overlapping deploys)

**Reasoning:** Separating PR checks from deploy workflow follows the $\mathcal{C}_{valid}$ restriction — only merged code reaches $F_{deploy}$.

### Step B: CI/CD Jobs (deploy.yml)

**Purpose:** Implement the morphism chain $f_3 \circ f_2 \circ f_1$ followed by deployment.

#### Job 1: `integrity-audit` ($f_2$ — The Deterministic Gate)

**Purpose:** Run Phase 3a database audit before any image is built. Fail closed.

- **Runner:** `ubuntu-latest`
- **Steps:**
    1. Checkout code
    2. Set up Python 3.11
    3. `pip install -e ".[viewer]"`
    4. Generate a **fixture compiled payload** for audit (or use committed test fixture under `tests/fixtures/`)
    5. Run: `covenant-pipeline audit` (invokes [covenant_pipeline/phases/audit.py](https://github.com/endisciple13/covenant_pipeline/blob/main/covenant_pipeline/phases/audit.py))
    6. **Exit criteria:** Non-zero exit if `Audit_Status` is not `Clean` or if dangling pointers / circular references / type violations are detected

- **Audit checks (from `audit.py`):**
    - Circular reference detection in glossary graph
    - Dangling `[$REF: ...]` pointer sweep
    - Numeric type validation on extracted covenant fields

**Reasoning:** This is the deterministic compiler gate — binary pass/fail before probabilistic LLM code ships. Maps directly to the roadmap's "Job 1: Run Phase 3a `audit.py`". In banking context, structural integrity of covenant data must be proven before deployment.

#### Job 2: `unit-tests` ($f_1$ — parallel with audit)

**Purpose:** Run existing Python unit tests.

- **Command:** `python -m unittest discover -s tests`
- **Fail:** Any test failure → $\bot$; downstream jobs skipped via `needs:` dependency

**Reasoning:** Fast, deterministic checks that don't require AWS credentials or Docker.

#### Job 3: `build-images` ($f_3$ — requires audit + tests pass)

**Purpose:** Build Phase 1 Docker images and tag with Git SHA.

- **Runner:** `ubuntu-latest`
- **Needs:** `[integrity-audit, unit-tests]`
- **Steps:**
    1. Configure AWS credentials
    2. Login to ECR (`aws ecr get-login-password`)
    3. Build backend: `docker build -f viewer/backend/Dockerfile -t {ecr}/covenant-pipeline-backend:{sha} .`
    4. Build frontend: `docker build -f viewer/frontend/Dockerfile -t {ecr}/covenant-pipeline-frontend:{sha} ./viewer/frontend`
    5. Tag both as `:latest` in addition to `:{sha}`
    6. Push all tags to ECR

- **Image tags:**
    - `{github.sha}` — immutable (global element $j_P$)
    - `latest` — rolling pointer to most recent successful build

**Reasoning:** Build only after $f_1$ and $f_2$ succeed. SHA tags enable rollback by re-deploying a previous Terraform variable value.

#### Job 4: `deploy-infrastructure` (Deployment Functor $F_{deploy}$)

**Purpose:** Update live AWS infrastructure to pull new images.

- **Runner:** `ubuntu-latest`
- **Needs:** `[build-images]`
- **Steps:**
    1. Configure AWS credentials
    2. Setup Terraform (`hashicorp/setup-terraform`)
    3. `cd infra/terraform`
    4. `terraform init`
    5. `terraform plan -var="backend_image_tag=${{ github.sha }}" -var="frontend_image_tag=${{ github.sha }}" -var-file=environments/dev/terraform.tfvars`
    6. `terraform apply -auto-approve` (dev only; prod requires manual approval gate)
    7. Output ALB DNS for smoke test comment on commit

- **ECS rolling update:** Terraform updates task definition image tags → ECS service triggers rolling deployment → old tasks drain, new tasks start

**Reasoning:** Terraform apply is the operational invocation of Phase 3's functor $F$. Passing image tags as variables creates a clean handoff from build job without editing `.tf` files in CI.

### Step C: Post-Deploy Verification (Smoke Test)

**Purpose:** Confirm the deployment functor produced a reachable system.

- **Optional Job 5: `smoke-test`** (needs `deploy-infrastructure`)
- **Checks:**
    - `curl -f https://{alb_dns}/api/pipeline-summary` — backend responds (may 404 if no artifacts in S3 yet; 502 = failure)
    - `curl -f https://{alb_dns}/` — frontend serves HTML
- **Notify:** GitHub commit status or Slack webhook on failure

**Reasoning:** Closes the control loop — verifies $I_{desired}$ is actually reachable, not just that Terraform reported success.

## IV. Control Loop Diagram

```mermaid
flowchart TD
  push["Git push to main"]
  f1["f1: unit-tests"]
  f2["f2: integrity-audit\naudit.py"]
  bot["Bottom type bot\nPIPELINE HALTS"]
  f3["f3: build-images\nDocker build"]
  ecrPush["Push to ECR\nsha + latest tags"]
  tfApply["terraform apply\nupdate ECS task defs"]
  ecsRoll["ECS rolling deploy"]
  smoke["smoke-test\nALB health check"]

  push --> f1
  push --> f2
  f1 -->|fail| bot
  f2 -->|fail| bot
  f1 -->|pass| f3
  f2 -->|pass| f3
  f3 --> ecrPush --> tfApply --> ecsRoll --> smoke
```

## V. Job Dependency Summary

| Job | Depends on | AWS credentials | Produces |
|-----|------------|-----------------|----------|
| `unit-tests` | — | No | Test pass/fail |
| `integrity-audit` | — | No | Audit pass/fail |
| `build-images` | tests + audit | Yes (ECR push) | Docker images in ECR |
| `deploy-infrastructure` | build-images | Yes (Terraform) | Updated ECS services |
| `smoke-test` | deploy | Yes (read ALB) | Health check pass/fail |

## VI. Security Considerations

- **No secrets in workflow YAML** — use GitHub Encrypted Secrets or OIDC
- **`GEMINI_API_KEY` never in CI logs** — mask outputs; only injected into ECS via Secrets Manager at runtime
- **Branch protection on `main`** — require PR + passing `ci.yml` before merge
- **Prod deploy gate** — `terraform apply` on prod requires manual `workflow_dispatch` or environment approval rule in GitHub

## VII. Out of Scope (Phase 4 Blueprint)

- Committed `.github/workflows/*.yml` files (design-level only)
- OIDC setup walkthrough (recommended for prod, not specified here)
- Pipeline `run-task` automation via EventBridge (on-demand extraction trigger — future enhancement)
- Blue/green or canary ECS deployments (rolling update sufficient for PoC)
