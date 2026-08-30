#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sv002_public_observe_runtime", ROOT / "scripts/serve_sv002_public_observation_runtime.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)

def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def digest(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()

def genesis():
    body = {
        "schema": "stegos.node_handoff_receipt.v1",
        "receipt_number": 1,
        "transition": "NODE_REGISTERED",
        "prior_state": "UNREGISTERED",
        "resulting_state": "REGISTERED",
        "continuity_parent": "GENESIS",
        "node_id": "SV-NODE-0123456789abcdef01234567",
        "interlock_id": "SV-IL-0123456789abcdef01234567",
        "device_binding_sha256": "a" * 64,
        "authority_effect": "NONE",
        "heartbeat_authority": "StegVerse-Labs/.github",
        "credential_authority": "TV/TVC",
    }
    return {**body, "receipt_sha256": digest(body)}

def request(auth="AUTH-1"):
    g = genesis()
    body = {
        "schema_version": mod.REQUEST_SCHEMA,
        "request_class": mod.REQUEST_CLASS,
        "operation": mod.OPERATION,
        "authority_ref": auth,
        "transport": "InTr",
        "observer": {
            "node_id": g["node_id"],
            "interlock_id": g["interlock_id"],
            "registration_receipt_sha256": g["receipt_sha256"],
            "genesis_receipt": g,
        },
        "bindings": {
            "experiment_id": mod.EXPERIMENT_ID,
            "observation_projection": mod.PROJECTION_CLASS,
        },
        "payload": {},
        "authority_transfer": False,
    }
    return {**body, "request_sha256": digest(body)}

FAKE_INTR = r'''
import hashlib, json

def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def uri(v):
    return "sha256:" + hashlib.sha256(canonical(v).encode()).hexdigest()

def sha256_uri(v):
    return uri(v)

def build_transport_intent(**kw):
    source=kw["source_boundary"]; dest=kw["destination_boundary"]
    path=[source,dest]
    basis={
      "operation_id":kw["operation_id"],"payload_hash":kw["payload_hash"],
      "source_boundary":source,"source_subsystem":kw["source_subsystem"],
      "destination_boundary":dest,"destination_subsystem":kw["destination_subsystem"],
      "boundary_path":path,
    }
    return {
      "schema":"stegverse.universal-intr-transport/v1","protocol":"InTr",
      "operation_id":kw["operation_id"],"packet_id":"INTR-"+hashlib.sha256(canonical(basis).encode()).hexdigest()[:24],
      "payload_hash":kw["payload_hash"],"prior_transport_receipt_hash":kw.get("prior_transport_receipt_hash"),
      "source":{"boundary":source,"subsystem":kw["source_subsystem"]},
      "destination":{"boundary":dest,"subsystem":kw["destination_subsystem"]},
      "boundary_path":path,
    }

def build_hop_receipt(intent, *, hop_index, receipt_id, boundary_identity_ref, recorded_at, prior_receipt_hash, transition_state="RECEIVED"):
    body={
      "schema":"stegverse.intr.hop_receipt/v1","receipt_id":receipt_id,"packet_id":intent["packet_id"],
      "hop_index":hop_index,"direction":"FORWARD","from_role":intent["boundary_path"][0],"to_role":intent["boundary_path"][1],
      "operation_hash":uri({"operation_id":intent["operation_id"],"packet_id":intent["packet_id"],"payload_hash":intent["payload_hash"]}),
      "payload_hash":intent["payload_hash"],"prior_receipt_hash":prior_receipt_hash,
      "boundary_identity_ref":boundary_identity_ref,"boundary_verification":"VERIFIED",
      "transition_state":transition_state,"secret_plaintext_present":False,"authority_transfer":False,"recorded_at":recorded_at,
    }
    return {**body,"receipt_hash":uri(body)}
'''

class TestSV002PublicObservationRuntime(unittest.TestCase):
    def test_valid_node_and_request_binding(self):
        admitted = mod.validate_request(request(), "AUTH-1")
        self.assertEqual(admitted["observer_binding"]["node_id"], genesis()["node_id"])
        self.assertEqual(admitted["bindings"]["experiment_id"], mod.EXPERIMENT_ID)

    def test_tampered_genesis_fails_closed(self):
        rq = request()
        rq["observer"]["genesis_receipt"]["node_id"] = "SV-NODE-TAMPERED"
        body = dict(rq); body.pop("request_sha256")
        rq["request_sha256"] = digest(body)
        with self.assertRaises(mod.SV002ObservationError):
            mod.validate_request(rq, "AUTH-1")

    def test_request_hash_tamper_fails_closed(self):
        rq = request()
        rq["payload"] = {"unexpected": True}
        with self.assertRaisesRegex(mod.SV002ObservationError, "request_sha256_mismatch"):
            mod.validate_request(rq, "AUTH-1")

    def test_missing_evidence_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            p = mod._projection(Path(td), None)
            self.assertEqual(p["state"]["execution"]["state"], "NOT_OBSERVED")
            self.assertEqual(p["reconstruction"]["state"], "NOT_OBSERVED")
            self.assertFalse(any(p["evidence_presence"].values()))

    def test_roundtrip_receipts_and_read_only_projection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stegos = root / "stegos-root" / "stegos"
            stegos.mkdir(parents=True)
            (stegos / "__init__.py").write_text("", encoding="utf-8")
            (stegos / "universal_intr_transport.py").write_text(FAKE_INTR, encoding="utf-8")

            exp = root / "exp"; exp.mkdir()
            (exp / "EXPERIMENT_EXECUTION_RECEIPT.json").write_text(json.dumps({"state":"COMPLETED","principal_run_completed":True}), encoding="utf-8")
            (exp / "SELF_CHARACTERIZATION_FORMAL.json").write_text(json.dumps({"AVAILABLE":True,"USED":False}), encoding="utf-8")
            (exp / "INTERACTION_RECEIPT_CHAIN.json").write_text(json.dumps({"events":[{"event":"principal_completed"}]}), encoding="utf-8")

            runtime = root / "runtime"
            resp = mod.process_request(
                request(),
                authorization_id="AUTH-1",
                stegos_root=root / "stegos-root",
                experiment_root=exp,
                runtime_root=runtime,
                boundary_identity_ref="TVC:BOUNDARY:SV002-OBSERVE",
            )
            self.assertEqual(resp["decision"], "ALLOW_READ_ONLY_OBSERVATION")
            self.assertFalse(resp["projection"]["topology"]["observer_direct_interaction_with_subject"])
            self.assertEqual(resp["transport_receipts"]["ingress"]["transition_state"], "RECEIVED")
            self.assertEqual(resp["transport_receipts"]["egress"]["transition_state"], "FORWARDED")
            self.assertEqual(resp["transport_receipts"]["egress"]["prior_receipt_hash"], resp["transport_receipts"]["ingress"]["receipt_hash"])
            receipts = list((runtime / "receipts/sovereign-network/sv002-public-observation").glob("*.json"))
            self.assertEqual(len(receipts), 1)

if __name__ == "__main__":
    unittest.main()
