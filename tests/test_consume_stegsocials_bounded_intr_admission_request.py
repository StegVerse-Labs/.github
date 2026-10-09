import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "consume_stegsocials_bounded_intr_admission_request",
    ROOT / "scripts/consume_stegsocials_bounded_intr_admission_request.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


def _no_network(*_args, **_kwargs):
    raise AssertionError("in-process admission must not open a socket or listener")


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
            result = mod.consume(ROOT, Path(td), mod.DEFAULT_INPUT_REL, admit=_no_network)
        self.assertEqual(result["state"], "INPUT_NOT_MATERIALIZED")
        self.assertFalse(result["runtime_execution_attempted"])

    def _write_pointer(self, runtime, auth="TVC-EGRESS-AUTH-001"):
        received = runtime / "incoming/received.json"
        received.parent.mkdir(parents=True)
        received.write_text(json.dumps(received_record()), encoding="utf-8")
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
        return pointer

    def test_absent_listener_does_not_block_in_process_write_once_admission(self):
        with tempfile.TemporaryDirectory() as td, \
                patch("urllib.request.urlopen", _no_network), patch("socket.socket", _no_network), \
                patch("socket.create_connection", _no_network):
            runtime = Path(td)
            self._write_pointer(runtime)
            _payload, request = mod.load_builder(ROOT).build(received_record())
            result = mod.consume(ROOT, runtime, mod.DEFAULT_INPUT_REL)
            self.assertEqual(result["state"], "INGRESS_ADMITTED")
            self.assertEqual(result["request_hash"], request["request_hash"])
            self.assertTrue(result["in_process_write_once_admission"])
            self.assertFalse(result["receiver_liveness_predicate"])
            self.assertTrue(result["ingress_write_once_persisted"])
            queued = Path(result["ingress_queue_ref"])
            self.assertTrue(queued.is_file())
            self.assertEqual(json.loads(queued.read_text(encoding="utf-8"))["request_hash"], request["request_hash"])
            receipt = json.loads(Path(result["ingress_receipt_ref"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertEqual(receipt["receipt_hash"], result["ingress_receipt_hash"])
            self.assertFalse(result["publication_authority_granted"])
            self.assertEqual(result["next_owner"], "TV/TVC_SKAP_SESSION_MATERIALIZATION")

    def test_ingress_admitted_never_claims_downstream_completion(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            self._write_pointer(runtime)
            result = mod.consume(ROOT, runtime, mod.DEFAULT_INPUT_REL)
            self.assertNotEqual(result["state"], "COMPLETED")
            self.assertFalse(result["runtime_execution_attempted"])
            self.assertFalse(result["downstream_execution_observed"])
            self.assertFalse(result["provider_execution_attempted"])
            receipt = json.loads(Path(result["ingress_receipt_ref"]).read_text(encoding="utf-8"))
            self.assertFalse(receipt["runtime_execution_attempted"])
            self.assertFalse(receipt["provider_operation_authorized"])

    def test_same_request_admitted_twice_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            pointer = self._write_pointer(runtime)
            first = mod.consume(ROOT, runtime, mod.DEFAULT_INPUT_REL)
            queued = Path(first["ingress_queue_ref"]).read_bytes()
            receipt = Path(first["ingress_receipt_ref"]).read_bytes()
            second = mod.consume(ROOT, runtime, mod.DEFAULT_INPUT_REL)
            self.assertEqual(second["state"], "ALREADY_CONSUMED")
            self.assertEqual(second["request_hash"], first["request_hash"])
            _payload, request = mod.load_builder(ROOT).build(received_record())
            again = mod.admit_exact(request, runtime, pointer["tvc_relay_authorization_id"], admit=mod.load_admission(ROOT))
            self.assertEqual(again["receipt_hash"], first["ingress_receipt_hash"])
            self.assertEqual(Path(first["ingress_queue_ref"]).read_bytes(), queued)
            self.assertEqual(Path(first["ingress_receipt_ref"]).read_bytes(), receipt)

    def test_malformed_request_is_refused_typed_without_effect(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            self._write_pointer(runtime)
            builder = mod.load_builder(ROOT)
            real_build = builder.build

            def tampered_build(record):
                payload, request = real_build(record)
                return payload, {**request, "request_hash": "sha256:" + "0" * 64}

            builder.build = tampered_build
            with patch.object(mod, "load_builder", return_value=builder):
                with self.assertRaisesRegex(RuntimeError, "^intr_admission_refused:"):
                    mod.consume(ROOT, runtime, mod.DEFAULT_INPUT_REL)
            self.assertFalse((runtime / "intr-materialization").exists())
            self.assertFalse((runtime / "receipts/sovereign-network/stegsocials-bounded-intr-ingress").exists())
            self.assertFalse((runtime / mod.DEFAULT_RECEIPT_REL).exists())

    def test_consumer_opens_no_loopback_connection(self):
        source = (ROOT / "scripts/consume_stegsocials_bounded_intr_admission_request.py").read_text(encoding="utf-8")
        for forbidden in ("urlopen", "urllib.request", "http.client", "import socket", "socket.", "timeout=", "Request("):
            self.assertNotIn(forbidden, source)
        self.assertIn("workers/stegsocials_bounded_intr_ingress.py", source)
        self.assertIn("transport_validator=hil.validate_transport_headers", source)

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
                mod.consume(ROOT, runtime, mod.DEFAULT_INPUT_REL, admit=_no_network)


if __name__ == "__main__":
    unittest.main()
