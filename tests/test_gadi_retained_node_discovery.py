from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_gadi_retained_node_discovery.py"
spec = importlib.util.spec_from_file_location("gadi_retained_discovery", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value):
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def valid_receipt():
    node = "SV-NODE-" + "a" * 24
    body = {
        "schema": "stegos.stegbrowser.current-iphone-rendezvous-observation/v1",
        "state": "LOCAL_DISCOVERY_OBSERVED",
        "task_id": "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001",
        "cosv": "40000100100000",
        "execution_surface": "CURRENT_USER_IPHONE",
        "node_ref": node,
        "node_origin": "STEGBROWSER_RESIDENT",
        "profile_ref": "canonical-resident-substrate-v1/stegbrowser",
        "source_device_hb_reference": "heartbeat_epoch:32",
        "current_observed_hb_reference": "heartbeat_epoch:33",
        "heartbeat_grants_authority": False,
        "node_receipt_1_sha256": "NONE",
        "site_projection_observed": False,
        "session_id": "SV001-LOCAL-test",
        "endpoint": "http://127.0.0.1:8000",
        "discovery": {
            "schema": "stegverse.resident-rendezvous.discovery/v1",
            "state": "AVAILABLE",
            "target_node_ref": node,
            "gateway_execution_authority": "NONE",
            "credential_authority": "TV/TVC",
            "discovery_grants_authority": False,
            "authority_effect": "NONE_DISCOVERY_ONLY",
        },
        "intr_admission_observed": False,
        "workercoordinator_claim_observed": False,
        "canonical_request_consumption_observed": False,
        "provider_session_observed": False,
        "publication_observed": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_COMPONENT_EVIDENCE_ONLY",
        "observed_at": "2026-09-12T02:40:00Z",
    }
    receipt = dict(body)
    receipt["receipt_sha256"] = sha_uri(body)
    receipt["retained_node_state_generation"] = 2
    receipt["retained_node_state_commitment"] = "b" * 64
    receipt["retained_node_transition_sequence"] = 1
    receipt["retained_node_transition_commitment"] = "c" * 64
    receipt["retained_node_lineage_bound"] = True
    receipt["envelope_sha256"] = sha_uri(receipt)
    return receipt


class GADIRetainedNodeDiscoveryTests(unittest.TestCase):
    def test_valid_component_receipt_projects_discovery_only(self):
        result = module.project(valid_receipt())
        self.assertEqual(result["state"], "CURRENT_RETAINED_NODE_DISCOVERY_OBSERVED")
        self.assertFalse(result["runtime_presence_observed"])
        self.assertFalse(result["runtime_supervision_observed"])
        self.assertFalse(result["runtime_subject_bound"])
        self.assertFalse(result["execution_authority_granted"])
        self.assertEqual(result["authority_effect"], "NONE_OBSERVATION_ONLY")

    def test_tampered_receipt_body_fails_closed(self):
        receipt = valid_receipt()
        receipt["endpoint"] = "http://127.0.0.1:9000"
        with self.assertRaises(module.GADIRetainedNodeDiscoveryError):
            module.project(receipt)

    def test_tampered_envelope_digest_fails_closed(self):
        receipt = valid_receipt()
        receipt["envelope_sha256"] = "sha256:" + "d" * 64
        with self.assertRaisesRegex(module.GADIRetainedNodeDiscoveryError, "envelope digest"):
            module.project(receipt)

    def test_task_identity_drift_fails_closed(self):
        receipt = valid_receipt()
        receipt["task_id"] = "GADI-RESIDENT-EXECUTION-001"
        with self.assertRaisesRegex(module.GADIRetainedNodeDiscoveryError, "source discovery task"):
            module.project(receipt)

    def test_discovery_cannot_claim_downstream_authority(self):
        receipt = valid_receipt()
        receipt["workercoordinator_claim_observed"] = True
        body = copy.deepcopy(receipt)
        body.pop("receipt_sha256")
        body.pop("retained_node_state_generation")
        body.pop("retained_node_state_commitment")
        body.pop("retained_node_transition_sequence")
        body.pop("retained_node_transition_commitment")
        body.pop("retained_node_lineage_bound")
        body.pop("envelope_sha256")
        receipt["receipt_sha256"] = sha_uri(body)
        envelope = copy.deepcopy(receipt)
        envelope.pop("envelope_sha256")
        receipt["envelope_sha256"] = sha_uri(envelope)
        with self.assertRaisesRegex(module.GADIRetainedNodeDiscoveryError, "WorkerCoordinator claim"):
            module.project(receipt)


if __name__ == "__main__":
    unittest.main()
