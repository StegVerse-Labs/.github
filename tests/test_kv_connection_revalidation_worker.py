from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "kv_connection_revalidation_worker",
    ROOT / "workers" / "kv_connection_revalidation_worker.py",
)
assert SPEC and SPEC.loader
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


class FakeStore:
    def __init__(self, assembly):
        self.registry = {
            "schema": "stegverse.kv.connection-assembly-registry/v1",
            "state": "DEGRADED",
            "authority_effect": "NONE",
            "assemblies": [dict(assembly)],
        }
        self.receipts = []

    def load_registry(self, _kv):
        return json.loads(json.dumps(self.registry))

    def upsert_assembly(self, _kv, assembly):
        self.registry["assemblies"] = [dict(assembly)]
        self.registry["state"] = assembly["compatibility_state"]
        return json.loads(json.dumps(self.registry))

    def persist_health_receipt(self, kv, receipt):
        self.receipts.append(dict(receipt))
        path = Path(kv) / "_System" / "Connections" / "Health" / "verified.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt), encoding="utf-8")
        return path


class FakeRevalidation:
    def __init__(self, reject=False):
        self.reject = reject
        self.calls = []

    def admit_revalidation(self, assembly, conformance, readback, *, required_after=None):
        self.calls.append((assembly, conformance, readback, required_after))
        if self.reject:
            raise ValueError("proof rejected")
        updated = dict(assembly)
        updated["compatibility_state"] = "VERIFIED"
        receipt = {
            "schema": "stegverse.kv.connection-health-receipt/v1",
            "assembly_id": assembly["assembly_id"],
            "observed_at": "2026-08-29T20:00:00Z",
            "provider_operation_authorized": False,
            "credential_material_present": False,
            "authority_effect": "NONE",
        }
        return updated, receipt


def make_env(tmp: Path):
    cvk = tmp / "cvk"
    kv = tmp / "kv"
    cvk.mkdir()
    kv.mkdir()
    conformance = tmp / "conformance.json"
    readback = tmp / "readback.json"
    conformance.write_text(json.dumps({"schema": "stegverse.kv.connection-conformance-proof/v1"}), encoding="utf-8")
    readback.write_text(json.dumps({"schema": "stegverse.kv.connection-readback-proof/v1"}), encoding="utf-8")
    return {
        "STEGVERSE_CVK_ROOT": str(cvk),
        "STEGVERSE_KV_ROOT": str(kv),
        "STEGVERSE_KV_CONNECTION_ASSEMBLY_ID": "kvcxn_test",
        "STEGVERSE_KV_CONNECTION_CONFORMANCE_PROOF": str(conformance),
        "STEGVERSE_KV_CONNECTION_READBACK_PROOF": str(readback),
        "STEGVERSE_KV_CONNECTION_REQUIRED_AFTER": "2026-08-29T19:00:00Z",
    }


def test_rejects_hosted_surface():
    result = worker.execute({"GITHUB_ACTIONS": "true"})
    assert result["state"] == "BLOCKED"
    assert result["transition_id"] == "HOSTED_SURFACE_REJECTED"
    assert result["connection_verified"] is False


def test_rejects_credential_environment():
    result = worker.execute({"GITHUB_TOKEN": "secret"})
    assert result["transition_id"] == "FORBIDDEN_CREDENTIAL_ENV"
    assert result["credential_material_present"] is False


def test_requires_bindings():
    result = worker.execute({})
    assert result["transition_id"] == "REVALIDATION_BINDINGS_REQUIRED"


def test_exact_assembly_required():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        env = make_env(root)
        store = FakeStore({"assembly_id": "kvcxn_other", "compatibility_state": "DEGRADED"})
        result = worker.execute(env, modules={"store": store, "revalidation": FakeRevalidation()})
        assert result["transition_id"] == "EXACT_CONNECTION_ASSEMBLY_NOT_FOUND"
        assert result["connection_verified"] is False


def test_canonical_revalidation_rejection_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        env = make_env(root)
        store = FakeStore({"assembly_id": "kvcxn_test", "compatibility_state": "DEGRADED"})
        result = worker.execute(env, modules={"store": store, "revalidation": FakeRevalidation(reject=True)})
        assert result["transition_id"] == "CONNECTION_REVALIDATION_REJECTED"
        assert result["connection_verified"] is False
        assert store.receipts == []


def test_success_persists_only_after_canonical_admission():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        env = make_env(root)
        store = FakeStore({"assembly_id": "kvcxn_test", "compatibility_state": "DEGRADED"})
        revalidation = FakeRevalidation()
        result = worker.execute(env, modules={"store": store, "revalidation": revalidation})
        assert result["state"] == "COMPLETED"
        assert result["transition_id"] == "KV_CONNECTION_REVALIDATION_COMPLETED"
        assert result["connection_verified"] is True
        assert result["provider_network_access_performed"] is False
        assert result["provider_operation_authorized"] is False
        assert result["credential_material_present"] is False
        assert result["proof_manufactured"] is False
        assert result["required_after_enforced"] is True
        assert store.registry["assemblies"][0]["compatibility_state"] == "VERIFIED"
        assert len(store.receipts) == 1
        assert revalidation.calls[0][3] == "2026-08-29T19:00:00Z"
