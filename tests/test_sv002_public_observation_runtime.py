#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sv002_observation_intr_runtime",
    ROOT / "scripts/serve_sv002_observation_intr_runtime.py",
)
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
        "schema_version": "stegverse.sv002.public_observation.interlock_request.v1",
        "request_class": "SV002_PUBLIC_OBSERVE",
        "operation": "READ_OBSERVATION",
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
            "observation_projection": "PUBLIC_READ_ONLY",
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
        validated = mod._validate_request(request(), "AUTH-1")
        self.assertEqual(validated["node_id"], genesis()["node_id"])

    def test_tampered_genesis_fails_closed(self):
        rq = request()
        rq["observer"]["genesis_receipt"]["node_id"] = "SV-NODE-TAMPERED"
        body = dict(rq); body.pop("request_sha256")
        rq["request_sha256"] = digest(body)
        with self.assertRaises(mod.ObservationRuntimeError):
            mod._validate_request(rq, "AUTH-1")

    def test_request_hash_tamper_fails_closed(self):
        rq = request()
        rq["payload"] = {"unexpected": True}
        with self.assertRaisesRegex(mod.ObservationRuntimeError, "request_sha256_mismatch"):
            mod._validate_request(rq, "AUTH-1")

    def test_missing_evidence_is_explicit_and_nonfabricated(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            micro = root / "micro"
            runtime = root / "runtime"
            (micro / "experiments/self-characterization-001").mkdir(parents=True)
            p = mod.build_projection(runtime, micro)
            self.assertEqual(p["state"]["worker_receipt"], "NOT_OBSERVED")
            self.assertEqual(p["state"]["principal_execution"], "NOT_OBSERVED")
            self.assertEqual(p["reconstruction"]["state"], "NOT_OBSERVED")
            self.assertFalse(p["topology"]["observer_direct_relation_to_stegverse_002"])

    def test_admissible_existence_is_available_not_connected_without_interlock_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            micro = root / "micro"
            runtime = root / "runtime"
            prov = micro / "experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json"
            prov.parent.mkdir(parents=True)
            prov.write_text(json.dumps({
                "source_organization": {"organization": "Admissible-Existence", "availability_known": True}
            }), encoding="utf-8")
            p = mod.build_projection(runtime, micro)
            self.assertEqual(
                p["knowledge"]["admissible_existence"]["availability"],
                "KNOWN_AVAILABLE_FROM_CONSTRUCTION_PROVENANCE",
            )
            self.assertEqual(p["knowledge"]["admissible_existence"]["interlock"], "NOT_CONNECTED")

    def test_roundtrip_receipts_and_read_only_projection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stegos = root / "stegos-root" / "stegos"
            stegos.mkdir(parents=True)
            (stegos / "__init__.py").write_text("", encoding="utf-8")
            (stegos / "universal_intr_transport.py").write_text(FAKE_INTR, encoding="utf-8")

            micro = root / "micro"
            prov = micro / "experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json"
            prov.parent.mkdir(parents=True)
            prov.write_text(json.dumps({
                "source_organization": {"organization": "Admissible-Existence", "availability_known": True}
            }), encoding="utf-8")

            runtime = root / "runtime"
            worker_receipt = runtime / mod.WORKER_RECEIPT_REL
            worker_receipt.parent.mkdir(parents=True)
            state_root = root / "state"
            state_root.mkdir()
            worker_receipt.write_text(json.dumps({
                "state": "COMPLETED",
                "state_root": str(state_root),
            }), encoding="utf-8")
            (state_root / "EXPERIMENT_EXECUTION_RECEIPT.json").write_text(
                json.dumps({"state": "COMPLETED", "principal_run_completed": True}),
                encoding="utf-8",
            )
            (state_root / "SELF_CHARACTERIZATION_FORMAL.json").write_text(
                json.dumps({"AVAILABLE": True, "USED": False}),
                encoding="utf-8",
            )
            (state_root / "INTERACTION_RECEIPT_CHAIN.json").write_text(
                json.dumps({"events": [{"event": "principal_completed"}]}),
                encoding="utf-8",
            )

            resp = mod.process_observation(
                request(),
                authorization_id="AUTH-1",
                stegos_root=root / "stegos-root",
                micro_node_root=micro,
                runtime_root=runtime,
                boundary_identity_ref="TVC:BOUNDARY:SV002-OBSERVE",
            )
            self.assertEqual(resp["decision"], "ALLOW_READ_ONLY_OBSERVATION")
            self.assertFalse(resp["projection"]["topology"]["observer_direct_relation_to_stegverse_002"])
            self.assertEqual(resp["transport_receipts"]["ingress"]["transition_state"], "RECEIVED")
            self.assertEqual(resp["transport_receipts"]["egress"]["transition_state"], "FORWARDED")
            self.assertEqual(
                resp["transport_receipts"]["egress"]["prior_receipt_hash"],
                resp["transport_receipts"]["ingress"]["receipt_hash"],
            )
            receipts = list((runtime / "receipts/sovereign-network/sv002-public-observation").glob("SV002-OBS-IN-*.json"))
            self.assertEqual(len(receipts), 1)

if __name__ == "__main__":
    unittest.main()
