from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workers import manifest_state_transition_intr_ingress as mod


GOAL = "ECOSYSTEM-ECONOMIC-WHITEPAPER-GATED-ROADMAP-001"


def governance_request() -> dict:
    manifest_body = {
        "manifest_profile": "stegverse.ingress-manifest.v1",
        "source_output_id": "economic-publication",
        "payload": {
            "candidate": {
                "goal_task_id": GOAL,
                "target_repository": "GCAT-BCAT-Engine/Publisher",
                "target_path": "papers/StegVerse_Private_State_Economy_White_Paper_v0.1.md",
            }
        },
    }
    manifest_hash = mod.sha256(manifest_body)
    manifest = dict(manifest_body)
    manifest["canonical_manifest_sha256"] = manifest_hash
    graph = {
        "schema": "stegverse.sdk.installed-state-transition-graph/v1",
        "graph_id": "RTC-GOVERNED-PROCESSING-002",
        "canonical_task_id": None,
        "processing_capability": "governance",
        "route_id": mod.GOVERNANCE_ROUTE_ID,
        "request": {"source": "test-only"},
        "ordered_transitions": [],
        "requires_workercoordinator_claim_fence": False,
        "predecessor_closure_required": True,
        "adapter_executes_lifecycle": False,
        "authority_effect": "NONE_GRAPH_DERIVATION_ONLY",
    }
    request = {
        "schema": mod.REQUEST_SCHEMA,
        "canonical_manifest": manifest,
        "canonical_manifest_sha256": manifest_hash,
        "processing_capability": "governance",
        "route_id": mod.GOVERNANCE_ROUTE_ID,
        "route_declaration_hash": "route-governance",
        "state_graph": graph,
        "graph_id": graph["graph_id"],
        "canonical_task_id": None,
        "requires_workercoordinator_claim_fence": False,
        "predecessor_closure_required": True,
        "credential_authority": "TV/TVC",
        "claim_fence_authority": "WORKERCOORDINATOR",
        "transition_authority": "INTERLOCK_INTR",
        "custody_replay_reconstruction_authority": "MASTER_RECORDS",
        "request_grants_authority": False,
        "sdk_executes_lifecycle": False,
        "authority_effect": "NONE_MANIFEST_RUNTIME_REQUEST_ONLY",
    }
    request["request_sha256"] = mod.sha256(request)
    return request


def custody_rows():
    counter = {"n": 0}

    def fake(**kwargs):
        counter["n"] += 1
        digit = str(counter["n"])
        receipt_sha = digit * 64
        org_sha = ("a" if counter["n"] == 1 else "b") * 64
        return {
            "receipt": {
                "transition_id": kwargs["transition_id"],
                "transition_outcome": kwargs["outcome"],
            },
            "custody": {
                "state": "RECORDED",
                "reconstruction_status": "PASS",
                "required_evidence_validation_status": "PASS",
                "receipt_sha256": receipt_sha,
                "reconstructed_receipt_sha256": receipt_sha,
                "organization_receipt": {
                    "receipt_sha256": org_sha,
                    "previous_receipt_sha256": kwargs["prior"],
                },
            },
        }

    return fake


class GovernanceUniversalInTrBindingTests(unittest.TestCase):
    def transport(self):
        return {
            "origin": "TVC_RELAY_EGRESS",
            "authorization_id": "TVC-AUTH-EXACT",
            "payload_sha256": "c" * 64,
        }

    def test_authenticated_governance_allow_is_org_then_master_records_closed(self):
        request = governance_request()
        governance = {
            "governance_state": "ALLOW",
            "manifest_receipt_id": "MR-GOV-1",
            "transaction_id": "TX-GOV-1",
            "result_binding_hash": "sha256:" + "d" * 64,
            "master_records_custody_status": "RECORDED",
            "chain_verified": True,
            "external_side_effect": False,
        }
        with tempfile.TemporaryDirectory() as td, \
             patch.object(mod, "_run_governance_owner", return_value=governance), \
             patch.object(mod, "_custody_transition", side_effect=custody_rows()):
            result = mod.execute(Path(td), request, transport=self.transport())
        self.assertEqual(result["disposition"], "ALLOW")
        self.assertEqual(result["subject_or_correlation_id"], GOAL)
        self.assertTrue(result["organization_records_before_master_records"])
        self.assertTrue(result["organization_master_records_closure_observed"])
        self.assertFalse(result["publisher_executed"])
        self.assertFalse(result["site_propagation_executed"])
        self.assertEqual(
            result["resolved_ordered_transitions"],
            ["INGRESS_ADMITTED", "GOVERNANCE_DISPOSITION"],
        )
        self.assertEqual(result["transition_closures"][1]["predecessor_receipt_sha256"], "1" * 64)
        self.assertEqual(
            result["transition_closures"][1]["organization_predecessor_receipt_sha256"],
            "a" * 64,
        )

    def test_canonical_governance_deny_is_preserved_not_laundered(self):
        request = governance_request()
        governance = {
            "governance_state": "DENY",
            "manifest_receipt_id": "MR-GOV-2",
            "transaction_id": "TX-GOV-2",
            "result_binding_hash": "sha256:" + "e" * 64,
            "master_records_custody_status": "RECORDED",
            "chain_verified": True,
            "external_side_effect": False,
        }
        with tempfile.TemporaryDirectory() as td, \
             patch.object(mod, "_run_governance_owner", return_value=governance), \
             patch.object(mod, "_custody_transition", side_effect=custody_rows()):
            result = mod.execute(Path(td), request, transport=self.transport())
        self.assertEqual(result["disposition"], "DENY")
        self.assertTrue(result["terminal"])
        self.assertTrue(result["organization_master_records_closure_observed"])

    def test_existing_owner_execution_failure_returns_actionable_fail_closed(self):
        request = governance_request()
        with tempfile.TemporaryDirectory() as td, \
             patch.object(mod, "_run_governance_owner", side_effect=RuntimeError("source roots not bound")), \
             patch.object(mod, "_custody_transition", side_effect=custody_rows()):
            result = mod.execute(Path(td), request, transport=self.transport())
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["reason_code"], "CANONICAL_GOVERNANCE_OWNER_EXECUTION_FAILED")
        self.assertEqual(
            result["failed_predicate"],
            "MANIFEST_SELECTED_CAPABILITY_EXECUTION_OWNER_BOUND_AND_EXECUTABLE",
        )
        self.assertTrue(result["organization_master_records_closure_observed"])

    def test_governance_requires_authenticated_tvc_relay_transport(self):
        request = governance_request()
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "AUTHENTIC_INTR_TRANSPORT_EVIDENCE_REQUIRED"):
                mod.execute(Path(td), request)
            with self.assertRaisesRegex(ValueError, "CANONICAL_GOVERNANCE_REQUIRES_TVC_RELAY_EGRESS"):
                mod.execute(
                    Path(td),
                    request,
                    transport={"origin": "STEGOS_NODE_OUTBOX", "authorization_id": None},
                )


if __name__ == "__main__":
    unittest.main()
