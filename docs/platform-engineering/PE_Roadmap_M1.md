<!-- MIRROR: auto-synced from notes/projects/covenant/platform-engineering/PE_Roadmap_M1.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_project_docs.py -->

---
id: projects-covenant-platform-engineering-PE_Roadmap_M1
type: project_strategy
status: draft
dependencies:
  - math/platform-engineering/Math_Containerization.md
  - math/platform-engineering/Math_Notes_Platform_Engineer.md
  - projects/covenant/platform-engineering/PE_Infrastructure_Invariants.md
tags: []
invariants: []
---
## Platform Engineering Roadmap: The CA Pipeline

**Milestone 1 (M1)** deploys the Covenant Extraction Pipeline to cloud infrastructure. **Milestone 2 (M2)** generalizes to an Internal Developer Platform (IDP) — see [PE_Roadmap_M2.md](PE_Roadmap_M2.md).

Planning docs for the infrastructure layer. Phase 1 implementation: see [Docker_Documentation.md](https://github.com/endisciple13/covenant_pipeline/blob/main/Docker_Documentation.md) in the `covenant_pipeline` repo.

### Purpose axioms

- **A1 — Learning is the objective function.** When a design trade-off pits "best production choice" against "most instructive choice at comparable cost and safety," the instructive choice wins. A roadmap phase that ships infrastructure without teaching its workings has failed even if the infrastructure runs.
- **A2 — Role split is fixed.** Andy specifies and verifies (Layers 0, 1, 4); agents implement (Layers 2, 3). Andy does not read or write code. Every phase must therefore state what *Andy* does — which axioms he supplies, which architecture he ratifies, which observable behavior he validates — not only what the agent builds. A phase whose human role is "watch" is misdesigned.
- **A3 — The operating loop is the learning mechanism.** Manual `apply → smoke test → observe → destroy → recreate`, run by Andy himself, is where understanding forms (the Layer 4 external coupling of this project). A milestone is *done* when Andy can run its loop unassisted and explain each observed effect, not when the agent's tests pass.
- **A4 — Scope of "the workings":** the four-pillar ladder from the math notes — containerization, infrastructure-as-code, CI/CD, runtime orchestration — is the intended competency surface. See the E1 orchestration-gap decision at M1 exit for the orchestration pillar.

### The Goal

Build and operate the cloud path for the Covenant Pipeline **in order to learn the workings of platform engineering**. The deployed pipeline is the proof artifact; understanding is the product. The roadmap may be large; largeness is handled by milestones (M1, M2, and later decisions such as E1), never by thinning learning content. AWS is the sole target cloud for this milestone (ECS Fargate + ECR + VPC); other clouds may appear only as labeled contrast.

**Technical blueprints (detailed design specs):**

| Phase | Blueprint | Status |
|-------|-----------|--------|
| Phase 1: Local Containerization | [PE_RM_Phase1.md](blueprints/PE_RM_Phase1.md) | Implemented — see [Docker_Documentation.md](https://github.com/endisciple13/covenant_pipeline/blob/main/Docker_Documentation.md) |
| Phase 2: Target Cloud Topology (AWS) | [PE_RM_Phase2.md](blueprints/PE_RM_Phase2.md) | Design only |
| Phase 3: Infrastructure as Code (Terraform) | [PE_RM_Phase3.md](blueprints/PE_RM_Phase3.md) | Design only |
| Phase 4: CI/CD Orchestration | [PE_RM_Phase4.md](blueprints/PE_RM_Phase4.md) | Design only |

> **Design audit (2026-07-04):** all four blueprints reviewed pre-implementation; seven defects corrected in place — see each blueprint's *Design Audit Notes* section. Notable: Mountpoint-for-S3 is not Fargate-compatible (Phase 2), HTTPS/ACM requires an owned domain (Phases 2–4), the Terraform state backend needs out-of-band bootstrap (Phase 3), and the CI audit gate as specified is fixture-scoped, not release-scoped (Phase 4).
>
> **R06 update (2026-07-16):** Mountpoint-for-S3 / Fargate incompatibility remains a true *historical* defect. AWS now documents **S3 Files** volumes as fully supported on Fargate. **Human Decision 1 closed 2026-07-16:** Andy ratified native S3 Files for the personal PoC because it preserves the frozen `/app/data` contract, avoids an application adapter, and keeps the learning work in the infrastructure layer. The application-level S3 adapter remains portability contrast only, not an implementation branch.

### Phase 1: Local Containerization

**Blueprint:** [PE_RM_Phase1.md](blueprints/PE_RM_Phase1.md) | **Implementation:** [Docker_Documentation.md](https://github.com/endisciple13/covenant_pipeline/blob/main/Docker_Documentation.md)

Phase 1 is **implemented and frozen as-built**. The roadmap describes the working Compose topology; it does not propose rewrites to Dockerfiles, compose, or application code in this pass.

**As-built contracts (describe, do not rewrite):**

- Backend service: port `8000:8000`; env-driven PDF/output paths under `/app/data`; volume `./data:/app/data`.
- Frontend service: port `5173:80` (host 5173 → Nginx 80); depends on backend.
- Shared `./data` bind mount is a recorded local-dev exception to full image isolation.

**Andy role:** Supplies A1–A4 as the learning objective for packaging; ratifies that Phase 1 remains the as-built baseline (ports, bind mounts, no silent rewrite); validates container-parity / config-totality behavior on the golden fixture by observing identical inside/outside runs and fail-fast missing-config behavior.

**Operating-loop exit (A3):** Andy can bring the Compose stack up, hit the viewer and API, explain what each published port and the `./data` mount do, tear the stack down, and recreate it unassisted — and can state why parity (not “it ran once”) is the done criterion.

#### What this phase teaches

An image is an immutable, layered filesystem plus metadata, addressed by content digest; a container is a process started from one. The load-bearing idea is **context collapse**: at build time you declare every dependency the software needs, and at run time execution depends only on what was declared — never on whatever happens to be installed on the host. That is why one test carries this whole phase: `container-parity` (invariant 7, enforced) runs the golden fixture inside and outside the container and demands identical output, catching environment drift, dependency skew, and path bugs in a single check. Its partner `config-totality` (invariant 8, enforced) checks the complement: configuration the image does *not* seal in must fail fast and loudly when missing, never start on a silent default.

**Math lens (tier-gated):** `container-context-collapse` is **tight** — its transfer claim *is* the parity test, so inferences from it are licensed. Keep its breakage lines in view: the kernel and CPU architecture are shared below the userland boundary (an image is not portable across architectures), and bind mounts are declared exceptions to isolation — which is exactly why this project's `./data` mount is recorded as a dev exception rather than hidden. **[Analogy]** The exponential-object story (image as $Y^D$, `docker run` as `eval`) is heuristic scaffold: useful for remembering "a program with its context sealed in," licensed for nothing further.

### Phase 2: Target Cloud Topology (AWS)

**Blueprint:** [PE_RM_Phase2.md](blueprints/PE_RM_Phase2.md)

Design the AWS target topology that hosts the Phase 1 images: **ECR** (registry), **ECS Fargate** (compute), **VPC** + ALB (networking), IAM (execution role vs task role). Azure Container Registry / Azure Container Apps appear only as contrast alternatives, never as deployment targets.

- **Container registry:** Amazon ECR stores image digests for backend and frontend.
- **Compute:** ECS Fargate runs tasks from those digests without managing VMs.
- **Networking & IAM:** VPC, subnets, ALB, security groups; execution role (pull images / write logs) vs task role (S3 Files mount access / app AWS APIs).
- **TLS:** ACM HTTPS requires an owned domain + DNS validation; when no domain exists, HTTP :80 PoC fallback is explicit.
- **Personal PoC cost deviation:** public-subnet / no-NAT topology (see threat boundary below); enterprise variant remains private subnets + NAT.

#### Storage selection (Human Decision 1 ratified 2026-07-16)

**Selected:** native **S3 Files** volume preserving the existing `/app/data` file contract. The grounded comparison favored S3 Files for this personal PoC because it removes adapter code and contract migration, is natively supported on ECS Fargate, and exposes file-system/IAM/network/synchronization behavior directly in the A3 operating loop. The application-level S3 object adapter remains the more portable contrast, but its additional application work is deferred.

**Ownership and teardown:** a versioned/encrypted general-purpose S3 data bucket is an enumerated persistent prerequisite outside the session-scoped main stack. The main stack owns the S3 Files file system, access point, mount targets, mount-target security group, and ECS volume wiring. Before destroy, synchronization health must show no pending exports or export failures; main-stack destroy removes the S3 Files resources while retaining the owned data bucket. The implementation plan must verify current prices against the `$5/month` stop rule before apply.

#### Threat boundary: public-subnet / no-NAT (personal PoC)

**The deviation.** The enterprise-correct topology is private subnets with NAT (or VPC endpoints) for egress and TLS at the edge. This PoC deliberately runs tasks in public subnets with public IPs and no NAT Gateway (~$35/month avoided, per the Phase 2 blueprint's recorded deviation), and serves HTTP-only when no owned domain exists for ACM. The deviation buys cost, not correctness — this section records exactly what it exposes and the conditions under which it stays acceptable.

**Accepted threat classes.** (1) *Direct inbound exposure:* task ENIs carry public IPs, so the security group is the only barrier between the internet and the containers — there is no private-subnet defense in depth. (2) *Plaintext transport:* HTTP-only means anything transiting the ALB is readable in flight. (3) *Uncontrolled egress origin:* without NAT, tasks originate traffic from their own ephemeral public IPs — no single egress point to monitor or allowlist.

**Compensating controls (each one checkable).** Task security groups admit ingress from the ALB security group only — never 0.0.0.0/0 on task ports; the ALB listener is the sole public entry; no SSH/exec ingress exists anywhere; the Gemini API key travels via Secrets Manager into the task via **execution-role** injection, never in the image, the repo, or HTTP traffic (its egress to the API is HTTPS regardless of the inbound scheme); and every session ends in `terraform destroy`, so the exposure window is hours, not standing.

**Boundary invariant — the deviation is valid only while all three hold:** (i) the data processed is the public-materials fixture — the moment any private or client document enters, this topology is disqualified; (ii) sessions are teardown-bounded per the cost rules; (iii) the only ingress path is the ALB listener. Violating any condition routes back to the blueprint's enterprise variant (private subnets + NAT + TLS), which remains the design of record for anything beyond personal practice.

**After `apply`, verify (A3):** public IP count matches expectation (task ENIs + ALB, nothing else); direct requests to task ports from the internet time out; the security-group graph shows task ingress referencing only the ALB security group.

**Andy role:** Supplies topology axioms (what must be reachable, what must stay private, what may be PoC-deviated); ratifies the public-subnet/no-NAT threat boundary and the S3 Files persistence branch; validates idle-cost inventory, storage synchronization/ownership, security-group ingress graph, and killed-task replacement observation on ECS — without claiming the E1 orchestration gap is closed.

**Operating-loop exit (A3):** Andy can name, for each Compose service, its AWS host object and which identity acts; explain the idle-cost inventory; verify the threat-boundary checks after apply; and destroy/recreate the topology unassisted. Observing Fargate replace a failed task is in scope; operating a full reconciliation control plane is not (see E1).

#### What this phase teaches

Topology design is an exercise in **interfaces and identities**. The platform never sees your Python or React internals — it sees an OCI image and its declared contract (ports, health endpoint, environment). Learning this phase means being able to name, for every Compose service, the AWS object that hosts it (task definition, service, ALB target group), which of two identities acts (the *execution role* that pulls images and writes logs vs the *task role* the application assumes for S3/secrets), and **what remains billable when nothing is running** — the idle-cost inventory is a design output, not an accident. The reconciliation machinery is present but veiled: an ECS service maintains desired task count and replaces failures, yet Fargate hides the loop's internals — observing a killed task get replaced is in scope here; *operating* a reconciliation loop is the open E1 decision, not covered by this phase.

**Math lens (tier-gated):** `eval-generality-interface` is **tight** — the platform depends only on the OCI contract, so the application can be rewritten freely behind a stable interface with zero platform change; that residue is checkable and is what invariant candidate 9 (ports listening, healthcheck schema-valid) operationalizes for this phase. `k8s-control-loop` is **tight** but its guarantee is *retry, not convergence* — reconciliation is negative feedback, never a promise that the system reaches the desired state. **[Analogy]** Talk of "objects in the Cloud Category" is heuristic inventory discipline — no morphisms or composition are defined — and licenses no inference.

### Phase 3: Infrastructure as Code (Terraform)

**Blueprint:** [PE_RM_Phase3.md](blueprints/PE_RM_Phase3.md)

Declare the Phase 2 AWS topology in Terraform. Manual clicking in the console is prohibited for the main stack.

- **Provider:** AWS only as the target provider (other clouds may be named only as contrast).
- **Remote state backend:** S3 bucket for state; locking via `use_lockfile = true` (DynamoDB locking is deprecated legacy, not the target).
- **Bootstrap:** create the state bucket (and any residual lock resources if present) out-of-band *before* the first `terraform init` — the documented chicken-and-egg exception.
- **Resources:** ECR, ECS/Fargate services and task definitions, VPC/ALB/IAM as designed in Phase 2.
- **TLS:** same ACM domain requirement / HTTP :80 PoC fallback as Phase 2.

**Andy role:** Supplies the teardown/ownership axioms for the state backend vs main stack; ratifies `plan` diffs before `apply`; validates that a second plan on unchanged code is empty after a clean apply, and that `destroy` leaves no unintended session-scoped billable resources.

**Operating-loop exit (A3):** Andy can run `plan → apply → observe → destroy → recreate` unassisted, explain what state records, why locking exists, and the teardown order (main stack first; state bucket emptied/deleted only when retiring the backend).

#### What this phase teaches

Terraform's real subject is **state**: the recorded binding between your declarations and live cloud objects. A `plan` is point-in-time evidence — configuration diffed against state and provider reads — to be reviewed like a proof sketch, not trusted like a theorem; `apply` executes the reviewed diff; **drift** is reality diverging from the record when anything mutates the cloud out-of-band. The discipline of the phase is the loop: `apply → observe → destroy → recreate` until a second plan on unchanged code is empty — that emptiness is the phase's central observable. Two structural facts must be owned, not memorized: the state backend (S3 bucket, lockfile locking) exists *before* and *outside* the stack it tracks, created once out-of-band — the documented exception to no-manual-changes — and therefore has its own teardown order; and locking exists because two concurrent applies against one state file corrupt it.

**Math lens (tier-gated):** **[Analogy]** `iac-functor` (Terraform as functor with $F(id)=id$) is heuristic — and instructively *false*: a plan on unchanged code produces mutations precisely when drift exists, which is why drift detection is a feature. The checkable residue that survives is **reconciliation idempotence**: absent external drift, a second unchanged plan is empty — make that the exit observable, not the functor story. **[Analogy]** `cross-cloud-natural-transformation` is heuristic; its usable spirit — "no special-casing" — is a design ideal deferred to M2's module work. Invariant candidate 11's reproducibility half (rerun against the same volume reproduces artifacts) is owned here.

### Phase 4: CI/CD Orchestration

**Blueprint:** [PE_RM_Phase4.md](blueprints/PE_RM_Phase4.md)

Automate build, audit, push, and deploy so a push updates live AWS architecture under fail-closed gates.

- **Identity:** GitHub→AWS OIDC as the default (no stored long-lived deployment keys in the repository).
- **Jobs (dependency graph):** audit gate → build images → push digests to ECR → Terraform apply / task definition update by digest.
- **Audit scope (live constraint):** the audit gate as specified is fixture-scoped, not release-scoped — passing CI attests only to what the gates actually check.
- **TLS:** ACM HTTPS still requires owned domain + DNS validation; HTTP :80 PoC fallback when no domain.
- **Observation (E1/E4):** in-scope observation of deploy outcomes and service health does **not** close the E1 orchestration gap.

**Andy role:** Supplies the gate-scope axioms (what CI must prove vs what remains unverified); ratifies OIDC role trust and workflow edges; validates a failed predecessor blocks successors and that the running task resolves to a digest he can name.

**Operating-loop exit (A3):** Andy can trigger the workflow, read a fail-closed run log, confirm digest-based deploy, destroy/recreate via the Terraform path, and explain the fixture-scoped vs release-scoped audit boundary without claiming more than the gates enforce.

#### What this phase teaches

CI/CD is **gated promotion under explicit identity**. The pipeline is a dependency graph of jobs where each edge is a refusal rule — a stage that will not run if its predecessor failed — and the deploy job holds a distinct, short-lived identity: GitHub's OIDC token exchanged for a scoped AWS role session, so no long-lived cloud key exists anywhere in the repository. Deployment is by **digest**, not tag: the running task definition resolves to exact image content, making "what is actually deployed" a checkable fact rather than a convention. Equally important is what the gate does *not* cover: the audit gate as specified is fixture-scoped, not release-scoped (a recorded 2026-07-04 constraint still live) — passing CI attests to what the gates actually check, nothing more, and knowing that boundary precisely is the learning objective.

**Math lens (tier-gated):** `ci-composition-gate` is **tight** — fail-closed gating is domain restriction enforced by the workflow engine's dependency edges, checkable in any run log where a failed predecessor blocks its successors. Its breakage lines are the phase's honest edges: branch-protection bypasses exist, and the gate's strength equals the actual checks configured, no more. **[Analogy]** Framing failure as a "bottom type" is misformalized (partial maps are the right setting) — keep it as memory scaffold only. Invariant candidate 10 (images pinned by digest, dependencies locked) is owned by this build path jointly with Phase 2's registry.

## Invariant inventory binding

| Inventory # | Id / status | Owning phase(s) | Binding |
|---|---|---|---|
| 7 | `container-parity` (enforced) | Phase 1 inheritance | Already in frontmatter of `PE_Infrastructure_Invariants.md`; M1 inherits — do not re-ratify |
| 8 | `config-totality` (enforced) | Phase 1 inheritance | Same |
| 9 | candidate — ports listening; healthcheck schema-valid | **Phase 2** (cloud healthcheck / port contract; `eval-generality-interface` tight) | Graduates when Phase 2 implemented |
| 10 | candidate — base images pinned by digest; deps locked | **Phase 2 / Phase 4** build path (ECR push + CI image build; `image-immutability`) | Graduates when owning build path is implemented; Phase 1 blueprint already restated the enforceable form |
| 11 | candidate — compose graph acyclic; volume rerun reproducibility | **Phase 1** (compose topology) **and Phase 3** (IaC-declared volume/persistence reproducibility) | Graduates when owning phases implemented |

Candidates 9–11 graduate to frontmatter `invariants:` entries when the platform-engineering roadmap phases that own them are implemented.

As phases land, populate spec-derived invariant candidates via `/invariant-propose`. **Neither agents nor Composer write frontmatter `invariants:` entries — entry is human ratification only.**

## Cost and teardown

### Rules (binding)

1. Standing cost while not practicing ≈ **$0**: every practice session ends in `terraform destroy` of the main stack.
2. The Terraform **state backend** (S3 bucket; lockfile locking) exists **before** the main stack and is **not** destroyable by it — explicit ownership + teardown order required (bootstrap create → main apply → main destroy → *separately* empty/delete state bucket when retiring the backend).
3. Observable post-session check: no *unintended session-scoped* cost-bearing resources remain; every *deliberate persistent exception* is enumerated, owned, and bounded.
4. **$5/month ceiling** (E2): AWS Budget alerting control already set — **alerts, does not hard-cap charges**. Treat as alerting threshold + feasibility constraint. If a typical practice session cannot fit, **stop and route to Andy** — never silently loosen.

### Observable checklist (what Andy looks at after destroy)

S3 buckets (the deliberately persistent data bucket + any session-created bucket), S3 Files file systems/access points/mount targets and synchronization health, ECR images (lifecycle-bound), CloudWatch log groups, Secrets Manager secrets, public IPv4 addresses, load balancers, running ECS services/tasks, **and** the deliberately persistent state bucket.

### Sourced unit prices (us-east-1 / US East, fetched 2026-07-16)

| Resource | Unit price (sourced) | Source |
|---|---|---|
| Fargate Linux/x86 vCPU | $0.000011244 / vCPU-second | [Fargate pricing](https://aws.amazon.com/fargate/pricing/) Example 1 |
| Fargate Linux/x86 memory | $0.000001235 / GB-second | same |
| Fargate duration | per-second, **1-minute minimum** | same |
| ALB | $0.0225 / partial-or-full hour + LCU usage | [ELB pricing](https://aws.amazon.com/elasticloadbalancing/pricing/) (US-East-1 example) |
| Public IPv4 (in-use or idle) | $0.005 / address-hour | [VPC pricing](https://aws.amazon.com/vpc/pricing/) |
| ECR private storage | $0.10 / GB-month | [ECR pricing](https://aws.amazon.com/ecr/pricing/) Example 1 |
| S3 Standard storage | starts ~$0.023 / GB-month (US East; confirm tier table at apply time) | [S3 pricing](https://aws.amazon.com/s3/pricing/) |
| Secrets Manager | $0.40 / secret-month (prorated) + API calls | [Secrets Manager pricing](https://aws.amazon.com/secrets-manager/pricing/) examples |
| CloudWatch Logs | usage-based (session-scoped; destroy/retain policy must be explicit) | [CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/) |
| AWS Budgets monitoring alerts | free; action-enabled budgets may incur fees | [AWS Budgets pricing](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/) |

### Practice-session arithmetic (Phase 2 personal PoC topology)

**Always-on Fargate (backend 0.5 vCPU/1 GB + frontend 0.25 vCPU/0.5 GB), Linux/x86:**

- Backend CPU/hr = `0.5 × 0.000011244 × 3600` = **$0.020239**
- Backend mem/hr = `1 × 0.000001235 × 3600` = **$0.004446**
- Frontend CPU/hr = `0.25 × 0.000011244 × 3600` = **$0.010120**
- Frontend mem/hr = `0.5 × 0.000001235 × 3600` = **$0.002223**
- **Fargate services subtotal ≈ $0.037 / hour**

**Rough deployed floor (public-subnet PoC, before S3 Files high-performance storage/data access, underlying S3 storage/requests, LCU, logs, transfer, and pipeline run-task):**

- Fargate services ≈ $0.037
- ALB ≈ $0.0225 / partial hour
- Public IPv4: 2 task ENIs + 2-AZ ALB ≈ 4 × $0.005 = **$0.020**
- **Floor ≈ $0.080 / hour**

**Feasibility vs $5 ceiling:** A 1-hour practice session at the floor is ~$0.08 before S3 Files/S3, LCU, logs, transfer, and pipeline-run charges; five such sessions ≈ $0.40 plus small persistent ECR, data-bucket, state-bucket, and Secrets charges. **Fits the $5 alerting ceiling under short sessions + teardown only after the omitted S3 Files/S3 components are estimated for the actual fixture.** If Andy runs multi-hour always-on stacks without destroy, the floor reaches $5 in ~62 hours of continuous deploy — treat that as a discipline failure, not a reason to raise the ceiling. NAT Gateway (~$35/month class) remains **out of scope for personal PoC** (use public-subnet deviation + threat-boundary writeup).

**Persistent exceptions:** Terraform state S3 bucket (owned; teardown-last); S3 Files data S3 bucket (owned; retained across main-stack destroy and retired separately); optional retained ECR images under lifecycle policy; Secrets Manager secret if not deleted between sessions (prefer delete-or-accept $0.40/mo prorated); CloudWatch log groups if retention > 0.

## M1 exit — E1 orchestration gap (E1(c) ratified)

Math step 4 (`k8s-control-loop`, tight) has no full milestone home in M1; Fargate hides the reconciliation loop. **E1(c) ratified:** record the gap now; the M3 (or equivalent) decision becomes due when the M1 operating loop is stable. In-scope observation duties in Phases 2/4 do **not** close this gap (E4).

**Ratified dispositions (E1/E3/E2/E4, 2026-07-16):** E1(c) gap recorded here; E3 keep four-phase skeleton; E2 $5/month ceiling as Budget alert (not hard cap); E4 uniform depth with frontier quality for in-scope content, A3 exits as floor, orchestration = observation duties only.
