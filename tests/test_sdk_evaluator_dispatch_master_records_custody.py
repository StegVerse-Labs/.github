import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dispatch_resident_execution_requests",
    ROOT / "scripts" / "dispatch_resident_execution_requests.py",
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(module)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha256_uri(value):
    raw = value if isinstance(value, bytes) else canonical_json(value).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def test_sdk_evaluator_dispatch_visit_enters_existing_master_records_custody(tmp_path, monkeypatch):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    (source / "workers").mkdir(parents=True)
    consumer = runtime / "scripts" / "consume_sdk_evaluator_governance_posture_request.py"
    consumer.parent.mkdir(parents=True)
    consumer.write_text("# placeholder\n")
    request_path = runtime / module.SDK_EVALUATOR_REQUEST_REL
    request_path.parent.mkdir(parents=True)
    request_path.write_text(json.dumps({
        "request_id": "RESIDENT-EXEC-SDK-EVALUATOR-GOVERNANCE-POSTURE-RUNTIME-PROOF-001",
        "task_id": "SDK-EVALUATOR-GOVERNANCE-POSTURE-RUNTIME-PROOF-001",
    }))

    captured = {}
    fake = types.ModuleType("canonical_state_transition_custody")
    fake.sha256_uri = sha256_uri

    def build_state_receipt(**kwargs):
        captured["build"] = kwargs
        return {"schema": "stegverse.canonical-state-transition-receipt/v1", **kwargs}

    def submit_state_receipt(receipt):
        captured["receipt"] = receipt
        digest = sha256_uri(receipt).split(":", 1)[1]
        return {
            "state": "RECORDED",
            "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": digest,
            "reconstructed_receipt_sha256": digest,
            "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
        }

    fake.build_state_receipt = build_state_receipt
    fake.submit_state_receipt = submit_state_receipt
    monkeypatch.setitem(sys.modules, "canonical_state_transition_custody", fake)

    class Completed:
        returncode = 0
        stdout = json.dumps({
            "state": "MASTER_RECORDS_VALIDATION_PENDING_OR_FAILED",
            "posture_bound_execution": True,
            "sdk_resolved_posture": False,
        }) + "\n"

    receipt = module.dispatch(
        source,
        runtime,
        runner=lambda *args, **kwargs: Completed(),
        env={},
        only_consumers=("sdk_evaluator_governance_posture",),
    )

    assert receipt["state"] == "DISPATCH_COMPLETE"
    custody = receipt["sdk_evaluator_dispatch_master_records"]
    assert custody["state"] == "RECORDED"
    assert custody["reconstruction_status"] == "PASS"
    assert custody["required_evidence_validation_status"] == "PASS"
    assert custody["receipt_sha256"] == custody["reconstructed_receipt_sha256"]

    build = captured["build"]
    assert build["transition_outcome"] == "OBSERVED"
    assert build["subject_or_correlation_id"] == "SDK-EVALUATOR-GOVERNANCE-POSTURE-RUNTIME-PROOF-001"
    evidence = build["transition_evidence"]
    assert evidence["transition"] == "RESIDENT_REQUEST_DISPATCH_VISIT"
    assert evidence["selector"] == "sdk_evaluator_governance_posture"
    assert evidence["attempted"] is True
    assert evidence["request_id"] == "RESIDENT-EXEC-SDK-EVALUATOR-GOVERNANCE-POSTURE-RUNTIME-PROOF-001"
    assert evidence["dispatch_grants_authority"] is False

    required = build["required_evidence_manifest"]
    assert len(required) == 1
    item = required[0]
    assert item["evidence_type"] == "RESIDENT_REQUEST_DISPATCH_SELECTOR_VISIT"
    assert item["origin_transition_id"] == build["transition_id"]
    assert item["encoding"] == "canonical-json"
    assert item["sha256"] == sha256_uri(item["content"]).split(":", 1)[1]
    assert item["content"]["attempted"] is True
    assert item["content"]["machine_result"]["posture_bound_execution"] is True
