<!-- MIRROR: auto-synced from notes/projects/covenant/platform-engineering/blueprints/PE_RM_Phase3.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_project_docs.py -->

---
id: projects-covenant-platform-engineering-blueprints-PE_RM_Phase3
type: blueprint
status: draft
dependencies:
  - projects/covenant/application/Pipeline_Invariants.md
  - projects/covenant/platform-engineering/PE_Infrastructure_Invariants.md
  - projects/covenant/platform-engineering/blueprints/PE_RM_Phase2.md
tags: []
invariants:
  - id: iac-topology-parity
    statement: "Terraform plan materializes every object declared in Phase 2 topology without undeclared resources"
inherited_invariants:
  - id: topology-completeness
    from: projects/covenant/platform-engineering/blueprints/PE_RM_Phase2.md
    status: planned
    enforced_by: "tests/terraform/test_topology_completeness.py::test_every_diagram_node_has_resource"
  - id: provenance-grounding
    from: projects/covenant/application/Pipeline_Invariants.md
    status: waived
    note: "Extraction pipeline invariants are out of scope for the Terraform IaC blueprint."
  - id: chunker-partition
    from: projects/covenant/application/Pipeline_Invariants.md
    status: waived
    note: "Extraction pipeline invariants are out of scope for the Terraform IaC blueprint."
  - id: chunker-coverage-audit
    from: projects/covenant/application/Pipeline_Invariants.md
    status: waived
    note: "Extraction pipeline invariants are out of scope for the Terraform IaC blueprint."
  - id: router-rule-dispatch
    from: projects/covenant/application/Pipeline_Invariants.md
    status: waived
    note: "Extraction pipeline invariants are out of scope for the Terraform IaC blueprint."
  - id: glossary-acyclic
    from: projects/covenant/application/Pipeline_Invariants.md
    status: waived
    note: "Extraction pipeline invariants are out of scope for the Terraform IaC blueprint."
  - id: metamorphic-stability
    from: projects/covenant/application/Pipeline_Invariants.md
    status: waived
    note: "Extraction pipeline invariants are out of scope for the Terraform IaC blueprint."
  - id: container-parity
    from: projects/covenant/platform-engineering/PE_Infrastructure_Invariants.md
    status: planned
    enforced_by: "tests/invariants/test_container_parity.py::test_container_parity_host_vs_docker"
  - id: config-totality
    from: projects/covenant/platform-engineering/PE_Infrastructure_Invariants.md
    status: planned
    enforced_by: "tests/invariants/test_config_totality.py::test_missing_env_fails_fast"
---
# Technical Blueprint: Phase 3 - Infrastructure as Code (Terraform)

## I. Objective

**Parent authority.** Declare the Phase 2 AWS topology in Terraform. Manual clicking in the console is prohibited for the main stack. AWS is the sole target provider (other clouds may be named only as contrast). Phase 1 is frozen as-built; this phase materializes the **corrected** Phase 2 PoC topology (public-subnet/no-NAT, HTTP :80, Nginx-preserving edge, digest-oriented images, native S3 Files persistence ratified by Human Decision 1 on 2026-07-16).

**Andy role:** Supplies the teardown/ownership axioms for persistent data/state buckets vs the session-scoped main stack; ratifies `plan` diffs before every apply; validates S3 Files synchronization health, an empty second plan after clean apply, and that `destroy` leaves no unintended session-scoped billable resources.

**Operating-loop exit (A3):** Andy can run `plan → apply → observe → synchronization check → destroy → recreate` unassisted, explain what Terraform state records, why locking exists, how S3 Files synchronizes with its durable bucket, and why the persistent data/state buckets retire separately from the main stack.

### Math lens

**[Analogy]** Terraform as an `iac-functor` mapping code objects to cloud objects is heuristic inventory discipline. The analogy is **false under drift** — out-of-band console mutations break any claim that code and cloud stay in lockstep without a plan check.

