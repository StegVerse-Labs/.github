#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path
from types import SimpleNamespace

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
            self.assertEqual(p["state"]["master_records_reconstruction"], "NOT_OBSERVED")
            self.assertEqual(p["state"]["principal_execution"], "NOT_OBSERVED")
            self.assertEqual(p["reconstruction"]["state"], "NOT_OBSERVED")
            self.assertEqual(p["materialization"]["state"], "NOT_AVAILABLE")
            self.assertFalse(p["topology"]["observer_direct_relation_to_stegverse_002"])

    def test_micro_node_provenance_does_not_bypass_master_records_projection_boundary(self):
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
            self.assertEqual(p["observation_source"], "MASTER_RECORDS_CUSTODY_ONLY")
            self.assertNotIn("knowledge", p)
            self.assertEqual(p["state"]["master_records_reconstruction"], "NOT_OBSERVED")

    def test_master_records_receipt_is_materialized_exactly_into_observer_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            state=root/"state"; runtime=root/"runtime"; micro=root/"micro"
            state.mkdir(); micro.mkdir()
            evidence={
                "artifact_sha256":{"SELF_CHARACTERIZATION.md":"a"*64},
                "subject_identity_sha256":"b"*64,
                "capability_realizations":[],
                "ordered_transition_receipts":[
                    {"sequence":0,"transition_receipt_id":"TR-1","transition_receipt_sha256":"c"*64,"transition_class":"CAUSAL_INGRESS_BOUND"}
                ],
                "repository_ledger_root":{"root_hash":"d"*64},
                "organization_ledger_root":{"root_hash":"e"*64},
            }
            body={
                "schema":"master-records.sv002-self-characterization-reconstruction/v0.2",
                "experiment_id":mod.EXPERIMENT_ID,
                "status":"PASS",
                "reconstruction":"PASS",
                "verified_at":"2026-09-01T00:00:00+00:00",
                "checks":{"execution_completed":True},
                "evidence":evidence,
                "error":None,
                "authority_boundary":{},
            }
            receipt={**body,"receipt_sha256":mod.sha256_hex(body)}
            source=state/mod.MR_CANONICAL_RECEIPT_NAME
            source.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
            prior=os.environ.get("STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT")
            os.environ["STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT"]=str(source)
            try:
                projection=mod.build_projection(runtime,micro)
            finally:
                if prior is None:
                    os.environ.pop("STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT",None)
                else:
                    os.environ["STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT"]=prior
            target=runtime/mod.MR_RECEIPT_REL
            self.assertEqual(target.read_bytes(),source.read_bytes())
            self.assertEqual(projection["materialization"]["state"],"MATERIALIZED")
            self.assertEqual(projection["state"]["master_records_reconstruction"],"PASS")
            self.assertEqual(projection["observation_source"],"MASTER_RECORDS_CUSTODY_ONLY")
            self.assertEqual(projection["topology"]["relationship_state_source"],"MASTER_RECORDS_CUSTODY_ONLY")
            self.assertEqual(projection["artifacts"]["ordered_transition_receipts"][0]["transition_receipt_id"],"TR-1")
            self.assertEqual(projection["artifacts"]["repository_ledger_root"]["root_hash"],"d"*64)
            self.assertEqual(projection["artifacts"]["organization_ledger_root"]["root_hash"],"e"*64)

    def test_master_records_projection_collision_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            state=root/"state"; runtime=root/"runtime"
            state.mkdir(); (runtime/mod.MR_RECEIPT_REL).parent.mkdir(parents=True)
            body={
                "schema":"master-records.sv002-self-characterization-reconstruction/v0.2",
                "experiment_id":mod.EXPERIMENT_ID,
                "status":"PASS","reconstruction":"PASS","verified_at":"2026-09-01T00:00:00+00:00",
                "checks":{},"evidence":{},"error":None,"authority_boundary":{},
            }
            receipt={**body,"receipt_sha256":mod.sha256_hex(body)}
            (state/mod.MR_CANONICAL_RECEIPT_NAME).write_text(json.dumps(receipt),encoding="utf-8")
            (runtime/mod.MR_RECEIPT_REL).write_text(json.dumps({"different":True}),encoding="utf-8")
            prior=os.environ.get("STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT")
            os.environ["STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT"]=str(state/mod.MR_CANONICAL_RECEIPT_NAME)
            try:
                with self.assertRaisesRegex(mod.ObservationRuntimeError,"projection_receipt_collision"):
                    mod.materialize_master_records_projection_receipt(runtime)
            finally:
                if prior is None:
                    os.environ.pop("STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT",None)
                else:
                    os.environ["STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT"]=prior

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


    def test_real_http_socket_roundtrip_observed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stegos_pkg = root / "stegos-root" / "stegos"
            stegos_pkg.mkdir(parents=True)
            (stegos_pkg / "__init__.py").write_text("", encoding="utf-8")
            (stegos_pkg / "universal_intr_transport.py").write_text(FAKE_INTR, encoding="utf-8")

            micro = root / "micro"
            prov = micro / "experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json"
            prov.parent.mkdir(parents=True)
            prov.write_text(json.dumps({
                "source_organization": {"organization": "Admissible-Existence", "availability_known": True}
            }), encoding="utf-8")

            runtime = root / "runtime"
            args = SimpleNamespace(
                allowed_origin="https://stegverse.org",
                runtime_root=runtime,
                micro_node_root=micro,
                stegos_root=root / "stegos-root",
                boundary_identity_ref="TVC:BOUNDARY:SV002-OBSERVE",
            )
            server = mod.BoundedHTTPServer(("127.0.0.1", 0), mod.make_handler(args))
            thread = threading.Thread(target=server.handle_request, daemon=True)
            thread.start()
            try:
                body = canonical(request()).encode("utf-8")
                req = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_address[1]}/intr/sv002-observe",
                    data=body,
                    method="POST",
                    headers={
                        "Origin": "https://stegverse.org",
                        "Content-Type": "application/json",
                        "X-StegVerse-Transport": "InTr",
                        "X-StegVerse-Authorization-Id": "AUTH-1",
                        "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
                    },
                )
                with urllib.request.urlopen(req, timeout=3) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                thread.join(timeout=3)
                self.assertFalse(thread.is_alive(), "SV002 observation HTTP receiver did not process request")
                self.assertEqual(payload["decision"], "ALLOW_READ_ONLY_OBSERVATION")
                self.assertEqual(payload["transport_receipts"]["ingress"]["transition_state"], "RECEIVED")
                self.assertEqual(payload["transport_receipts"]["egress"]["transition_state"], "FORWARDED")
                self.assertEqual(
                    payload["transport_receipts"]["egress"]["prior_receipt_hash"],
                    payload["transport_receipts"]["ingress"]["receipt_hash"],
                )
                self.assertFalse(payload["projection"]["topology"]["observer_direct_relation_to_stegverse_002"])
                receipts = list(
                    (runtime / "receipts/sovereign-network/sv002-public-observation").glob("SV002-OBS-IN-*.json")
                )
                self.assertEqual(len(receipts), 1)
            finally:
                server.server_close()

if __name__ == "__main__":
    unittest.main()
