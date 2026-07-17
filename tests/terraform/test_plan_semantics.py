"""Root-aware plan semantics (V1).

Gate B: set COVENANT_BOOTSTRAP_PLAN_JSON — zero skips required.
Gate D: set COVENANT_MAIN_PLAN_JSON — zero skips required for main cases.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_PLAN_JSON = os.environ.get("COVENANT_BOOTSTRAP_PLAN_JSON")
MAIN_PLAN_JSON = os.environ.get("COVENANT_MAIN_PLAN_JSON")

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
IMAGE_REF_RE = re.compile(r"^.+@sha256:[0-9a-f]{64}$")

BOOTSTRAP_ALLOWED_TYPES = {
    "aws_ecr_repository",
    "aws_ecr_lifecycle_policy",
    "aws_ecr_repository_policy",
    "aws_s3_bucket",
    "aws_s3_bucket_versioning",
    "aws_s3_bucket_server_side_encryption_configuration",
    "aws_s3_bucket_public_access_block",
    "aws_secretsmanager_secret",
    "aws_iam_role_policy",
}

BOOTSTRAP_PROHIBITED_TYPES = {
    "aws_secretsmanager_secret_version",
    "aws_iam_role",
    "aws_iam_openid_connect_provider",
    "aws_nat_gateway",
    "aws_eip",
    "aws_dynamodb_table",
    "aws_vpc",
    "aws_ecs_cluster",
    "aws_s3files_file_system",
}


def _load_plan(path: str) -> dict:
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def _resource_changes(plan: dict) -> list[dict]:
    return list(plan.get("resource_changes", []))


def _counts(plan: dict) -> tuple[int, int, int]:
    add = change = destroy = 0
    for rc in _resource_changes(plan):
        actions = rc.get("change", {}).get("actions", [])
        if actions == ["create"]:
            add += 1
        elif actions == ["delete"]:
            destroy += 1
        elif "update" in actions or actions == ["create", "delete"] or actions == ["delete", "create"]:
            change += 1
        elif actions == ["no-op"]:
            continue
        else:
            # treat mixed replace as change
            if "create" in actions and "delete" in actions:
                change += 1
            elif "create" in actions:
                add += 1
            elif "delete" in actions:
                destroy += 1
            elif "update" in actions:
                change += 1
    return add, change, destroy


def _types(plan: dict) -> set[str]:
    return {rc["type"] for rc in _resource_changes(plan) if "type" in rc}


def _addresses(plan: dict) -> set[str]:
    return {rc["address"] for rc in _resource_changes(plan) if "address" in rc}


def test_digest_hex_shape_helper():
    assert DIGEST_RE.match("0" * 64)
    assert not DIGEST_RE.match("0" * 63)
    assert IMAGE_REF_RE.match(
        "568728209842.dkr.ecr.us-east-1.amazonaws.com/covenant-pipeline-backend@sha256:" + ("a" * 64)
    )


@pytest.mark.skipif(not BOOTSTRAP_PLAN_JSON, reason="set COVENANT_BOOTSTRAP_PLAN_JSON for Gate B")
def test_bootstrap_plan_allowlist_and_counts():
    plan = _load_plan(BOOTSTRAP_PLAN_JSON)
    add, change, destroy = _counts(plan)
    assert add > 0
    assert change == 0
    assert destroy == 0

    types = _types(plan)
    for banned in BOOTSTRAP_PROHIBITED_TYPES:
        assert banned not in types, f"bootstrap must not plan {banned}"

    unexpected = types - BOOTSTRAP_ALLOWED_TYPES
    assert not unexpected, f"unexpected bootstrap types: {sorted(unexpected)}"

    addrs = "\n".join(sorted(_addresses(plan)))
    assert "aws_ecr_repository" in addrs
    assert "aws_s3_bucket" in addrs
    assert "aws_secretsmanager_secret" in addrs
    assert "aws_iam_role_policy" in addrs
    # Must not own/import the OIDC role or state bucket
    assert "github-actions-covenant-deploy" not in addrs or "aws_iam_role." not in addrs
    assert "covenant-tfstate-andy-568728209842" not in addrs
    assert "aws_secretsmanager_secret_version" not in types


@pytest.mark.skipif(not MAIN_PLAN_JSON, reason="set COVENANT_MAIN_PLAN_JSON for Gate D")
def test_main_plan_semantics():
    plan = _load_plan(MAIN_PLAN_JSON)
    add, change, destroy = _counts(plan)
    assert add > 0
    assert change == 0
    assert destroy == 0

    types = _types(plan)
    for banned in (
        "aws_nat_gateway",
        "aws_eip",
        "aws_dynamodb_table",
        "aws_ecr_repository",
        "aws_secretsmanager_secret",
        "aws_secretsmanager_secret_version",
        "aws_s3_bucket",
    ):
        assert banned not in types

    addrs = "\n".join(sorted(_addresses(plan)))
    assert "aws_s3files_file_system" in addrs
    assert "aws_service_discovery_http_namespace" in addrs or "service_connect" in addrs.lower() or "module.network" in addrs
    assert "aws_ecs_service" in addrs


@pytest.mark.skipif(not MAIN_PLAN_JSON, reason="set COVENANT_MAIN_PLAN_JSON for Gate D")
def test_main_digest_image_refs_exact():
    """When plan JSON embeds container image strings, require repo@sha256:64hex."""
    plan = _load_plan(MAIN_PLAN_JSON)
    blob = json.dumps(plan)
    # Soft probe: if any @sha256: appears, each must be exact 64 hex
    for match in re.finditer(r"@sha256:([0-9a-fA-F]+)", blob):
        digest = match.group(1).lower()
        assert DIGEST_RE.match(digest), f"malformed digest length/charset: {digest}"
