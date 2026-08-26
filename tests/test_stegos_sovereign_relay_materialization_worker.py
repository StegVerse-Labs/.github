import io
import json
from pathlib import Path

import pytest

from workers import stegos_sovereign_relay_bridge as bridge
from workers import stegos_sovereign_relay_materialization_worker as worker


def _make_stegos_root(root: Path) -> Path:
    for rel in bridge.REQUIRED_STEGOS_SURFACES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n", encoding="utf-8")
    return root


def test_find_stegos_root_prefers_explicit_complete_surface(tmp_path):
    control = tmp_path / "control"
    control.mkdir()
    stegos = _make_stegos_root(tmp_path / "source" / "StegOS")
    found = bridge.find_stegos_root(control, {"STEGVERSE_STEGOS_ROOT": str(stegos)})
    assert found == stegos.resolve()


def test_find_stegos_root_rejects_incomplete_surface(tmp_path):
    control = tmp_path / "control"
    control.mkdir()
    partial = tmp_path / "StegOS"
    partial.mkdir()
    assert bridge.find_stegos_root(control, {"STEGVERSE_STEGOS_ROOT": str(partial)}) is None


def test_process_adapter_and_registry_fragments_preserve_authority_boundaries():
    root = Path(__file__).resolve().parents[1]
    adapter = json.loads((root / "control/process-worker-adapters.d/stegos-sovereign-relay-materialization-001.json").read_text())
    registry = json.loads((root / "control/worker-registry.d/stegos-sovereign-relay-materialization-001.json").read_text())
    row = adapter["adapters"][0]
    assert row["adapter_ref"] == "process:stegos-sovereign-relay-materialization-v1"
    assert row["env_allowlist"] == ["STEGVERSE_STEGOS_ROOT", "STEGVERSE_RELAY_RUNTIME_BASE"]
    task = registry["tasks"][0]
    assert task["state"] == "HANDOFF_READY"
    assert task["admission"]["authority_domain"] == "INDEPENDENT_TASK_CONTROL"
    assert task["admission"]["heartbeat_grants_execution_authority"] is False
    assert task["admission"]["fresh_fence_required"] is True
    assert registry["credential_authority"] == "TV/TVC"
    assert registry["github_token_required"] is False


def test_executable_handoff_request_is_non_authorizing_controlled_activation():
    root = Path(__file__).resolve().parents[1]
    handoff = json.loads((root / "handoffs/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json").read_text())
    req = handoff["execution"]["relay_activation_request"]
    assert handoff["state"] == "HANDOFF_READY"
    assert handoff["authority"]["heartbeat_grants_execution_authority"] is False
    assert req["admission_state"] == "ADMITTED"
    assert req["evidence_class"] == "CONTROLLED_SOVEREIGN_RUNTIME_ACTIVATION"
    assert req["production_capacity_deficit_claimed"] is False
    assert req["credential_authority"] == "TV/TVC"
    assert req["route_admitted"] is False
    assert req["outbound_egress_authorized"] is False


def test_worker_completes_only_on_full_lease_open_evidence(tmp_path, monkeypatch):
    fake_root = tmp_path / "repo"
    fake_root.mkdir()
    stegos = _make_stegos_root(tmp_path / "StegOS")
    receipt = fake_root / "receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json"
    monkeypatch.setattr(worker, "ROOT", fake_root)
    monkeypatch.setattr(worker, "RECEIPT", receipt)
    monkeypatch.setattr(worker, "find_stegos_root", lambda root: stegos)
    monkeypatch.setattr(worker, "runtime_base", lambda: tmp_path / "runtime")
    monkeypatch.setattr(worker, "materialize_relay", lambda **kwargs: {
        "evidence": {
            "lease_state": "LEASE_OPEN",
            "runtime_instantiated": True,
            "local_identity_verified": True,
            "bounded_rendezvous_open": True,
            "public_identity_verified": True,
            "route_admitted": False,
            "outbound_egress_executed": False,
            "credential_authority": "TV/TVC",
            "credential_material_present": False,
            "canonical_transition_committed": False,
        },
        "runtime": {"runtime_id": "runtime-1"},
        "rendezvous": {"rendezvous_id": "rv-1"},
    })
    handoff = {
        "execution": {
            "required_capabilities": ["runtime_observation", "bounded_process_execution", "sovereign_relay_materialization"],
            "allowed_paths": ["receipts/stegos-sovereign-relay/**"],
            "relay_activation_request": {"schema": "stegverse.sovereign-relay-materialization-request/v1"},
        }
    }
    invocation = {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 32,
        "task": {"task_id": worker.TASK_ID, "claim_id": "claim-22", "heartbeat_timing": {"fencing_token": 22}},
        "handoff": handoff,
    }
    stdin = io.StringIO(json.dumps(invocation))
    stdout = io.StringIO()
    monkeypatch.setattr("sys.stdin", stdin)
    monkeypatch.setattr("sys.stdout", stdout)
    assert worker.main() == 0
    result = json.loads(receipt.read_text())
    assert result["state"] == "COMPLETED"
    assert result["transition_id"] == "SOVEREIGN_RELAY_LEASE_OPEN"
    assert result["relay_lease_open"] is True
    assert result["route_admitted"] is False
    assert result["outbound_egress_executed"] is False


def test_worker_stays_active_when_stegos_source_missing(tmp_path, monkeypatch):
    fake_root = tmp_path / "repo"
    fake_root.mkdir()
    receipt = fake_root / "receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json"
    monkeypatch.setattr(worker, "ROOT", fake_root)
    monkeypatch.setattr(worker, "RECEIPT", receipt)
    monkeypatch.setattr(worker, "find_stegos_root", lambda root: None)
    invocation = {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 32,
        "task": {"task_id": worker.TASK_ID, "claim_id": "claim-22", "heartbeat_timing": {"fencing_token": 22}},
        "handoff": {"execution": {"required_capabilities": ["runtime_observation", "bounded_process_execution", "sovereign_relay_materialization"], "allowed_paths": ["receipts/stegos-sovereign-relay/**"]}},
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(invocation)))
    monkeypatch.setattr("sys.stdout", io.StringIO())
    assert worker.main() == 0
    result = json.loads(receipt.read_text())
    assert result["state"] == "ACTIVE"
    assert result["transition_id"] == "STEGOS_RELAY_SOURCE_MATERIALIZATION_REQUIRED"
    assert result["blocker"]["physical_additional_machine_required"] is False
    assert result["blocker"]["human_action_required"] is False
