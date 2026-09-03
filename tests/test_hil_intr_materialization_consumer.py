from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "consume_hil_intr_materialization_request",
    ROOT / "scripts/consume_hil_intr_materialization_request.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def request(materialization_id: str = "INTR-MAT-" + "a" * 24) -> dict:
    body = {
        "schema": "stegverse.universal-intr-materialization-request/v1",
        "materialization_id": materialization_id,
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": "sha256:" + "1" * 64,
        "operation_id": "HIL-UPLOAD-TEST-001",
        "packet_id": "INTR-" + "b" * 24,
        "payload_hash": "sha256:" + "2" * 64,
        "payload_ref": "opaque://hil/HIL-UPLOAD-TEST-001",
        "destination": {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "HIL:Ingress"},
        "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
        "downstream_owner_ref": "StegVerse-Labs/.github#246",
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False,
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    return {**body, "request_hash": mod.digest_uri(body)}


def ingress_receipt(req: dict) -> dict:
    return {
        "schema": "stegverse.hil-intr-materialization-ingress/v1",
        "state": "INGRESS_ADMITTED",
        "materialization_id": req["materialization_id"],
        "request_hash": req["request_hash"],
        "transport_intent_hash": req["transport_intent_hash"],
        "payload_hash": req["payload_hash"],
        "operation_id": req["operation_id"],
        "packet_id": req["packet_id"],
        "runtime_execution_attempted": False,
        "receiver_readiness_claimed": False,
        "hil_custody_claimed": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_INGRESS_ONLY",
    }


def prepare(base: Path) -> tuple[Path, Path, dict]:
    source = base / "source"
    runtime = base / "runtime"
    source.mkdir()
    (runtime / mod.REQUEST_DIR_REL).mkdir(parents=True)
    (runtime / mod.INGRESS_RECEIPT_DIR_REL).mkdir(parents=True)
    req = request()
    (runtime / mod.REQUEST_DIR_REL / "request.json").write_text(json.dumps(req) + "\n", encoding="utf-8")
    (runtime / mod.INGRESS_RECEIPT_DIR_REL / f"{req['materialization_id']}.json").write_text(json.dumps(ingress_receipt(req)) + "\n", encoding="utf-8")
    return source, runtime, req


def fake_materializer(*, source, intake_runtime, request, ingress_receipt, env):
    execution_runtime = intake_runtime / "esrl-hil-runtime" / "lease-1"
    (execution_runtime / "scripts").mkdir(parents=True)
    (execution_runtime / mod.TARGET_ENTRYPOINT).write_text("# target\n", encoding="utf-8")
    return {
        "runtime_root": execution_runtime,
        "evidence": {
            "schema": "stegverse.hil-esrl-runtime-materialization/v1",
            "state": "LEASE_OPEN",
            "lease_id": "HIL-ESRL-test",
            "lease_state": "LEASE_OPEN",
            "source_receipt_id": "sha256:" + "f" * 64,
            "runtime_instantiated": True,
            "local_identity_verified": True,
            "hil_public_https_rendezvous_observed": False,
            "public_gateway_readiness_verified": False,
            "public_gateway_origin": None,
            "public_observation_is_downstream_optional": True,
            "same_device_execution_required": True,
            "requires_other_machine": False,
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE_RUNTIME_MATERIALIZATION_ONLY",
        },
    }


class HILInTrMaterializationConsumerTests(unittest.TestCase):
    def test_valid_request_is_non_authorizing_and_g18_independent(self) -> None:
        value = request()
        mod.validate_request(value)
        self.assertFalse(value["request_grants_execution_authority"])
        self.assertFalse(value["claim_or_fence_minted"])
        self.assertEqual(value["credential_authority"], "TV/TVC")
        self.assertFalse(value["always_on_receiver_required"])
        self.assertFalse(value["second_user_device_required"])

    def test_missing_ingress_receipt_fails_closed_before_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"; runtime = base / "runtime"
            source.mkdir(); (runtime / mod.REQUEST_DIR_REL).mkdir(parents=True)
            req = request(); (runtime / mod.REQUEST_DIR_REL / "request.json").write_text(json.dumps(req) + "\n")
            calls = []
            def materializer(**kwargs):
                calls.append(kwargs); return {}
            result = mod.consume_all(source, runtime, runtime_materializer=materializer)
            self.assertEqual(result["results"][0]["state"], "REQUEST_REJECTED")
            self.assertIn("ingress_receipt_missing", result["results"][0]["reason"])
            self.assertEqual(calls, [])

    def test_consumer_materializes_esrl_runtime_before_targeted_executor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime, _ = prepare(Path(td))
            calls = []
            def runner(command, **kwargs):
                calls.append((command, kwargs))
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            result = mod.consume_all(source, runtime, runner=runner, env={"GITHUB_TOKEN": "forbidden"}, runtime_materializer=fake_materializer)
            self.assertEqual(result["state"], "PROCESSED")
            self.assertEqual(result["runtime_execution_attempt_count"], 1)
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertIn("--task-id", command)
            self.assertIn(mod.TARGET_TASK, command)
            self.assertIn("esrl-hil-runtime", " ".join(command))
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
            saved = json.loads((runtime / mod.RECEIPT_DIR_REL / f"{request()['materialization_id']}.json").read_text())
            self.assertTrue(saved["esrl_runtime_instantiated"])
            self.assertTrue(saved["esrl_local_identity_verified"])
            self.assertEqual(saved["esrl_lease_state"], "LEASE_OPEN")
            self.assertFalse(saved["hil_public_https_rendezvous_observed"])
            self.assertFalse(saved["public_gateway_readiness_verified"])
            self.assertIsNone(saved["public_gateway_origin"])
            self.assertTrue(saved["public_observation_is_downstream_optional"])
            self.assertTrue(saved["same_device_execution_required"])
            self.assertFalse(saved["requires_other_machine"])
            self.assertFalse(saved["claim_or_fence_minted_by_consumer"])

    def test_consumer_rejects_non_open_local_lease(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime, _ = prepare(Path(td))
            def bad_materializer(**kwargs):
                value = fake_materializer(**kwargs)
                value["evidence"]["state"] = "LOCAL_READY"
                value["evidence"]["lease_state"] = "LOCAL_READY"
                value["evidence"]["hil_public_https_rendezvous_observed"] = False
                value["evidence"]["public_gateway_readiness_verified"] = False
                return value
            result = mod.consume_all(source, runtime, runtime_materializer=bad_materializer)
            self.assertEqual(result["results"][0]["state"], "REQUEST_REJECTED")
            self.assertIn("esrl_lease_not_open", result["results"][0]["reason"])

    def test_successful_materialization_is_not_blindly_reexecuted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime, _ = prepare(Path(td))
            calls = []
            def runner(command, **kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            first = mod.consume_all(source, runtime, runner=runner, runtime_materializer=fake_materializer)
            second = mod.consume_all(source, runtime, runner=runner, runtime_materializer=fake_materializer)
            self.assertEqual(first["runtime_execution_attempt_count"], 1)
            self.assertEqual(second["runtime_execution_attempt_count"], 0)
            self.assertEqual(second["results"][0]["state"], "ALREADY_CONSUMED_SUCCESS")
            self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()


    def test_consumer_rejects_other_machine_runtime_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime, _ = prepare(Path(td))
            def bad_materializer(**kwargs):
                value = fake_materializer(**kwargs)
                value["evidence"]["requires_other_machine"] = True
                value["evidence"]["same_device_execution_required"] = True
                return value
            result = mod.consume_all(source, runtime, runtime_materializer=bad_materializer)
            self.assertEqual(result["results"][0]["state"], "REQUEST_REJECTED")
            self.assertIn("esrl_same_device_invariant_not_proven", result["results"][0]["reason"])
