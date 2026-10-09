#!/usr/bin/env python3
"""The CanonicalWork bootstrap admits in-process: no listener, socket or timeout (#3012 ECO-08).

No transport origin is patched in here (F50-01): the bootstrap's production path
is exercised as it runs, and the shared worker is exercised only with the
provenance each origin actually requires (F52-01, F52-02).
"""
from __future__ import annotations

import copy
import functools
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
attestation = ingress.origin_attestation
# The relay verifier is ONLY the TV/TVC conformance path: TVC's own sign/verify
# functions under the conformance test key, never a production key. Without a
# TVC checkout (STEGVERSE_TVC_ROOT) those cases skip as unproven, never passed.
conformance = load_module("origin_attestation_tvc_conformance_fixture", ROOT / "tests" / "test_origin_attestation_tvc_conformance.py")
RELAY_ORIGIN = "StegVerse-org"


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


def _headers(body: bytes, origin: str, authorization_id: str | None = None, *,
             origin_organization: str | None = None, signature: dict | None = None) -> dict[str, str]:
    headers = {"Content-Type": "application/json", "X-StegVerse-Transport": "InTr", "X-StegVerse-Transport-Origin": origin,
               "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest()}
    if authorization_id is not None:
        headers["X-StegVerse-Authorization-Id"] = authorization_id
    if origin_organization is not None:
        headers[ingress.ORIGIN_ORGANIZATION_HEADER] = origin_organization
    if signature is not None:
        headers[ingress.ORIGIN_ATTESTATION_HEADER] = json.dumps(signature, sort_keys=True)
    return headers


class _ConformanceAuthority:
    """TVC's own sign/verify functions under the conformance test key."""

    def __init__(self):
        self.signer = conformance._module("tv_signer_relay", conformance.TVC / conformance.SIGNER)
        verifier = conformance._module("tv_verifier_relay", conformance.TVC / conformance.VERIFIER)
        self.verify = functools.partial(verifier.verify_export, key=conformance.TEST_KEY)

    def sign(self, request: dict, body: bytes, *, origin_organization: str = RELAY_ORIGIN) -> dict:
        declared = ingress.relay_statement(request, origin_organization=origin_organization,
                                           request_sha256=hashlib.sha256(body).hexdigest())
        signature, _ = self.signer.sign_export(payload=attestation.payload_bytes(declared), key=conformance.TEST_KEY)
        return signature


class CanonicalWorkInProcessAdmissionTests(unittest.TestCase):
    def _request(self, runtime: Path, *, carrier: bool = False) -> dict:
        # The builder subprocess resolves repository packages the way its workflow does.
        with patch.dict(os.environ, {"PYTHONPATH": str(ROOT)}):
            path = bootstrap.run_builder(task_id=TASK_ID, runtime=runtime, registry=REGISTRY, registry_shards=SHARDS, without_carrier_binding=not carrier)
        return json.loads(path.read_text(encoding="utf-8"))

    def _admit_node(self, runtime: Path, request: dict) -> dict:
        body = _encoded(_node_envelope(request))
        return ingress.admit(runtime_root=runtime, body=body, headers=_headers(body, boundary.ORIGIN_NODE))

    def _assert_refused_without_effect(self, runtime: Path, body: bytes, headers: dict, reason: str | None = None,
                                       *, origin_verifier=None) -> ValueError:
        with patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()) as popen:
            with self.assertRaises(ValueError) as ctx:
                ingress.admit(runtime_root=runtime, body=body, headers=headers, origin_verifier=origin_verifier)
        if reason is not None:
            self.assertEqual(str(ctx.exception), reason)
        self.assertFalse((runtime / ingress.REQUEST_DIR_REL).exists())
        self.assertFalse((runtime / ingress.RECEIPT_DIR_REL).exists())
        popen.assert_not_called()
        return ctx.exception

    def _assert_relay_fail_closed(self, runtime: Path, body: bytes, headers: dict, predicate: str, *, origin_verifier=None) -> dict:
        refused = self._assert_refused_without_effect(runtime, body, headers, predicate, origin_verifier=origin_verifier)
        self.assertIsInstance(refused, ingress.OriginAttestationFailClosed)
        record = refused.record
        self.assertEqual(record["state"], "FAIL_CLOSED")
        self.assertEqual(record["failed_predicate"], predicate)
        self.assertEqual(record["retry_entrypoint"], ingress.RETRY_ENTRYPOINT)
        self.assertFalse(record["queue_written"] or record["receipt_written"])
        self.assertEqual(record["origin_attestation"]["origin_attestation_state"], attestation.REFUSED)
        self.assertEqual(record["authority_effect"], "NONE_NO_EFFECT")
        return record

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
            self._assert_relay_fail_closed(runtime, body, _headers(body, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-UNVERIFIED"),
                                           ingress.A4_VERIFIER_PREDICATE)

    # A4: TVC_RELAY_EGRESS only on TV/TVC's own receipt for the exact request.

    def test_relay_without_verifier_fails_closed_a4_predicate(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            body = _encoded(self._request(runtime))
            carried = {"algo": attestation.ALGORITHM, "value": "0" * 64, "sha256": "0" * 64}
            headers = _headers(body, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-1", origin_organization=RELAY_ORIGIN, signature=carried)
            record = self._assert_relay_fail_closed(runtime, body, headers, "A4_TV_TVC_ORIGIN_VERIFIER_PRESENT_AT_CUSTODY_OWNER")
            self.assertEqual(record["transport_origin"], boundary.ORIGIN_RELAY)
            # The bootstrap holds the same line before building anything: the
            # command line cannot inject a verifier and there is no fallback.
            evidence = Path(td) / "tvc-relay-authorization.json"
            evidence.write_text(json.dumps({"authorization_id": "RELAY-EGRESS-AUTH-1", "origin_organization": RELAY_ORIGIN,
                                            "origin_attestation": carried}), encoding="utf-8")
            with patch.dict(os.environ, {"STEGVERSE_TV_TVC_VERIFIER": "anything", "TV_HMAC_SIGNING_KEY": "anything"}):
                code, result = self._run_main(runtime / "bootstrap-runtime", "--tvc-relay-authorization", str(evidence))
            self.assertEqual(code, 2)
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["failed_predicate"], "A4_TV_TVC_ORIGIN_VERIFIER_PRESENT_AT_CUSTODY_OWNER")
            self.assertEqual(result["retry_entrypoint"], "scripts/run_canonical_work_event_bootstrap.py::main")
            self.assertIn("org-boundary/runtime/origin_attestation.py", result["detail"])
            self.assertFalse(result["admission_attempted"] or result["queue_written"] or result["receipt_written"])
            self.assertFalse((runtime / "bootstrap-runtime").exists())

    @unittest.skipUnless(conformance.TVC, conformance.REASON)
    def test_relay_origin_positive_case_admits_on_tvc_conformance_receipt(self):
        authority = _ConformanceAuthority()
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request_path = Path(td) / "request.json"
            request = self._request(runtime / "build")
            request_path.write_bytes(json.dumps(request, sort_keys=True, indent=2).encode("utf-8") + b"\n")
            body = request_path.read_bytes()
            provenance = {"state": "BOUND", "transport_origin": boundary.ORIGIN_RELAY, "authorization_id": "RELAY-EGRESS-AUTH-1",
                          "origin_organization": RELAY_ORIGIN, "origin_attestation": authority.sign(request, body),
                          "origin_verifier": authority.verify}
            with patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()):
                receipt = bootstrap.post_one(runtime=runtime, request_path=request_path, provenance=provenance, admit=ingress.admit)
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertEqual(receipt["disposition"], "ALLOW")
            self.assertEqual(receipt["transport_origin"], boundary.ORIGIN_RELAY)
            self.assertEqual(receipt["transport_authorization_id"], "RELAY-EGRESS-AUTH-1")
            self.assertEqual(receipt["transport_payload_sha256"], hashlib.sha256(body).hexdigest())
            record = receipt["origin_attestation"]
            self.assertEqual(record["origin_attestation_state"], attestation.PROVEN)
            self.assertIs(record["proves_the_authority_authenticated_the_asker"], False)
            self.assertEqual(record["attested_statement"], {
                "schema": attestation.STATEMENT_SCHEMA, "origin_organization": RELAY_ORIGIN,
                "destination_organization": "StegVerse-Labs", "destination_service": "CanonicalWork:Ingress",
                "packet_id": request["materialization_id"], "payload_sha256": hashlib.sha256(body).hexdigest(),
                "transport_profile": "TVC_RELAY_EGRESS"})
            self.assertEqual(json.loads(Path(receipt["queue_ref"]).read_text(encoding="utf-8"))["request_hash"], request["request_hash"])

    @unittest.skipUnless(conformance.TVC, conformance.REASON)
    def test_relay_with_moved_signature_refused(self):
        authority = _ConformanceAuthority()
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request = self._request(runtime)
            body = _encoded(request)
            other_packet = {**request, "materialization_id": "INTR-MAT-" + "f" * 24}
            moved = {
                "different packet": authority.sign(other_packet, body),
                "different payload": authority.sign(request, body + b" "),
                "different origin": authority.sign(request, body, origin_organization="StegGhost"),
            }
            for case, signature in moved.items():
                with self.subTest(case=case):
                    headers = _headers(body, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-1", origin_organization=RELAY_ORIGIN, signature=signature)
                    self._assert_relay_fail_closed(runtime, body, headers, "STATEMENT_MATCHES_WHAT_THE_AUTHORITY_SIGNED",
                                                   origin_verifier=authority.verify)
            # A signature from a key that is not the authority's never verifies.
            forged = {**authority.sign(request, body), "value": "0" * 64}
            headers = _headers(body, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-1", origin_organization=RELAY_ORIGIN, signature=forged)
            self._assert_relay_fail_closed(runtime, body, headers, "CREDENTIAL_AUTHORITY_REPORTS_THE_SIGNATURE_VALID",
                                           origin_verifier=authority.verify)

    @unittest.skipUnless(conformance.TVC, conformance.REASON)
    def test_relay_attested_statement_admits_only_exact_request(self):
        authority = _ConformanceAuthority()
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request = self._request(runtime)
            body = _encoded(request)
            signature = authority.sign(request, body)
            # The same request, other bytes: the attested digest is of the exact body.
            reserialized = json.dumps(request, sort_keys=True, indent=2).encode("utf-8")
            self._assert_relay_fail_closed(
                runtime, reserialized,
                _headers(reserialized, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-1", origin_organization=RELAY_ORIGIN, signature=signature),
                "STATEMENT_MATCHES_WHAT_THE_AUTHORITY_SIGNED", origin_verifier=authority.verify)
            # The exact body under another declared origin.
            self._assert_relay_fail_closed(
                runtime, body,
                _headers(body, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-1", origin_organization="StegVerse-Labs", signature=signature),
                "STATEMENT_MATCHES_WHAT_THE_AUTHORITY_SIGNED", origin_verifier=authority.verify)
            # No declared origin at all: the statement cannot be rebuilt.
            self._assert_relay_fail_closed(
                runtime, body, _headers(body, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-1", signature=signature),
                "STATEMENT_DECLARES_EVERY_BOUND_FIELD", origin_verifier=authority.verify)
            # No signature carried: the authority's shape is required.
            self._assert_relay_fail_closed(
                runtime, body, _headers(body, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-1", origin_organization=RELAY_ORIGIN),
                "SIGNATURE_IS_AN_OBJECT_OF_THE_AUTHORITYS_SHAPE", origin_verifier=authority.verify)
            # Only the exact attested request is admitted, once, write-once.
            headers = _headers(body, boundary.ORIGIN_RELAY, "RELAY-EGRESS-AUTH-1", origin_organization=RELAY_ORIGIN, signature=signature)
            with patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()) as popen:
                first = ingress.admit(runtime_root=runtime, body=body, headers=headers, origin_verifier=authority.verify)
                second = ingress.admit(runtime_root=runtime, body=body, headers=headers, origin_verifier=authority.verify)
            self.assertEqual(first["request_hash"], request["request_hash"])
            self.assertEqual(first["origin_attestation"]["attested_statement"]["payload_sha256"], hashlib.sha256(body).hexdigest())
            self.assertEqual(second["admitted_at"], first["admitted_at"])
            self.assertEqual(popen.call_count, 1)

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
