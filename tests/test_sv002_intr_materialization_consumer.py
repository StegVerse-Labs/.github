from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "consume_sv002_intr_materialization_request",
    ROOT / "scripts/consume_sv002_intr_materialization_request.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


def request(materialization_id: str = "INTR-MAT-" + "a" * 24) -> dict:
    body = {
        "schema": "stegverse.universal-intr-materialization-request/v1",
        "materialization_id": materialization_id,
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": "sha256:" + "1" * 64,
        "operation_id": "SV002-OBSERVE-TEST-001",
        "packet_id": "INTR-" + "b" * 24,
        "payload_hash": "sha256:" + "2" * 64,
        "payload_ref": "opaque://sv002-observation/request/001",
        "destination": {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "SV002:PublicObservation"},
        "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
        "downstream_owner_ref": "StegVerse-Labs/.github#493",
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


def ingress(req: dict) -> dict:
    return {
        "schema": "stegverse.sv002-intr-materialization-ingress/v1",
        "state": "INGRESS_ADMITTED",
        "materialization_id": req["materialization_id"],
        "request_hash": req["request_hash"],
        "transport_intent_hash": req["transport_intent_hash"],
        "payload_hash": req["payload_hash"],
        "operation_id": req["operation_id"],
        "packet_id": req["packet_id"],
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "claim_or_fence_minted": False,
        "g18_required": False,
    }


class SV002MaterializationConsumerTests(unittest.TestCase):
    def test_request_is_event_triggered_non_authorizing_and_g18_independent(self):
        value = request()
        mod.validate_request(value)
        self.assertTrue(value["event_triggered"])
        self.assertFalse(value["always_on_receiver_required"])
        self.assertFalse(value["request_grants_execution_authority"])
        self.assertFalse(value["claim_or_fence_minted"])

    def test_route_pending_remains_nonterminal_and_retryable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"; runtime = root / "runtime"
            source.mkdir(); (runtime / mod.REQUEST_DIR_REL).mkdir(parents=True)
            (runtime / mod.INGRESS_RECEIPT_DIR_REL).mkdir(parents=True)
            (runtime / "scripts").mkdir()
            (runtime / mod.ROUTE_MATERIALIZER).write_text("# materializer\n")
            req = request()
            (runtime / mod.REQUEST_DIR_REL / "request.json").write_text(json.dumps(req))
            (runtime / mod.INGRESS_RECEIPT_DIR_REL / f"{req['materialization_id']}.json").write_text(json.dumps(ingress(req)))

            def runner(command, **kwargs):
                self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
                if str(command[1]).endswith("materialize_sv002_observation_route_config.py"):
                    return SimpleNamespace(returncode=0, stdout=json.dumps({"state":"PREDICATE_PENDING","reason":"local roots absent"})+"\n", stderr="")
                raise AssertionError("targeted executor must not run while route predicates are pending")

            result = mod.consume_all(source, runtime, runner=runner, env={"GITHUB_TOKEN":"forbidden","PATH":"/bin"})
            self.assertEqual(result["state"], "NONTERMINAL")
            self.assertEqual(result["runtime_execution_attempt_count"], 0)
            self.assertFalse(result["results"][0]["receiver_ready_observed"])
            self.assertFalse(result["g18_completion_required"])

    def test_receiver_ready_terminalizes_materialization_not_observation_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"; runtime = root / "runtime"
            source.mkdir(); (runtime / mod.REQUEST_DIR_REL).mkdir(parents=True)
            (runtime / mod.INGRESS_RECEIPT_DIR_REL).mkdir(parents=True)
            (runtime / "scripts").mkdir()
            (runtime / mod.ROUTE_MATERIALIZER).write_text("# materializer\n")
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# executor\n")
            req = request()
            (runtime / mod.REQUEST_DIR_REL / "request.json").write_text(json.dumps(req))
            (runtime / mod.INGRESS_RECEIPT_DIR_REL / f"{req['materialization_id']}.json").write_text(json.dumps(ingress(req)))

            def runner(command, **kwargs):
                if str(command[1]).endswith("materialize_sv002_observation_route_config.py"):
                    return SimpleNamespace(returncode=0, stdout=json.dumps({"state":"MATERIALIZED"})+"\n", stderr="")
                return SimpleNamespace(returncode=0, stdout=json.dumps({"transition_id":"SV002_PUBLIC_OBSERVATION_RECEIVER_READY"})+"\n", stderr="")

            result = mod.consume_all(source, runtime, runner=runner)
            row = result["results"][0]
            self.assertEqual(row["state"], "MATERIALIZATION_READY_OBSERVED")
            self.assertTrue(row["receiver_ready_observed"])
            self.assertFalse(row["round_trip_observed"])
            self.assertEqual(result["state"], "READY_OBSERVED")

            second = mod.consume_all(source, runtime, runner=lambda *a, **k: (_ for _ in ()).throw(AssertionError("successful materialization must not rerun")))
            self.assertEqual(second["results"][0]["state"], "ALREADY_CONSUMED_SUCCESS")

    def test_mismatched_ingress_binding_is_rejected_without_execution(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"; runtime = root / "runtime"
            source.mkdir(); (runtime / mod.REQUEST_DIR_REL).mkdir(parents=True)
            (runtime / mod.INGRESS_RECEIPT_DIR_REL).mkdir(parents=True)
            req = request()
            bad = ingress(req); bad["request_hash"] = "sha256:" + "f" * 64
            (runtime / mod.REQUEST_DIR_REL / "request.json").write_text(json.dumps(req))
            (runtime / mod.INGRESS_RECEIPT_DIR_REL / f"{req['materialization_id']}.json").write_text(json.dumps(bad))
            result = mod.consume_all(source, runtime, runner=lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not execute")))
            self.assertEqual(result["results"][0]["state"], "REQUEST_REJECTED")


if __name__ == "__main__":
    unittest.main()
