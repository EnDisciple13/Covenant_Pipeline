# Covenant Pipeline — Terraform (Layer 3 PoC)

Operator guide for the two-root Terraform layout that lowers
`PE_RM_Phase2` (topology) and `PE_RM_Phase3` (lifecycle) into proof space.

## Roots and state ownership

| Root | Path | State key (bucket `covenant-tfstate-andy-568728209842`) | Owns |
|------|------|----------------------------------------------------------|------|
| **Bootstrap** | `infra/terraform/bootstrap/` | `env/poc/bootstrap/terraform.tfstate` | ECR×2 (+ lifecycle/scan), persistent data bucket, Secrets Manager **metadata** (no value), inline ECR-push policy on unmanaged `github-actions-covenant-deploy` |
| **Main** | `infra/terraform/` | `env/poc/terraform.tfstate` | VPC/ALB/SGs, ECS, IAM task/exec/sync roles, S3 Files FS/AP/MT |
| **OOB** | — | N/A | State bucket itself (never create/import/destroy here) |

Main consumes bootstrap outputs as inputs: `backend_repository_url`, `frontend_repository_url`, `data_bucket_arn`, `gemini_secret_arn`, plus image digests from the hosted build.

## Operator sequence (Human-gated)

1. **PRECHECK** — identity `568728209842`, region `us-east-1`, state bucket healthy, budget alert active.
2. **Bootstrap plan** → Andy Gate B → `terraform apply` approved bootstrap plan only.
3. **Gate C** — commit SHA match + approve `aws-dev` workflow; upload HD1 fixture under standing authority; record digests.
4. **Main plan** (digests + bootstrap ARNs) → Andy Gate D (includes OOB `PutSecretValue`) → apply main.
5. Runtime / destroy / recreate / final teardown per the L3 implementation plan gates E–I.

**Never** `terraform apply` without Andy approving the exact saved plan for that stage.

## Sync-health destroy rule

Before every main-stack destroy: quiesce writers, then require fresh CloudWatch `AWS/S3/Files` datapoints for the `FileSystemId` with `PendingExports Sum = 0` and `ExportFailures Sum = 0`. Missing/stale data is BLOCKED, not zero-by-default. Verify expected objects in the persistent data bucket after the cutoff.

## Sensitive-plan handling

Do **not** commit: `.terraform/`, `*.tfstate*`, `tfplan`, `*.tfplan`, `*.tfplan.json`, `plan.json`, `.evidence/`, secret values, or unredacted plan JSON. Keep `.terraform.lock.hcl` and non-secret `terraform.tfvars`. Chat/docs/ledger get redacted summaries and hashes only.

## Hosted image build

`.github/workflows/build-push-poc.yml` — `workflow_dispatch` only, OIDC into `aws-dev`, digest emission. This is an L3 bootstrap surface, **not** Phase 4 (`deploy.yml` / audit gate / `environments/dev` / tag-based deploy identity).

## Prediction / evidence index (registers stay separate)

**P2 (topology):** `P2-VAL-01`, `P2-PLAN-01`, `P2-STOR-01`, `P2-SMOKE-01`, `P2-LOOP-01`, `P2-THREAT-01`, `P2-DOWN-01`  
**P3 (lifecycle):** `P3-VAL-01`, `P3-PLAN-01`, `P3-PLAN-02`, `P3-APPLY-01`, `P3-SMOKE-01`, `P3-DOWN-01`, `P3-RECREATE-01`, `P3-REPRO-01`

Shared evidence bytes live once under `infra/terraform/.evidence/<run-id>/` (gitignored). Closure manifests are validated by `tests/terraform/test_evidence_manifest.py`.

## Local offline checks

```bash
cd infra/terraform
terraform fmt -check -recursive
cd bootstrap && terraform init -backend=false && terraform validate
cd .. && terraform init -backend=false && terraform validate
# from repo root:
pytest tests/terraform/ -q
```
