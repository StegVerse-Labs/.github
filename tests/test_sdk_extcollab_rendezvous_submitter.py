import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "submit_sdk_workspace_extcollab_resident_rendezvous.py"
spec = importlib.util.spec_from_file_location("extcollab_submitter", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

NODE = "SV-NODE-0123456789abcdef01234567"
NOW = datetime(2026, 9, 13, 20, 0, tzinfo=timezone.utc)


def test_invocation_binding_preserves_node_kv_authority_model():
    manifest = module.validate_manifest(module.load_json(ROOT / module.MANIFEST))
    assert manifest["task_id"] == module.TASK_ID
    assert manifest["cosv_task_vector"] == module.COSV
    assert manifest["physical_device_identity_gate"] == "NONE_PROHIBITED"
    assert manifest["target_node_role"] == "ROUTING_AND_RUNTIME_EVIDENCE_CORRELATION_ONLY"
    assert manifest["user_verification_authority"] == "KV/SKAP Vault"
    assert manifest["gateway_execution_authority"] == "NONE"
    assert manifest["request_grants_execution_authority"] is False
    assert manifest["request_grants_transition_authority"] is False
    assert manifest["request_grants_user_verification"] is False


def test_build_envelope_binds_goal_cosv_manifest_request_and_node_without_granting_authority():
    consumer = "sdk_workspace_external_collab_client_secret_reseal"
    manifest = module.validate_manifest(module.load_json(ROOT / module.MANIFEST))
    inner = module.validate_inner_request(consumer, module.load_json(ROOT / module.CONSUMERS[consumer]), manifest)
    envelope, context = module.build_envelope(
        consumer=consumer,
        node_ref=NODE,
        resident_request=inner,
        manifest=manifest,
        submitted_at=NOW,
    )
    assert envelope["target_node_ref"] == NODE
    assert envelope["consumer"] == consumer
    assert envelope["resident_request"] == inner
    assert envelope["authority_effect"] == "NONE_REQUEST_ONLY"
    assert re.fullmatch(r"transport-correlation:sha256:[0-9a-f]{64}", envelope["submitter_authorization_ref"])
    assert context["task_id"] == module.TASK_ID
    assert context["cosv_task_vector"] == module.COSV
    assert context["target_node_ref"] == NODE
    assert context["node_identity_role"] == "ROUTING_AND_RUNTIME_EVIDENCE_CORRELATION_ONLY"
    assert context["authority_effect"] == "NONE_CORRELATION_ONLY"


def test_submit_discovers_exact_consumer_and_records_pending_not_execution(tmp_path):
    for rel in [module.MANIFEST, *module.CONSUMERS.values()]:
        src = ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())

    seen = {}

    def getter(url):
        seen["get"] = url
        return {
            "schema": "stegverse.resident-rendezvous.discovery/v1",
            "state": "AVAILABLE",
            "consumer": "sdk_workspace_external_collab_consent_listener",
            "current_resident_request_id": "RESIDENT-EXEC-SDK-WORKSPACE-EXTCOLLAB-CONSENT-LISTENER-001",
            "target_node_ref": NODE,
            "expires_at": "2026-09-13T20:10:00+00:00",
            "gateway_execution_authority": "NONE",
            "credential_authority": "TV/TVC",
            "discovery_grants_authority": False,
            "authority_effect": "NONE_DISCOVERY_ONLY",
        }

    def poster(url, payload, *, authorization_ref):
        seen["post"] = url
        seen["payload"] = payload
        seen["authorization_ref"] = authorization_ref
        return {
            "schema": "stegverse.resident-rendezvous.store-result/v1",
            "state": "PENDING",
            "request_id": payload["request_id"],
            "resident_request_sha256": payload["resident_request_sha256"],
            "gateway_execution_authority": "NONE",
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE_REQUEST_ONLY",
        }

    receipt = module.submit(
        source_root=tmp_path,
        base_url="https://stegverse.org",
        consumer="sdk_workspace_external_collab_consent_listener",
        now=NOW,
        getter=getter,
        poster=poster,
    )
    assert "consumer=sdk_workspace_external_collab_consent_listener" in seen["get"]
    assert seen["post"].endswith("/api/resident-rendezvous/v1/requests")
    assert seen["authorization_ref"] == seen["payload"]["submitter_authorization_ref"]
    assert receipt["state"] == "REQUEST_STORED_PENDING_RESIDENT_CONSUMPTION"
    assert receipt["gateway_execution_authority"] == "NONE"
    assert receipt["workercoordinator_claim_fence_observed"] is False
    assert receipt["intr_admission_observed"] is False
    assert receipt["resident_execution_observed"] is False
    written = json.loads((tmp_path / module.RECEIPT).read_text(encoding="utf-8"))
    assert written == receipt


def test_arbitrary_consumer_and_device_identity_are_not_accepted():
    manifest = module.validate_manifest(module.load_json(ROOT / module.MANIFEST))
    try:
        module.validate_inner_request("arbitrary_shell", {}, manifest)
    except module.RendezvousSubmissionError as exc:
        assert "consumer not admitted" in str(exc)
    else:
        raise AssertionError("arbitrary consumer unexpectedly admitted")
