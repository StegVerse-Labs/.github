from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_manifest_runner_carries_immutable_nonce():
    source = read("scripts/run_stegbrowser_manifest_bound_runtime.py")
    assert NONCE in source
    assert "STEGVERSE_STEGBROWSER_INVOCATION_NONCE" in source
    assert '"invocation_request_nonce":NONCE' in source


def test_materialization_consumer_preserves_immutable_nonce():
    source = read("workers/stegbrowser_intr_materialization_consumer.py")
    assert 'child["STEGVERSE_STEGBROWSER_INVOCATION_NONCE"] = NONCE' in source


def test_org_ingress_hash_binds_nonce_to_claim_fence_packet():
    source = read("workers/stegbrowser_manifest_intr_ingress.py")
    assert NONCE in source
    assert "immutable invocation nonce missing or mismatched" in source
    assert '"invocation_request_nonce": NONCE' in source
    assert '"invocation_request_nonce":NONCE' in source
    assert '"workercoordinator_claim_fence_observed":True' in source


def test_runtime_projection_fails_closed_on_nonce_mismatch():
    source = read("scripts/run_stegbrowser_runtime_consumption_reusable.py")
    assert NONCE in source
    assert 'result.get("invocation_request_nonce") != NONCE' in source
    assert "workercoordinator_claim_fence_invocation_nonce_mismatch" in source
    assert '"invocation_request_nonce":NONCE' in source