**Checkable residue:** Absent external drift, a second unchanged plan after a clean apply is empty (`P3-APPLY-01`). That residue — not the functor metaphor — is what this phase verifies.

**Prerequisites:** Phase 1 (Docker images) implemented; Phase 2 (cloud topology) designed and re-grounded. See [PE_RM_Phase2.md](PE_RM_Phase2.md).

### Invariant candidates (body obligations; not frontmatter)

| Candidate | Phase 3 body obligation | Gate |
|-----------|-------------------------|------|
| **11** (Phase 3 half — persistence-reproducibility) | For selected S3 Files: reset only the `/app/data/out` prefix, preserve and hash-check the public PDF fixture, rerun with the same declared configuration, verify the required artifact set/structural checks, and prove no undeclared local state. Compose-acyclic half remains Phase 1 ownership. | Human Decision 1 is closed; eventual `/invariant-propose` + Human gate still owns graduation. Do **not** write candidate 11 into frontmatter. |

Frontmatter invariant `iac-topology-parity` remains tied to the corrected Phase 2 blueprint: every Phase 2 topology node maps to a named Terraform address; undeclared extras are prohibited.

## II. Target Architecture & File Tree

Cursor must generate the following directory structure within the existing repository (design-level — committed `.tf` is out of scope for this blueprint-document pass):

```
/ (Project Root)
├── infra/
│   └── terraform/
│       ├── main.tf                 # Main root: wires session-scoped modules (no ECR/secret create)
│       ├── variables.tf            # Region, digests, data_bucket_arn, gemini_secret_arn, ECR URLs
│       ├── outputs.tf              # Exported values (ALB DNS, service names)
│       ├── providers.tf            # AWS provider configuration
│       ├── backend.tf              # Remote state: S3 + use_lockfile = true (key env/poc/terraform.tfstate)
│       ├── versions.tf             # Terraform ≥ 1.11.0 and provider constraints
│       ├── bootstrap/              # Persistent prerequisites root (separate state)
│       │   ├── main.tf             # Sole create site: modules/ecr + modules/secrets + data bucket + OIDC push policy
│       │   ├── backend.tf          # State key env/poc/bootstrap/terraform.tfstate
│       │   └── environments/poc/terraform.tfvars
│       ├── modules/
│           ├── network/            # VPC, public subnets, IGW, ALB :80, SGs, Service Connect namespace (no NAT/EIP in PoC)
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           ├── ecr/                # ECR repositories + lifecycle policies (called only from bootstrap/)
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           ├── ecs/                # Cluster, services, task definitions (digest pins)
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           ├── iam/                # Execution role vs task roles (+ S3 Files sync role)
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           ├── secrets/            # Secrets Manager metadata for GEMINI_API_KEY (called only from bootstrap/)
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           └── storage/            # Selected S3 Files file system, access point, mount targets, SG
│               ├── main.tf
│               ├── variables.tf
│               └── outputs.tf
│       └── environments/
│           └── poc/
│               └── terraform.tfvars    # ONE PoC environment/state path (Human 4)
```

**Two-root ownership (G2):** bootstrap owns ECR×2, the persistent versioned/encrypted data bucket, and persistent Secrets Manager **metadata** (no secret value). Main consumes `backend_repository_url`, `frontend_repository_url`, `data_bucket_arn`, and `gemini_secret_arn` as inputs and must not call `modules/ecr` or `modules/secrets` as create sites. The state bucket remains OOB.

**Contrast only (non-operative):** multi-environment scaffolding (`environments/dev` + `environments/prod`) may be named as an enterprise pattern; it is **not** the PoC target (Human 4 ratified).

## III. Component Specifications

### Step A: Provider Configuration & Remote State

**Purpose:** Initialize the Terraform runtime and persist state outside the developer laptop.

