"""Topology completeness checks against Terraform plan JSON or HCL markers.

Offline: assert prohibited resource types are absent from module sources.
With a main plan JSON (Gate D): assert Phase-2 topology addresses exist and
NAT/EIP/DynamoDB/state/data bucket ownership are absent from the main plan.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TF_ROOT = REPO_ROOT / "infra" / "terraform"
MAIN_PLAN_JSON = os.environ.get("COVENANT_MAIN_PLAN_JSON")


def _iter_tf_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.tf") if ".terraform" not in p.parts]


def _load_plan(path: str | Path) -> dict:
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def _planned_addresses(plan: dict) -> set[str]:
    addrs: set[str] = set()
    for rc in plan.get("resource_changes", []):
        addr = rc.get("address")
        if addr:
            addrs.add(addr)
    return addrs


def _planned_types(plan: dict) -> set[str]:
    types: set[str] = set()
    for rc in plan.get("resource_changes", []):
        t = rc.get("type")
        if t:
            types.add(t)
    return types


def test_main_root_does_not_call_ecr_or_secrets_modules():
    main_tf = (TF_ROOT / "main.tf").read_text(encoding="utf-8")
    assert 'module "ecr"' not in main_tf
    assert 'module "secrets"' not in main_tf
    assert 'module "network"' in main_tf
    assert 'module "storage"' in main_tf
    assert 'module "ecs"' in main_tf
    assert 'module "iam"' in main_tf


def test_hcl_forbids_nat_eip_dynamodb_in_main_modules():
    prohibited = (
        "aws_nat_gateway",
        "aws_eip",
        "aws_dynamodb_table",
    )
    for path in _iter_tf_files(TF_ROOT):
        if "bootstrap" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for token in prohibited:
            assert token not in text, f"{token} found in {path}"


@pytest.mark.skipif(not MAIN_PLAN_JSON, reason="set COVENANT_MAIN_PLAN_JSON for Gate D")
def test_main_plan_topology_completeness():
    plan = _load_plan(MAIN_PLAN_JSON)
    types = _planned_types(plan)
    addrs = _planned_addresses(plan)

    for banned in (
        "aws_nat_gateway",
        "aws_eip",
        "aws_dynamodb_table",
        "aws_s3_bucket",  # data/state buckets must not be main-owned
        "aws_ecr_repository",
        "aws_secretsmanager_secret",
        "aws_secretsmanager_secret_version",
    ):
        assert banned not in types, f"main plan must not own {banned}"

    # Session-scoped topology signals (module addresses)
    joined = "\n".join(sorted(addrs))
    for needle in (
        "module.network",
        "module.ecs",
        "module.storage",
        "module.iam",
        "aws_s3files_file_system",
        "aws_lb",
        "aws_ecs_service",
    ):
        assert needle in joined, f"missing topology marker {needle}"
