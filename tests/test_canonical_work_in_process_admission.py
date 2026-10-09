#!/usr/bin/env python3
"""The CanonicalWork bootstrap admits in-process: no listener, socket or timeout (#3012 ECO-08).

No transport origin is patched in here (F50-01): the bootstrap's production path
is exercised as it runs, and the shared worker is exercised only with the
provenance each origin actually requires (F52-01, F52-02).
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
SHARDS = ROOT / "data" / "canonical-task-records"
TASK_ID = "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bootstrap = load_module("canonical_work_bootstrap_in_process", ROOT / "scripts" / "run_canonical_work_event_bootstrap.py")
ingress = load_module("canonical_work_intr_ingress_in_process", ROOT / "workers" / "canonical_work_intr_ingress.py")
boundary = ingress.transport_boundary


class _NoProcess:
    pid = 0


def _no_network(*_args, **_kwargs):
    raise AssertionError("in-process admission must not open a socket or listener")


def _encoded(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _rehash_request(request: dict) -> dict:
    body = {key: value for key, value in request.items() if key != "request_hash"}
    return {**body, "request_hash": boundary._sha256_uri(body)}


def _node_envelope(request: dict, *, trigger_origin: str | None = None) -> dict:
    entry = {
        "schema": boundary.NODE_OUTBOX_SCHEMA, "state": "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
        "node_id": "SV-NODE-" + "a" * 24, "interlock_id": "SV-IL-" + "b" * 24,
        "materialization_id": request["materialization_id"], "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"], "payload_hash": request["payload_hash"],
        "destination": request["destination"], "downstream_owner_ref": request["downstream_owner_ref"],
        "materialization_request": request, "network_delivery_observed": False, "runtime_materialization_observed": False,
        "receiver_receipt_observed": False, "tvc_receipt_observed": False, "request_grants_execution_authority": False,
        "claim_or_fence_minted": False, "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_LOCAL_CONTINUITY_ONLY",
    }
    entry["outbox_entry_hash"] = boundary._sha256_uri(entry)
    trigger = {
        "schema": boundary.NODE_TRIGGER_SCHEMA, "transport_origin": trigger_origin or boundary.ORIGIN_NODE,
        "node_id": entry["node_id"], "interlock_id": entry["interlock_id"], "outbox_entry_hash": entry["outbox_entry_hash"],
        "node_outbox_entry": entry, "request_grants_execution_authority": False, "claim_or_fence_minted": False,
        "authority_effect": "NONE_TRIGGER_ONLY",
    }
    trigger["trigger_sha256"] = boundary._sha256_uri(trigger)
    return trigger


def _headers(body: bytes, origin: str, authorization_id: str | None = None) -> dict[str, str]:
    headers = {"Content-Type": "application/json", "X-StegVerse-Transport": "InTr", "X-StegVerse-Transport-Origin": origin,
               "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest()}
    if authorization_id is not None:
        headers["X-StegVerse-Authorization-Id"] = authorization_id
    return headers


class CanonicalWorkInProcessAdmissionTests(unittest.TestCase):
    def _request(self, runtime: Path, *, carrier: bool = False) -> dict:
        # The builder subprocess resolves repository packages the way its workflow does.
        with patch.dict(os.environ, {"PYTHONPATH": str(ROOT)}):
            path = bootstrap.run_builder(task_id=TASK_ID, runtime=runtime, registry=REGISTRY, registry_shards=SHARDS, without_carrier_binding=not carrier)
        return json.loads(path.read_text(encoding="utf-8"))

    def _admit_node(self, runtime: Path, request: dict) -> dict:
        body = _encoded(_node_envelope(request))
        return ingress.admit(runtime_root=runtime, body=body, headers=_headers(body, boundary.ORIGIN_NODE))

    def _assert_refused_without_effect(self, runtime: Path, body: bytes, headers: dict, reason: str | None = None) -> None:
        with patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()) as popen:
            with self.assertRaises(ValueError) as ctx:
                ingress.admit(runtime_root=runtime, body=body, headers=headers)
        if reason is not None:
            self.assertEqual(str(ctx.exception), reason)
        self.assertFalse((runtime / ingress.REQUEST_DIR_REL).exists())
        self.assertFalse((runtime / ingress.RECEIPT_DIR_REL).exists())
        popen.assert_not_called()

    def _run_main(self, runtime: Path, *extra: str) -> tuple[int, dict]:
        argv = ["run_canonical_work_event_bootstrap.py", "--task-id", TASK_ID, "--runtime-root", str(runtime), *extra]
        printed: list[str] = []
        with patch.object(sys, "argv", argv), \
                patch.object(bootstrap, "run_builder", side_effect=AssertionError("builder must not run unbound")), \
                patch.object(bootstrap, "post_one", side_effect=AssertionError("admission must not be called unbound")), \
                patch.object(bootstrap.shared_ingress, "admit_canonical_work", side_effect=AssertionError("admission must not be called unbound"), create=True), \
                patch("builtins.print", side_effect=lambda value, *a, **k: printed.append(value)):
            code = bootstrap.main()
        return code, json.loads(printed[-1])

    # In-process admission behaviour, through the validated node envelope.

    def test_absent_listener_does_not_block_admission(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request = self._request(runtime)
            with patch("urllib.request.urlopen", _no_network), patch("socket.socket", _no_network), \
                    patch("socket.create_connection", _no_network), \
                    patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()):
                receipt = self._admit_node(runtime, request)
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertEqual(receipt["request_hash"], request["request_hash"])
            self.assertTrue(receipt["write_once_persisted"])
            self.assertEqual(json.loads(Path(receipt["queue_ref"]).read_text(encoding="utf-8"))["request_hash"], request["request_hash"])

    def test_same_request_admitted_twice_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request = self._request(runtime)
            with patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()) as popen:
                first = self._admit_node(runtime, request)
                queued = Path(first["queue_ref"]).read_bytes()
                second = self._admit_node(runtime, request)
            self.assertEqual(second["request_hash"], first["request_hash"])
            self.assertEqual(second["admitted_at"], first["admitted_at"])
            self.assertEqual(Path(first["queue_ref"]).read_bytes(), queued)
            # The replay returns the write-once receipt; the consumer is not dispatched again.
            self.assertEqual(popen.call_count, 1)

    def test_malformed_request_is_refused_typed_without_effect(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request = self._request(runtime)
            request["request_hash"] = "sha256:" + "0" * 64
            body = _encoded(_node_envelope(request))
            self._assert_refused_without_effect(runtime, body, _headers(body, boundary.ORIGIN_NODE), "materialization_request_hash_mismatch")

    def test_ingress_admitted_never_claims_downstream_completion(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request = self._request(runtime)
            with patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()):
                receipt = self._admit_node(runtime, request)
            self.assertFalse(receipt["runtime_execution_attempted"])
            self.assertFalse(receipt["claim_or_fence_minted"])
            self.assertEqual(receipt["authority_effect"], "INGRESS_TRANSITION_ONLY")

    def test_declared_sovereign_node_origin_is_refused_typed_without_effect(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            body = _encoded(self._request(runtime))
            self._assert_refused_without_effect(runtime, body, _headers(body, "SOVEREIGN_NODE"), "transport_origin_header_invalid")

    def test_bootstrap_opens_no_loopback_connection(self):
        source = (ROOT / "scripts" / "run_canonical_work_event_bootstrap.py").read_text(encoding="utf-8")
        for forbidden in ("urlopen", "urllib.request", "http.client", "import socket", "shared_ingress.Server", "handle_request"):
            self.assertNotIn(forbidden, source)
        self.assertIn('getattr(shared_ingress, "admit_canonical_work", None)', source)

    # F50-01 / F52-01 / F52-02: origin only from authentic provenance.

    def test_default_unbound_bootstrap_fails_closed_with_origin_provenance_predicate_and_retry(self):
        self.assertFalse(hasattr(bootstrap, "TRANSPORT_ORIGIN"))
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve() / "runtime"
            code, result = self._run_main(runtime)
            self.assertEqual(code, 2)
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["failed_predicate"], "CANONICAL_WORK_TRANSPORT_ORIGIN_AUTHENTICALLY_BOUND")
            self.assertEqual(result["retry_entrypoint"], "scripts/run_canonical_work_event_bootstrap.py::main")
            self.assertIn("--node-outbox-envelope not supplied", result["detail"])
            self.assertIn("--tvc-relay-authorization not supplied", result["detail"])
            self.assertIsNone(result["transport_origin"])
            self.assertFalse(result["admission_attempted"] or result["queue_written"] or result["receipt_written"])
            # No effect: the runtime root is not even created.
            self.assertFalse(runtime.exists())

    def test_hb_carrier_binding_alone_never_selects_admitted_origin(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request = self._request(runtime, carrier=True)
            self.assertIsNotNone(request.get("carrier_binding"))
            self.assertIs(request["carrier_binding"]["carrier_grants_admission_authority"], False)
            # The bootstrap never derives an origin from a carrier-bearing request.
            resolved = bootstrap.resolve_transport_provenance(node_outbox_envelope=None, tvc_relay_authorization=None)
            self.assertEqual(resolved["state"], "FAIL_CLOSED")
            self.assertIs(resolved["carrier_binding_selects_origin"], False)
            body = _encoded(request)
            # A carrier-bearing raw request is neither a node envelope nor a verified relay request.
            self._assert_refused_without_effect(runtime, body, _headers(body, boundary.ORIGIN_NODE), "node_outbox_canonical_work_envelope_required")
            self._assert_refused_without_effect(runtime, body, _headers(body, boundary.ORIGIN_RELAY), "authorization_id_header_required_for_relay")
            missing_origin = _headers(body, boundary.ORIGIN_NODE)
            missing_origin.pop("X-StegVerse-Transport-Origin")
            self._assert_refused_without_effect(runtime, body, missing_origin, "transport_origin_header_invalid")

    def test_relay_origin_requires_verified_tvc_authorization(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            body = _encoded(self._request(runtime))
            self._assert_refused_without_effect(runtime, body, _headers(body, boundary.ORIGIN_RELAY), "authorization_id_header_required_for_relay")
            # A supplied id is never self-certified: without the A4/TV-TVC verifier it cannot bind.
            self._assert_refused_without_effect(runtime, body, _headers(body, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-UNVERIFIED"),
                                                ingress.RELAY_AUTHORIZATION_UNVERIFIABLE)
            evidence = Path(td) / "tvc-relay-authorization.json"
            evidence.write_text(json.dumps({"authorization_id": "RELAY-EGRESS-AUTH-UNVERIFIED"}), encoding="utf-8")
            code, result = self._run_main(runtime / "bootstrap-runtime", "--tvc-relay-authorization", str(evidence))
            self.assertEqual(code, 2)
            self.assertEqual(result["failed_predicate"], "CANONICAL_WORK_TRANSPORT_ORIGIN_AUTHENTICALLY_BOUND")
            self.assertIn("authorization id is unverifiable", result["detail"])
            self.assertIn("org-boundary/runtime/origin_attestation.py", result["detail"])
            self.assertFalse((runtime / "bootstrap-runtime").exists())

    def test_relay_origin_positive_case_requires_existing_a4_verifier(self):
        self.skipTest("no A4/TV-TVC authorization verifier exists in this repository; the positive relay case cannot run and is not faked")

    def test_node_origin_requires_validated_outbox_envelope(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request = self._request(runtime)
            raw = _encoded(request)
            self._assert_refused_without_effect(runtime, raw, _headers(raw, boundary.ORIGIN_NODE), "node_outbox_canonical_work_envelope_required")
            tampered = _node_envelope(request)
            tampered["node_outbox_entry"]["node_id"] = "SV-NODE-" + "c" * 24
            body = _encoded(tampered)
            self._assert_refused_without_effect(runtime, body, _headers(body, boundary.ORIGIN_NODE), "node_outbox_entry_hash_mismatch")
            with patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()):
                receipt = self._admit_node(runtime, request)
            self.assertEqual(receipt["transport_origin"], boundary.ORIGIN_NODE)
            self.assertIsNone(receipt["transport_authorization_id"])
            self.assertEqual(receipt["node_id"], "SV-NODE-" + "a" * 24)
            self.assertEqual(receipt["outbox_entry_hash"], _node_envelope(request)["outbox_entry_hash"])

    def test_mismatched_header_envelope_missing_authorization_spoofed_carrier_fail_closed_without_effect(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request = self._request(runtime, carrier=True)
            envelope = _encoded(_node_envelope(request))
            # Relay header over a node envelope.
            self._assert_refused_without_effect(runtime, envelope, _headers(envelope, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-TEST"), "canonical_work_destination_mismatch")
            # Node header claiming a TVC authorization.
            self._assert_refused_without_effect(runtime, envelope, _headers(envelope, boundary.ORIGIN_NODE, "RELAY-EGRESS-AUTH-TEST"), "node_outbox_cannot_claim_tvc_authorization")
            # Envelope whose trigger declares the relay origin under a node header.
            relabelled = _encoded(_node_envelope(request, trigger_origin=boundary.ORIGIN_RELAY))
            self._assert_refused_without_effect(runtime, relabelled, _headers(relabelled, boundary.ORIGIN_NODE), "node_trigger_origin_invalid")
            # Payload digest header that is not the exact body.
            mismatched = _headers(envelope, boundary.ORIGIN_NODE)
            mismatched["X-StegVerse-Payload-SHA256"] = "0" * 64
            self._assert_refused_without_effect(runtime, envelope, mismatched, "payload_sha256_header_mismatch")
            # Relay with no authorization id.
            raw = _encoded(request)
            self._assert_refused_without_effect(runtime, raw, _headers(raw, boundary.ORIGIN_RELAY), "authorization_id_header_required_for_relay")
            # Spoofed carrier: a binding claiming admission authority, wrapped in an otherwise valid envelope.
            spoofed = copy.deepcopy(request)
            spoofed["carrier_binding"]["carrier_grants_admission_authority"] = True
            spoofed_body = _encoded(_node_envelope(_rehash_request(spoofed)))
            self._assert_refused_without_effect(runtime, spoofed_body, _headers(spoofed_body, boundary.ORIGIN_NODE))


if __name__ == "__main__":
    unittest.main()
