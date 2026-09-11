import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "consume_stegsocials_bounded_intr_admission_request",
    ROOT / "scripts/consume_stegsocials_bounded_intr_admission_request.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


class _Response:
    def __init__(self, value):
        self._raw = json.dumps(value).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self._raw


def received_record():
    intent = {
        "schema": "stegsocials.bounded-group-intr-execution-intent.v1",
        "task_id": mod.TASK_ID,
        "stable_work_id": "work-social-001",
        "correlation_id": "corr-social-001",
        "requested_transition": "INGRESS_ADMITTED",
        "group_id": "group-001",
        "use_index": 1,
        "participant_approval_receipt_ref": "kv://approval/group-001",
        "state_ref": "kv://state/group-001",
        "content_ref": "kv://content/post-001",
        "content_hash": "sha256:" + "1" * 64,
        "platform": "linkedin",
        "account_ref": "account://stegverse",
        "intr_admission_receipt_ref": None,
        "tv_tvc_skap_session_receipt_ref": None,
        "request_grants_execution_authority": False,
        "provider_operation_authorized": False,
        "secret_material_present": False,
        "raw_credential_material": None,
    }
    return {
        "schema": "stegverse.universal-work-interlock/v1",
        "direction": "INGRESS",
        "state": "RECEIVED",
        "organization": "StegVerse-Labs",
        "repository": "StegVerse-Labs/StegSocials",
        "component": "bounded-group-social-publication",
        "next_owner": "INTERLOCK_INTR",
        "human_action_required": False,
        "admission_receipt_ref": None,
        "runtime_admission_observed": False,
        "work_id": intent["stable_work_id"],
        "correlation_id": intent["correlation_id"],
        "goal": "bounded social publication",
        "recorded_at": "2026-09-11T00:00:00Z",
        "source": {"type": "RUNTIME_EVENT"},
        "authority": {
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "heartbeat_granted_authority": False,
            "interlock_self_grants_authority": False,
            "intr_self_grants_authority": False,
        },
        "bounded_social_intent": intent,
    }


class StegSocialsResidentAdmissionTests(unittest.TestCase):
    def test_missing_input_is_non_authorizing_wait_state(self):
        with tempfile.TemporaryDirectory() as td:
            result = mod.consume(ROOT, Path(td), mod.DEFAULT_INPUT_REL, opener=lambda *a, **k: None)
        self.assertEqual(result["state"], "INPUT_NOT_MATERIALIZED")
        self.assertFalse(result["runtime_execution_attempted"])

    def test_exact_local_received_object_posts_and_binds_admission(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            received = runtime / "incoming/received.json"
            received.parent.mkdir(parents=True)
            received.write_text(json.dumps(received_record()), encoding="utf-8")
            builder = mod.load_builder(ROOT)
            payload, request = builder.build(received_record())
            auth = "TVC-EGRESS-AUTH-001"
            response = {
                "schema": "stegverse.stegsocials-bounded-intr-materialization-ingress/v1",
                "state": "INGRESS_ADMITTED",
                "materialization_id": request["materialization_id"],
                "request_hash": request["request_hash"],
                "payload_hash": request["payload_hash"],
                "transport_intent_hash": request["transport_intent_hash"],
                "work_id": payload["work_id"],
                "correlation_id": payload["correlation_id"],
                "group_id": payload["group_id"],
                "use_index": payload["use_index"],
                "content_hash": payload["content_hash"],
                "transport_origin": "TVC_RELAY_EGRESS",
                "transport_authorization_id": auth,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
                "admission_grants_publication_authority": False,
                "next_owner": "TV/TVC_SKAP_SESSION_MATERIALIZATION",
                "runtime_execution_attempted": False,
                "provider_operation_authorized": False,
                "credential_material_present": False,
                "receipt_hash": "sha256:" + "2" * 64,
            }
            pointer = {
                "schema": mod.INPUT_SCHEMA,
                "state": "READY",
                "task_id": mod.TASK_ID,
                "transport_origin": "TVC_RELAY_EGRESS",
                "received_record_path": "incoming/received.json",
                "ingress_url": "http://127.0.0.1:8788/intr/materialization",
                "tvc_relay_authorization_id": auth,
                "request_grants_execution_authority": False,
                "authority_effect": "NONE_INPUT_ONLY",
            }
            pointer["input_hash"] = mod.sha_uri(pointer)
            input_path = runtime / mod.DEFAULT_INPUT_REL
            input_path.parent.mkdir(parents=True)
            input_path.write_text(json.dumps(pointer), encoding="utf-8")

            result = mod.consume(ROOT, runtime, mod.DEFAULT_INPUT_REL, opener=lambda *a, **k: _Response(response))
            self.assertEqual(result["state"], "COMPLETED")
            self.assertTrue(result["authentic_shared_ingress_response_observed"])
            self.assertFalse(result["publication_authority_granted"])
            self.assertEqual(result["next_owner"], "TV/TVC_SKAP_SESSION_MATERIALIZATION")

    def test_non_loopback_ingress_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            received = runtime / "received.json"
            received.write_text(json.dumps(received_record()), encoding="utf-8")
            pointer = {
                "schema": mod.INPUT_SCHEMA,
                "state": "READY",
                "task_id": mod.TASK_ID,
                "transport_origin": "TVC_RELAY_EGRESS",
                "received_record_path": "received.json",
                "ingress_url": "https://example.com/intr/materialization",
                "tvc_relay_authorization_id": "AUTH-1",
                "request_grants_execution_authority": False,
                "authority_effect": "NONE_INPUT_ONLY",
            }
            pointer["input_hash"] = mod.sha_uri(pointer)
            p = runtime / mod.DEFAULT_INPUT_REL
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps(pointer), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                mod.consume(ROOT, runtime, mod.DEFAULT_INPUT_REL, opener=lambda *a, **k: None)


if __name__ == "__main__":
    unittest.main()
