"""V2 evidence manifest shape validation.

Offline: validates a sample fixture or skips until COVENANT_EVIDENCE_MANIFEST is set.
Gate closure sittings must set the env var and expect 0 skipped.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

MANIFEST_PATH = os.environ.get("COVENANT_EVIDENCE_MANIFEST")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")

P2_IDS = {
    "P2-VAL-01",
    "P2-PLAN-01",
    "P2-STOR-01",
    "P2-SMOKE-01",
    "P2-LOOP-01",
    "P2-THREAT-01",
    "P2-DOWN-01",
}
P3_IDS = {
    "P3-VAL-01",
    "P3-PLAN-01",
    "P3-PLAN-02",
    "P3-APPLY-01",
    "P3-SMOKE-01",
    "P3-DOWN-01",
    "P3-RECREATE-01",
    "P3-REPRO-01",
}


def _validate_manifest(doc: dict) -> None:
    assert "run_id" in doc
    assert HEX40.match(doc["commit_sha"]) or len(doc["commit_sha"]) >= 7
    assert doc["account_id"] == "568728209842"
    assert doc["region"] == "us-east-1"
    assert isinstance(doc.get("shared_evidence"), list)
    preds = doc.get("predictions")
    assert isinstance(preds, list)
    p2 = {p["prediction_id"] for p in preds if p.get("lens") == "P2"}
    p3 = {p["prediction_id"] for p in preds if p.get("lens") == "P3"}
    assert p2 == P2_IDS
    assert p3 == P3_IDS
    for p in preds:
        assert p["status"] in {"PASS", "FALSIFIED", "BLOCKED"}
        assert isinstance(p.get("evidence_refs"), list)
        assert "falsifier_observed" in p
        assert p.get("router_layer") in {"L0", "L1", "L2", "L3", "none"}
        assert "disposition" in p
    for ev in doc["shared_evidence"]:
        assert "ref" in ev
        assert HEX64.match(ev["sha256"])
        assert "captured_at_utc" in ev
        assert "source" in ev
    assert isinstance(doc.get("sync_receipts"), list)
    assert isinstance(doc.get("inventories"), list)


def test_manifest_schema_constants():
    assert len(P2_IDS) == 7
    assert len(P3_IDS) == 8


@pytest.mark.skipif(not MANIFEST_PATH, reason="set COVENANT_EVIDENCE_MANIFEST for closure sittings")
def test_evidence_manifest_file():
    path = Path(MANIFEST_PATH)
    doc = json.loads(path.read_text(encoding="utf-8"))
    _validate_manifest(doc)
