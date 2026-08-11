from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile

from heartbeat_runtime.blocker_policy import validate_worker_response_blocker
from heartbeat_runtime.engine_v4 import HeartbeatRuntime

ROOT = Path(__file__).resolve().parents[1]
RECOVERY_ID = "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28"
PARENT_ID = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_recovery_worker_is_unique_and_cannot_match_parent() -> None:
    fragment = load(ROOT / "control" / "worker-registry.d" / "ecosystem-chat-orphan-recovery-hb28.json")
    recovery = fragment["workers"][0]
    registry = load(ROOT / "control" / "worker-registry.json")
    inference = next(w for w in registry["workers"] if w["worker_id"] == "ecosystem-chat-sovereign-inference-worker")
    recovery_handoff = load(ROOT / "handoffs" / "generated" / f"{RECOVERY_ID}.json")
    parent_handoff = load(ROOT / "handoffs" / f"{PARENT_ID}.json")
    recovery_required = set(recovery_handoff["execution"]["required_capabilities"])
    parent_required = set(parent_handoff["execution"]["required_capabilities"])
    assert recovery_required == {"orphan_lifecycle_reconstruction"}
    assert recovery_required.issubset(set(recovery["capabilities"]))
    assert not recovery_required.issubset(set(inference["capabilities"]))
    assert parent_required.issubset(set(inference["capabilities"]))
    assert not parent_required.issubset(set(recovery["capabilities"]))
    assert fragment["github_token_required"] is False
    assert fragment["parent_task_execution_authority"] is False


def test_bounded_authorization_file_releases_only_matching_recovery_scope() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "handoffs").mkdir(parents=True)
        (root / "authorizations").mkdir(parents=True)
        handoff_ref = "handoffs/recovery.json"
        auth_ref = "authorizations/recovery.json"
        handoff = {
            "authority": {"authority_source": "source", "heartbeat_grants_execution_authority": False},
            "execution": {"required_capabilities": ["orphan_lifecycle_reconstruction"], "allowed_paths": ["receipts/**"], "allowed_services": []},
            "activation": {"executor_binding": "AUTHORIZED", "authorization_ref": auth_ref},
        }
        auth = {
            "schema": "stegverse.bounded-worker-authorization/v0.1",
            "state": "ADMITTED",
            "task_id": RECOVERY_ID,
            "authority_source": "source",
            "allowed_capabilities": ["orphan_lifecycle_reconstruction"],
            "allowed_paths": ["receipts/**"],
            "allowed_services": [],
            "heartbeat_grants_execution_authority": False,
            "availability_grants_execution_authority": False,
            "github_token_required": False,
        }
        (root / handoff_ref).write_text(json.dumps(handoff), encoding="utf-8")
        (root / auth_ref).write_text(json.dumps(auth), encoding="utf-8")
        runtime = HeartbeatRuntime(root)
        task = {"task_id": RECOVERY_ID, "handoff_ref": handoff_ref}
        assert runtime._bounded_file_dependency_released(f"file:{auth_ref}", task) is True
        auth["github_token_required"] = True
        (root / auth_ref).write_text(json.dumps(auth), encoding="utf-8")
        assert runtime._bounded_file_dependency_released(f"file:{auth_ref}", task) is False


def test_tc_tvc_wrapper_normalizes_legacy_blocked_response_to_current_policy() -> None:
    spec = importlib.util.spec_from_file_location("tctvc", ROOT / "workers" / "ecosystem_chat_tc_tvc_route_worker.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    response = {
        "state": "BLOCKED",
        "expected_next_transition": "SOVEREIGN_LIVE_MODEL_ENDPOINT_VERIFIED",
        "blocker": {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "local capsule absent",
            "solution_required": True,
            "next_solution_action": "materialize local capsule and retry",
            "github_token_required": False,
        },
    }
    normalized = module.normalize_blocker_contract(response)
    validate_worker_response_blocker(normalized)
    assert normalized["blocker"]["workaround_candidates"] == ["materialize local capsule and retry"]
    assert normalized["github_token_required"] is False
