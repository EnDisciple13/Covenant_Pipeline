"""S3 Files contract assertions (HCL offline + main plan Gate D)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
STORAGE = REPO_ROOT / "infra" / "terraform" / "modules" / "storage" / "main.tf"
ECS = REPO_ROOT / "infra" / "terraform" / "modules" / "ecs" / "main.tf"
MAIN_PLAN_JSON = os.environ.get("COVENANT_MAIN_PLAN_JSON")


def test_storage_hcl_encodes_s3files_contract():
    text = STORAGE.read_text(encoding="utf-8")
    assert "aws_s3files_file_system" in text
    assert "aws_s3files_access_point" in text
    assert "aws_s3files_mount_target" in text
    assert "posix_user" in text
    assert "uid" in text and "gid" in text
    assert "0" in text
    assert "2049" in text
    # AWS-owned default: no kms_key_id forced
    assert "kms_key_id" not in text


def test_ecs_hcl_mounts_app_data_ro_rw():
    text = ECS.read_text(encoding="utf-8")
    assert "s3files_volume_configuration" in text or "s3files" in text.lower()
    assert "/app/data" in text
    assert "read_only" in text.lower() or "readOnly" in text or "readonly" in text.lower()


@pytest.mark.skipif(not MAIN_PLAN_JSON, reason="set COVENANT_MAIN_PLAN_JSON for Gate D")
def test_main_plan_s3files_shape():
    with open(MAIN_PLAN_JSON, encoding="utf-8") as fh:
        plan = json.load(fh)
    types = {rc.get("type") for rc in plan.get("resource_changes", [])}
    assert "aws_s3files_file_system" in types
    assert "aws_s3files_access_point" in types
    assert "aws_s3files_mount_target" in types
    # Data bucket remains outside main
    assert "aws_s3_bucket" not in types
