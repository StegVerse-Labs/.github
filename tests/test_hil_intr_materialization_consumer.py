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


class HILInTrMaterializationConsumerTests(unittest.TestCase):
    def test_valid_request_is_non_authorizing_and_g18_independent(self) -> None:
        value = request()
        mod.validate_request(value)
        self.assertFalse(value["request_grants_execution_authority"])
        self.assertFalse(value["claim_or_fence_minted"])
        self.assertFalse(value["transport_grants_execution_authority"])
        self.assertEqual(value["credential_authority"], "TV/TVC")
        self.assertEqual(value["github_token_runtime_authority"], "NONE")
        self.assertFalse(value["always_on_receiver_required"])
        self.assertFalse(value["second_user_device_required"])

    def test_invalid_destination_is_rejected(self) -> None:
        value = request()
        value["destination"] = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "Other"}
        body = dict(value)
        body.pop("request_hash")
        value["request_hash"] = mod.digest_uri(body)
        with self.assertRaises(mod.HILInTrMaterializationError):
            mod.validate_request(value)

    def test_consumer_invokes_only_existing_hil_targeted_executor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "intr-materialization").mkdir(parents=True)
            (runtime / "scripts").mkdir(parents=True)
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# target\n", encoding="utf-8")
            (runtime / "intr-materialization/request.json").write_text(
                json.dumps(request()) + "\n", encoding="utf-8"
            )
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            result = mod.consume_all(source, runtime, runner=runner, env={"GITHUB_TOKEN": "forbidden"})
            self.assertEqual(result["state"], "PROCESSED")
            self.assertEqual(result["runtime_execution_attempt_count"], 1)
            self.assertEqual(result["blocked_attempt_count"], 0)
            self.assertFalse(result["g18_completion_required"])
            self.assertFalse(result["g18_claim_or_fence_consumed"])
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertIn("--task-id", command)
            self.assertIn(mod.TARGET_TASK, command)
            self.assertIn("--source-root", command)
            self.assertIn("--runtime-root", command)
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
            self.assertEqual(kwargs["env"]["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")

            receipt = runtime / mod.RECEIPT_DIR_REL / f"{request()['materialization_id']}.json"
            self.assertTrue(receipt.is_file())
            saved = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(saved["state"], "MATERIALIZATION_EXECUTION_ATTEMPTED")
            self.assertFalse(saved["claim_or_fence_minted_by_consumer"])

    def test_successful_materialization_is_not_blindly_reexecuted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "intr-materialization").mkdir(parents=True)
            (runtime / "scripts").mkdir(parents=True)
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# target\n", encoding="utf-8")
            req = request()
            (runtime / "intr-materialization/request.json").write_text(json.dumps(req) + "\n", encoding="utf-8")
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            first = mod.consume_all(source, runtime, runner=runner)
            second = mod.consume_all(source, runtime, runner=runner)
            self.assertEqual(first["runtime_execution_attempt_count"], 1)
            self.assertEqual(second["runtime_execution_attempt_count"], 0)
            self.assertEqual(second["results"][0]["state"], "ALREADY_CONSUMED_SUCCESS")
            self.assertEqual(len(calls), 1)

    def test_failed_attempt_remains_nonterminal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "intr-materialization").mkdir(parents=True)
            (runtime / "scripts").mkdir(parents=True)
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# target\n", encoding="utf-8")
            (runtime / "intr-materialization/request.json").write_text(json.dumps(request()) + "\n", encoding="utf-8")

            def runner(command, **kwargs):
                return SimpleNamespace(returncode=7, stdout="", stderr="blocked")

            result = mod.consume_all(source, runtime, runner=runner)
            self.assertEqual(result["state"], "BLOCKED")
            self.assertEqual(result["blocked_attempt_count"], 1)
            self.assertTrue(result["results"][0]["blocked_attempt_remains_nonterminal"])


if __name__ == "__main__":
    unittest.main()