- **Provider:** `hashicorp/aws` — pin a Review-verified minor **≥ 6.41.0** in `versions.tf`; v6.40 introduced S3 Files resources and v6.41 added ECS task-definition `s3files_volume_configuration` support ([AWS provider v6.40.0](https://github.com/hashicorp/terraform-provider-aws/releases/tag/v6.40.0); [v6.41.0](https://github.com/hashicorp/terraform-provider-aws/releases/tag/v6.41.0))
- **Terraform version:** require **≥ 1.11.0** so `use_lockfile` is GA ([Terraform v1.11.0](https://github.com/hashicorp/terraform/releases/tag/v1.11.0); [CHANGELOG](https://github.com/hashicorp/terraform/blob/v1.11/CHANGELOG.md))
- **Region:** Configurable via `var.aws_region` (default `us-east-1` for PoC)
- **Remote backend (`backend.tf`):**
    - **State storage:** S3 bucket `covenant-pipeline-tfstate-{account-id}` (versioning enabled, encryption SSE-S3)
    - **State locking (target):** `use_lockfile = true` — S3-native locking ([S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3))
    - **DynamoDB locking:** deprecated/legacy **contrast only** — not the target design
    - **Key:** `env/poc/terraform.tfstate` (one PoC state path)
    - **Bootstrap:** the state bucket cannot be created by the Terraform it backs (chicken-and-egg). Create it once, out-of-band, *before* the first `terraform init` — via AWS CLI or a tiny separate bootstrap stack with local state. Explicit ownership; teardown-last retirement (empty/delete bucket only when retiring the backend — never as part of main-stack `destroy`).

- **Input variables (`variables.tf`):**

| Variable | Type | Purpose |
|----------|------|---------|
| `aws_region` | string | AWS region |
| `backend_image_digest` | string | ECR digest for backend image (`sha256:…`) |
| `frontend_image_digest` | string | ECR digest for frontend image (`sha256:…`) |
| `domain_name` | string | Optional; unused in operative HTTP :80 PoC (TLS contrast) |
| `data_bucket_arn` | string | ARN of the versioned/encrypted persistent S3 data bucket created by the separately reviewed bootstrap root |
| `gemini_secret_arn` | string | ARN of the persistent Secrets Manager secret **metadata** created by bootstrap (value written OOB; never in Terraform state) |
| `backend_repository_url` | string | ECR repository URL from bootstrap (main does not create ECR) |
| `frontend_repository_url` | string | ECR repository URL from bootstrap |

Do **not** use `backend_image_tag` / `frontend_image_tag` as deployment identity.

**Reasoning:** Remote state is mandatory for collaboration and CI/CD (Phase 4). Lockfile locking removes the DynamoDB lock table from the target design. Digest variables create a clean interface between Phase 4 (build/push) and Phase 3 (deploy).

### Step B: Resource Definitions (Modules)

**Purpose:** Declare every AWS object from the corrected [PE_RM_Phase2.md](PE_RM_Phase2.md) as Terraform resources.

#### Module: `network`

- `aws_vpc` — dedicated VPC
- `aws_subnet` — public subnets across 2 AZs (ALB **and** ECS tasks)
- `aws_internet_gateway`
- **No** `aws_nat_gateway` / NAT `aws_eip` in the operative PoC branch
- `aws_lb` (Application Load Balancer) — public-facing
- `aws_lb_listener` — **HTTP :80** operative (TLS/ACM = enterprise contrast only)
- `aws_lb_target_group` — **frontend (:80) only** as public target
- **No** ALB listener rules splitting `/api/*` → backend TG (Nginx preserves `/api/*` ownership)
- `aws_security_group` — ALB, frontend, backend (least-privilege ingress; no SSH/exec)

**Outputs:** `vpc_id`, `public_subnet_ids`, `alb_dns_name`, `frontend_target_group_arn`, security-group IDs

#### Module: `ecr`

- `aws_ecr_repository` — `covenant-pipeline-backend`, `covenant-pipeline-frontend`
- `aws_ecr_lifecycle_policy` — retain last 10 tagged images; expire untagged after 7 days
- `aws_ecr_repository_policy` — allow ECS task execution role to pull

**Outputs:** `backend_repository_url`, `frontend_repository_url`

#### Module: `ecs`

- `aws_ecs_cluster` — `covenant-pipeline`
- `aws_ecs_task_definition` — `backend`, `frontend`, `pipeline` (three definitions, two services + one run-task template)
- `aws_ecs_service` — `backend` and `frontend` (desired count from variable); tasks in public subnets with public IPs
- `aws_cloudwatch_log_group` — per task definition for container logs
- Task definitions pin images by digest: `"${repo_url}@${var.backend_image_digest}"` / frontend equivalent
- Environment block: exact frozen `COVENANT_*` paths from Phase 2 / Compose:
  - `COVENANT_PDF_PATH` = `/app/data/Credit_Agreement_Hallador.pdf`
  - `COVENANT_OUTPUT_DIR` = `/app/data/out`
  - `COVENANT_AUDITED_JSON` = `/app/data/out/final_compiled_payload_audited.json`
  - `COVENANT_DISPATCH_QUEUE_JSON` = `/app/data/out/dispatch_queue_output.json`
- Backend command: `uvicorn main:app --app-dir viewer/backend --host 0.0.0.0 --port 8000`
- Pipeline: entrypoint `covenant-pipeline`; command `run --pdf /app/data/Credit_Agreement_Hallador.pdf --output-dir /app/data/out`
- Secrets block: `GEMINI_API_KEY` from Secrets Manager ARN (injection via execution role)
- Frontend TG health: path `/`, status-code matcher only
- Fargate floor sizes: backend 0.5 vCPU / 1 GB; frontend 0.25 vCPU / 0.5 GB

**Outputs:** `cluster_arn`, `backend_service_name`, `frontend_service_name`, `pipeline_task_definition_arn`

#### Module: `iam`

- `aws_iam_role` — `ecsTaskExecutionRole` (trust: `ecs-tasks.amazonaws.com`) — ECR pull, logs, secret retrieve for injection
- `aws_iam_role_policy_attachment` — `AmazonECSTaskExecutionRolePolicy`
- `aws_iam_role` — `ecsBackendTaskRole` / `ecsPipelineTaskRole` — least-privilege S3 Files mount/read vs mount/read/write permissions
- `aws_iam_role` — S3 Files synchronization role scoped to the persistent data bucket/prefix and required EventBridge synchronization actions
- `aws_iam_policy` — scoped permissions per role; exact current actions verified during L3 Review

**Outputs:** `task_execution_role_arn`, `backend_task_role_arn`, `pipeline_task_role_arn`, `s3_files_sync_role_arn`

#### Module: `secrets`

- `aws_secretsmanager_secret` — `covenant-pipeline/gemini-api-key`
- Secret value **not** stored in Terraform — set manually or via CI/CD secret injection on first deploy

**Outputs:** `gemini_api_key_secret_arn`

#### Module: `storage` (native S3 Files — Human Decision 1 ratified)

- `aws_s3files_file_system` — linked to `var.data_bucket_arn` through the synchronization role; use default AWS-owned KMS encryption for file-system data/metadata unless Review justifies a customer-managed key (bucket-object encryption is configured separately)
- `aws_s3files_access_point` — application root with POSIX UID/GID verified against the actual backend image
- `aws_s3files_mount_target` — one in each operative AZ/subnet (maximum one per AZ; local network path for both task placements)
- `aws_security_group` — mount-target ingress TCP 2049 from backend/pipeline task SGs only; no public ingress. AWS specifies that compute resources reach S3 Files mount targets over NFS port 2049 ([mounting S3 Files on compute](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-files-attach-compute.html)); the optional ECS `transitEncryptionPort` does not replace this mount-target rule.
- `aws_s3files_synchronization_configuration` only when non-default import/export settings are justified by the public-fixture workload; otherwise retain service defaults and monitor them
- ECS task definitions use `s3files_volume_configuration`; backend mounts `/app/data` read-only and pipeline mounts `/app/data` read-write through the same access point. Task IAM roles and transit encryption are mandatory for S3 Files ECS volumes; ECS enforces transit encryption automatically.

**Persistent prerequisite boundary:** the versioned/encrypted general-purpose S3 data bucket is outside the session-scoped main stack and is supplied by `data_bucket_arn`. It must be created or adopted only through a separately reviewed prerequisite/bootstrap plan, then inventoried after every main-stack destroy. Do not hide it behind `prevent_destroy` inside a root that must complete `terraform destroy`.

**Synchronization and writer discipline:** the pipeline is the primary writer and backend is read-only for this PoC. Before destroy, retain evidence that `PendingExports = 0` and `ExportFailures = 0` (or the current equivalent metrics). Concurrent bucket-side and file-system-side writes to the same path are prohibited because S3 is authoritative on conflicts.

**Outputs:** `s3files_file_system_arn`, `s3files_access_point_arn`, mount-target IDs, data-bucket ARN

#### Root `main.tf` wiring

```hcl
# Conceptual wiring (design-level — not committed HCL)
# bootstrap/main.tf (persistent prerequisites; separate state)
module "ecr"     { source = "../modules/ecr"     ... }  # sole ECR create site
module "secrets" { source = "../modules/secrets" ... }  # sole secret-metadata create site
# + data bucket + narrowly scoped OIDC ECR-push policy on unmanaged deploy role

# main root (session-scoped topology)
module "network"  { source = "./modules/network"  ... }
module "iam"      { source = "./modules/iam"      ... }
module "storage"  { source = "./modules/storage"  ... }
module "ecs"      { source = "./modules/ecs"
                    depends_on = [module.network, module.iam, module.storage]
                    # consumes backend_repository_url, frontend_repository_url,
                    # data_bucket_arn, gemini_secret_arn, digests as variables
                    ... }
# main does not call module.ecr or module.secrets
```

**Topology parity:** Every corrected Phase 2 node → named Terraform address. Prohibit undeclared extras. State backend is **external** to the main-stack graph.

**Reasoning:** Modular Terraform mirrors Phase 2 decomposition. `depends_on` encodes the directed dependency graph. S3 Files preserves the frozen file contract while making persistence networking, IAM, synchronization, and teardown observable in the operating loop.

### Step C: Workflow (full A3 loop)

**Purpose:** Define the operational workflow for translating code changes into live AWS mutations.

#### Workflow

1. **`terraform validate`** — syntax/config check (TF ≥ 1.11.0)
2. **`terraform init`** — Download providers; configure remote backend (`use_lockfile`)
3. **`terraform plan -var-file=environments/poc/terraform.tfvars -out=tfplan`** — Compute creates/updates/destroys
4. **Human review** — Andy ratifies the saved plan before apply
5. **`terraform apply tfplan`** — Execute; converge desired state
6. **Smoke test** — use Terraform outputs (ALB DNS) per Phase 2 `P2-SMOKE-01` / `P2-THREAT-01` observations (reference; do not copy evidence rows into this register)
7. **Observe** — idle-cost inventory; optional killed-task replacement observation (Phase 2 `P2-LOOP-01`; does not close E1)
8. **Second unchanged plan** — expect `0` add / `0` change / `0` destroy (`P3-APPLY-01`)
9. **S3 Files synchronization gate** — `PendingExports = 0`, `ExportFailures = 0` (or current equivalent); stop on pending/failed synchronization
10. **`terraform destroy`** — session-scoped main stack first; retain the separately owned data/state buckets
11. **Post-destroy inventory** — no unintended session-scoped billable resources; enumerate persistent exceptions
12. **Recreate** — next plan create-only; second unchanged plan returns to `0/0/0`

**$5 stop rule:** If a typical practice session cannot fit the alerting threshold, **stop and route to Andy** — never silently loosen.

**Teardown order:** synchronization-health gate → session-scoped main stack → inventory persistent data/state buckets. Either bucket is emptied/deleted only through its separately approved retirement operation.

#### Drift policy

- If manual console changes occur, next `plan` reveals drift as unexpected diffs
- Policy: **no manual console edits** for the main stack — all changes flow through Git → Terraform

#### Image digest updates (handoff to Phase 4)

- CI/CD updates `backend_image_digest` / `frontend_image_digest` or passes `-var` flags
- `terraform apply` updates ECS task definitions to pull new digests
- ECS performs rolling deployment of backend/frontend services

**Reasoning:** Separating `plan` (read-only diff) from `apply` (mutation) is the review gate. Digest-as-variable creates the Phase 4 ↔ Phase 3 interface without treating tags as deployment identity.

## IV. Dependency Graph

```mermaid
flowchart TD
  network["module.network\nVPC ALB SG public subnets"]
  ecr["module.ecr\nRepositories"]
  iam["module.iam\nExec vs task roles"]
  secrets["module.secrets\nGEMINI_API_KEY"]
  storage["module.storage\nS3 Files fs access point mount targets"]
  dataBucket["persistent S3 data bucket\nexternal prerequisite"]
  ecs["module.ecs\nCluster Services Tasks"]

  network --> ecs
  ecr --> ecs
  iam --> ecs
  secrets --> ecs
  dataBucket --> storage
  network --> storage
  iam --> storage
  storage --> ecs
  iam --> ecr
```

## V. Out of Scope (Phase 3 Blueprint)

- Committed `.tf` files in **this** blueprint-document pass (design-level only; Track A implementation is a follow-on)
- Cloud execution / `apply` in this field-test measurement
- `terraform import` of existing resources
- Multi-account AWS Organizations / cross-account IAM
- Terraform Cloud / HCP Terraform (remote backend uses S3 + `use_lockfile` directly)
- Application-level S3 object adapter (portability contrast; not selected for this PoC)
- Multi-environment PoC scaffolding (contrast only)

## VI. Phase 3 Prediction Register

Distinct from Phase 2. Do not merge registers. Do not copy Phase 2 prediction evidence rows into this register.

| ID | Before-the-run condition | Prediction stated in advance | Falsifier / evidence to retain |
|---|---|---|---|
| P3-VAL-01 | Terraform files are generated from the ratified blueprint and initialized with Terraform ≥ 1.11.0 plus a Review-verified AWS provider ≥ 6.41.0. | `terraform validate` exits `0`, emits its success result, and emits no error diagnostic. | Non-zero exit or any error diagnostic. Retain stdout/stderr and version/provider-lock output. |
| P3-PLAN-01 | State backend and persistent data bucket exist outside the session-scoped main stack; main stack is absent; all Human decisions are ratified. | The initial saved plan reports a non-zero add count, `0` changes, and `0` destroys. It contains no DynamoDB lock table, NAT Gateway/NAT EIP, state-backend bucket, or data bucket owned by the main stack. | Any destroy, prohibited resource, persistent bucket in the main graph, or Phase 2 topology node without a Terraform address. Retain plan summary and address-to-topology matrix. |
| P3-PLAN-02 | Human Decision 1 ratified S3 Files and `data_bucket_arn` names the owned persistent bucket. | The runnable plan materializes exactly the selected S3 Files file system/access point/per-AZ mount targets/SG/task-volume wiring and contains no adapter implementation or path rewrite. | Missing/extra storage resource, adapter work, path rewrite, public NFS ingress, or unowned bucket. Retain storage-only plan JSON assertions and task-definition volume diff. |
| P3-APPLY-01 | Human has reviewed the saved plan and apply completes without an out-of-band mutation. | A second unchanged plan reports `0` to add, `0` to change, and `0` to destroy. | Any non-zero diff absent a separately recorded drift event. Retain both plan summaries and apply result. |
| P3-SMOKE-01 | Apply completed and the full pipeline output prerequisite holds. | Terraform output supplies the smoke-test entry value; the same root, `/api/document-data`, `/api/pdf`, direct-task-port, and threat-boundary observations specified in P2-SMOKE-01/P2-THREAT-01 pass without copying their evidence into the Phase 3 register. | Missing/incorrect output, failed ALB-path checks, successful direct task access, or a threat-boundary mismatch. Retain Phase 3 output-to-Phase 2 observation references. |
| P3-DOWN-01 | S3 Files synchronization is healthy and `terraform destroy` runs against the session-scoped main stack after smoke and observation. | Destroy completes successfully; no file system/access point/mount target or other unintended main-stack resource remains; the enumerated data/state buckets and only other owned persistent exceptions remain. | Pending/failed synchronization, destroy failure, residual S3 Files/main-stack resource, missing persistent-exception record, or main destroy attempting to retire either bucket. Retain synchronization metrics, destroy result, and inventory. |
| P3-RECREATE-01 | Main stack was cleanly destroyed while the state backend and persistent data bucket remain valid. | The next plan again shows the expected create-only topology, and recreate followed by a second unchanged plan returns to `0/0/0`. | Missing resources, unexpected changes/destroys, or a non-empty unchanged plan without recorded drift. Retain recreate plan and second-plan result. |
| P3-REPRO-01 | S3 Files is recreated against the same persistent bucket; only `/app/data/out` was reset; the public PDF fixture hash and declared configuration are unchanged. | The pipeline reproduces the required artifact set; the fixture hash is unchanged; deterministic artifacts match their declared hashes where applicable; LLM-derived artifacts pass their declared schema/provenance checks rather than an invented byte-equality requirement; no undeclared local state is needed. | Missing artifact, changed fixture, failed deterministic hash or schema/provenance check, synchronization failure, or dependence on undeclared local state. Retain reset command/evidence, fixture hash, artifact manifest, and applicable comparisons. |

## VII. Design Audit Notes

### 2026-07-04 (historical)

External design review prior to implementation; corrections applied in place:

1. **State-backend bootstrap documented** (§III Step A) — the chicken-and-egg was previously unstated and would stall the first `terraform init`.
2. **ACM certificate resources** — previously required for unconditional HTTPS; operative PoC is now HTTP :80 (Human 2); ACM remains enterprise contrast.
3. **Native S3 state locking noted** — historically as a DynamoDB alternative (Terraform ≥ 1.10). **Superseded 2026-07-16:** target is `use_lockfile` + TF ≥ 1.11.0; DynamoDB locking is deprecated contrast only — not "acceptable" as target design.
4. **§II file tree fixed** — a duplicated `infra/` subtree (generation artifact) merged; `environments/` sits inside the single `infra/terraform/` directory.

### 2026-07-16 (re-grounding)

Re-grounded in place from parent [PE_Roadmap_M1.md](../PE_Roadmap_M1.md) and corrected [PE_RM_Phase2.md](PE_RM_Phase2.md) via implementation plan `inbox/2026-07-16-pe-blueprints-regrounding-l2-plan.md`: `use_lockfile` + TF ≥ 1.11.0; one PoC env path; digest variables; no NAT/EIP in PoC; Nginx-preserving edge; conditional storage modules; candidate 11 conditional on Human 1; full A3 workflow; distinct 8-row prediction register. At this Step 2 checkpoint, storage selection remained open.

### 2026-07-16 (Human Decision 1 closure; post-Step-2 L2 re-entry)

Andy ratified native S3 Files for the personal PoC. This separately attributed re-entry replaces conditional persistence with a concrete S3 Files module and ECS volume contract, establishes the persistent-data-bucket vs session-main-stack ownership boundary, raises the AWS-provider floor to the first ECS-capable S3 Files release, and compiles synchronization-safe destroy/reproducibility predictions. The application adapter remains contrast only; completed Step 2 evidence remains frozen.
