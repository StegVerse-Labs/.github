import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "scripts/consume_ibc_intr_resident_request.py"
spec = importlib.util.spec_from_file_location("consume_ibc_intr_resident_request", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def write_request(runtime: Path):
    path = runtime / module.REQUEST_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": "RESIDENT-EXEC-IBC-VERIFIED-INTR-ACK-001",
        "state": "REQUESTED",
        "task_id": module.TARGET_TASK,
        "mode": module.TARGET_MODE,
        "entrypoint": module.TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "requires_sovereign_node_marker": True,
        "requires_local_stegos_source": True,
        "observation_class": module.TARGET_OBSERVATION_CLASS,
        "authority_effect": "NONE_REQUEST_ONLY",
        "note": "test",
    }))


def write_stegos_root(root: Path):
    entrypoint = root / module.TARGET_ENTRYPOINT
    entrypoint.parent.mkdir(parents=True, exist_ok=True)
    entrypoint.write_text("print('fake')\n")
    for rel in module.EXPECTED_EVIDENCE:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith("ics23-verification.json"):
            value = {"result": "accepted", "proof_verified": True}
        elif rel.endswith("verified-classic-evidence.json"):
            value = {
                "classic_evidence_grants_transition_admission": False,
                "classic_evidence_grants_execution_authority": False,
                "classic_evidence_mints_custody_result": False,
            }
        else:
            value = {"ok": True}
        path.write_text(json.dumps(value))


def test_nonresident_context_cannot_manufacture_resident_execution(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    write_request(runtime)
    called = False

    def runner(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("runner must not execute without sovereign marker")

    receipt = module.consume(tmp_path, runtime, runner=runner, env={"PATH": "/usr/bin"})
    assert receipt["state"] == "SOVEREIGN_NODE_MARKER_REQUIRED"
    assert receipt["runtime_execution_attempted"] is False
    assert receipt["resident_runtime_execution_observed"] is False
    assert receipt["original_ibc_packet_relay_observed"] is False
    assert receipt["transition_admission_observed"] is False
    assert receipt["authority_effect"] == "NONE_FAIL_CLOSED"
    assert called is False


def test_sovereign_context_requires_successful_resident_artifact(tmp_path):
    runtime = tmp_path / "runtime"
    stegos = tmp_path / "stegos"
    runtime.mkdir()
    stegos.mkdir()
    write_request(runtime)
    write_stegos_root(stegos)

    def runner(command, **kwargs):
        output = Path(command[command.index("--output") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        artifact = {
            "observation_class": module.TARGET_OBSERVATION_CLASS,
            "resident_runtime_execution_observed": True,
            "original_ibc_packet_relay_observed": False,
            "transition_admission_observed": False,
            "application_execution_observed": False,
            "claim_or_fence_minted": False,
            "custody_result_minted": False,
            "credential_minted": False,
            "authority_effect": "NONE_RESIDENT_TRANSPORT_ONLY",
        }
        output.write_text(json.dumps(artifact))
        result = {
            "observation_class": module.TARGET_OBSERVATION_CLASS,
            "resident_runtime_execution_observed": True,
            "packet_id": "INTR-test",
            "receipt_hash": "sha256:" + "a" * 64,
        }
        return SimpleNamespace(returncode=0, stdout=json.dumps(result) + "\n", stderr="")

    receipt = module.consume(
        tmp_path,
        runtime,
        runner=runner,
        env={
            "PATH": "/usr/bin",
            "STEGVERSE_SOVEREIGN_NODE": "sovereign-node:test",
            "STEGVERSE_STEGOS_ROOT": str(stegos),
        },
    )
    assert receipt["state"] == "RESIDENT_INTR_ACK_CONSUMED"
    assert receipt["runtime_execution_attempted"] is True
    assert receipt["resident_runtime_execution_observed"] is True
    assert receipt["original_ibc_packet_relay_observed"] is False
    assert receipt["transition_admission_observed"] is False
    assert receipt["application_execution_observed"] is False
    assert receipt["claim_or_fence_minted"] is False
    assert receipt["workercoordinator_claim_fence_observed"] is False
    assert receipt["custody_result_minted"] is False
    assert receipt["credential_minted"] is False
    assert receipt["network_source_fetch_performed"] is False
    assert receipt["credential_authority"] == "TV/TVC"
    assert receipt["github_token_runtime_authority"] == "NONE"
    assert receipt["authority_effect"] == "NONE_RESIDENT_CONSUMPTION_ONLY"


def test_dispatch_refresh_and_targeted_bridge_wiring_is_present():
    dispatcher = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text()
    refresher = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
    targeted = (ROOT / "scripts/refresh_and_dispatch_resident_requests.py").read_text()

    assert '("ibc_verified_intr_ack", "scripts/consume_ibc_intr_resident_request.py")' in dispatcher
    assert '"SOVEREIGN_NODE_MARKER_REQUIRED", "RESIDENT_INTR_ACK_CONSUMED"' in dispatcher
    assert 'Path("scripts/consume_ibc_intr_resident_request.py")' in refresher
    assert '"ibc_verified_intr_ack"' in targeted
