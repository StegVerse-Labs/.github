from __future__ import annotations

import os
import tempfile
import unittest
from types import SimpleNamespace
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



ORG_BATCH_TASK = "ORGANIZATION-BATCH-CUSTODY-REPLAY-001"


def organization_batch_governance_request() -> dict:
    request = governance_request()
    payload = {
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": "RESIDENT-EXEC-ORGANIZATION-BATCH-CUSTODY-REPLAY-001",
        "state": "REQUESTED",
        "task_id": ORG_BATCH_TASK,
        "cosv_profile": "task.v1",
        "cosv_task_vector": "10000000100000",
        "pointer_source": "data/canonical-task-records/ORGANIZATION-BATCH-CUSTODY-REPLAY-001.json",
        "mode": "CANONICAL_WORK_EVENT_BOOTSTRAP",
        "entrypoint": "scripts/install_and_run_canonical_work_event_bootstrap.py",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    manifest_body = {
        "manifest_profile": "stegverse.ingress-manifest.v1",
        "source_output_id": payload["request_id"],
        "payload": payload,
        "extensions": {
            "stegverse_canonical_task": {
                "task_id": ORG_BATCH_TASK,
                "correlation_id": ORG_BATCH_TASK,
                "registry_repository": "StegVerse-Labs/.github",
                "observed_registry_generation": 278,
                "cosv_task_vector": "10000000100000",
                "canonical_request_ref": mod.ORGANIZATION_BATCH_REQUEST_REF,
                "authority_effect": "NONE",
            },
            mod.ORGANIZATION_BATCH_POLICY_EXTENSION: {
                "release_condition": {"type": "COUNT", "count": 1}
            },
        },
    }
    manifest_hash = mod.sha256(manifest_body)
    manifest = dict(manifest_body)
    manifest["canonical_manifest_sha256"] = manifest_hash
    batch = manifest_body["extensions"][mod.ORGANIZATION_BATCH_POLICY_EXTENSION]
    graph = {
        "schema": "stegverse.sdk.installed-state-transition-graph/v1",
        "graph_id": "RTC-GOVERNED-PROCESSING-002:" + ORG_BATCH_TASK,
        "canonical_task_id": ORG_BATCH_TASK,
        "processing_capability": "governance",
        "route_id": mod.GOVERNANCE_ROUTE_ID,
        "request": {
            "canonical_task_binding": {
                "task_id": ORG_BATCH_TASK,
                "observed_registry_generation": 278,
                "cosv_task_vector": "10000000100000",
                "canonical_request_ref": mod.ORGANIZATION_BATCH_REQUEST_REF,
                "original_request_sha256": mod.sha256(payload),
                "receipt_batch": batch,
            },
            "authority_effect": "NONE_PUBLIC_GOVERNANCE_REQUEST_ONLY",
        },
        "ordered_transitions": [],
        "requires_workercoordinator_claim_fence": False,
        "predecessor_closure_required": True,
        "adapter_executes_lifecycle": False,
        "authority_effect": "NONE_GRAPH_DERIVATION_ONLY",
    }
    request.update({
        "canonical_manifest": manifest,
        "canonical_manifest_sha256": manifest_hash,
        "state_graph": graph,
        "graph_id": graph["graph_id"],
        "canonical_task_id": ORG_BATCH_TASK,
    })
    request["request_sha256"] = mod.sha256({k: v for k, v in request.items() if k != "request_sha256"})
    return request

REAL_CUSTODY_TRANSITION = mod._custody_transition


def custody_rows():
    """The real producer: each transition appends to the tmp Organization ledger root."""
    def real(**kwargs):
        return REAL_CUSTODY_TRANSITION(**kwargs)

    return real


class GovernanceUniversalInTrBindingTests(unittest.TestCase):
    def setUp(self):
        # Ledger roots are supplied, never derived from the host.
        ledger = tempfile.TemporaryDirectory()
        self.addCleanup(ledger.cleanup)
        env = patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": ledger.name})
        env.start()
        self.addCleanup(env.stop)

    def transport(self):
        return {
            "origin": "TVC_RELAY_EGRESS",
            "authorization_id": "TVC-AUTH-EXACT",
            "payload_sha256": "c" * 64,
        }

    def test_authenticated_governance_allow_is_org_then_master_records_recorded(self):
        request = governance_request()
        governance = {
            "governance_state": "ALLOW",
            "manifest_receipt_id": "MR-GOV-1",
            "transaction_id": "TX-GOV-1",
            "result_binding_hash": "sha256:" + "d" * 64,
            "master_records_organization_record_status": "RECORDED",
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
        self.assertTrue(result["organization_master_records_organization_record_observed"])
        self.assertFalse(result["publisher_executed"])
        self.assertFalse(result["site_propagation_executed"])
        self.assertEqual(
            result["resolved_ordered_transitions"],
            ["INGRESS_ADMITTED", "GOVERNANCE_DISPOSITION"],
        )
        first, second = result["transition_closures"][0], result["transition_closures"][1]
        self.assertEqual(second["predecessor_receipt_sha256"], first["receipt_sha256"])
        self.assertEqual(second["organization_predecessor_receipt_sha256"], first["organization_receipt_sha256"])

    def test_canonical_governance_deny_is_preserved_not_laundered(self):
        request = governance_request()
        governance = {
            "governance_state": "DENY",
            "manifest_receipt_id": "MR-GOV-2",
            "transaction_id": "TX-GOV-2",
            "result_binding_hash": "sha256:" + "e" * 64,
            "master_records_organization_record_status": "RECORDED",
            "chain_verified": True,
            "external_side_effect": False,
        }
        with tempfile.TemporaryDirectory() as td, \
             patch.object(mod, "_run_governance_owner", return_value=governance), \
             patch.object(mod, "_custody_transition", side_effect=custody_rows()):
            result = mod.execute(Path(td), request, transport=self.transport())
        self.assertEqual(result["disposition"], "DENY")
        self.assertTrue(result["terminal"])
        self.assertTrue(result["organization_master_records_organization_record_observed"])

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
        self.assertTrue(result["organization_master_records_organization_record_observed"])


    def test_organization_batch_allow_executes_manifest_directed_action_without_second_governance(self):
        request = organization_batch_governance_request()
        governance = {
            "governance_state": "ALLOW",
            "manifest_receipt_id": "MR-ORG-BATCH-ALLOW",
            "transaction_id": "TX-ORG-BATCH-ALLOW",
            "result_binding_hash": "sha256:" + "f" * 64,
            "master_records_organization_record_status": "RECORDED",
            "chain_verified": True,
            "external_side_effect": False,
        }
        calls = []

        def aggregate(receipt, **kwargs):
            calls.append((receipt, kwargs))
            return {
                "schema": "stegverse.organization-transition-receipt/v1",
                "receipt_sha256": "sha256:" + "9" * 64,
                "previous_receipt_sha256": "sha256:" + "8" * 64,
                "source_transition_sha256": "sha256:" + "7" * 64,
                "boundary_evidence": {
                    "parent_manifest_released_batch": {
                        "batch_id": "sha256:" + "6" * 64,
                        "execution_result": "COMPLETED",
                        "reason": None,
                        "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
                    }
                },
            }

        with tempfile.TemporaryDirectory() as td, \
             patch.object(mod, "_run_governance_owner", return_value=governance), \
             patch.object(mod, "_custody_transition", side_effect=custody_rows()), \
             patch.object(
                 mod,
                 "_load_organization_append_owner",
                 return_value=SimpleNamespace(aggregate_transition=aggregate),
             ):
            result = mod.execute(Path(td), request, transport=self.transport())

        self.assertEqual(result["disposition"], "ALLOW")
        action = result["manifest_directed_action"]
        self.assertEqual(action["execution_result"], "COMPLETED")
        self.assertIsNone(action["governance_disposition"])
        self.assertEqual(action["canonical_manifest_sha256"], request["canonical_manifest_sha256"])
        self.assertEqual(action["released_batch"]["execution_result"], "COMPLETED")
        self.assertEqual(len(calls), 1)
        receipt, kwargs = calls[0]
        self.assertEqual(receipt["transition_id"], "MANIFEST_DIRECTED_ORGANIZATION_APPEND_COMPLETED")
        self.assertEqual(
            receipt["governance_decision_ref_where_applicable"],
            "sha256:" + result["transition_closures"][1]["receipt_sha256"],
        )
        self.assertEqual(
            kwargs["parent_manifest"]["receipt_batch"]["release_condition"],
            {"type": "COUNT", "count": 1},
        )
        self.assertEqual(kwargs["boundary_evidence"]["parent_governance_disposition"], "ALLOW")

    def test_organization_batch_deny_does_not_execute_downstream_action(self):
        request = organization_batch_governance_request()
        governance = {
            "governance_state": "DENY",
            "manifest_receipt_id": "MR-ORG-BATCH-DENY",
            "transaction_id": "TX-ORG-BATCH-DENY",
            "result_binding_hash": "sha256:" + "e" * 64,
            "master_records_organization_record_status": "RECORDED",
            "chain_verified": True,
            "external_side_effect": False,
        }
        with tempfile.TemporaryDirectory() as td, \
             patch.object(mod, "_run_governance_owner", return_value=governance), \
             patch.object(mod, "_custody_transition", side_effect=custody_rows()), \
             patch.object(mod, "_load_organization_append_owner") as owner:
            result = mod.execute(Path(td), request, transport=self.transport())
        self.assertEqual(result["disposition"], "DENY")
        self.assertNotIn("manifest_directed_action", result)
        owner.assert_not_called()

    def test_organization_batch_append_failure_preserves_parent_allow_and_custodies_failure(self):
        request = organization_batch_governance_request()
        governance = {
            "governance_state": "ALLOW",
            "manifest_receipt_id": "MR-ORG-BATCH-ALLOW-FAIL",
            "transaction_id": "TX-ORG-BATCH-ALLOW-FAIL",
            "result_binding_hash": "sha256:" + "d" * 64,
            "master_records_organization_record_status": "RECORDED",
            "chain_verified": True,
            "external_side_effect": False,
        }

        def fail(*args, **kwargs):
            raise RuntimeError("ORGANIZATION_BATCH_AUTHENTIC_CUSTODY_SURFACE_UNAVAILABLE")

        with tempfile.TemporaryDirectory() as td, \
             patch.object(mod, "_run_governance_owner", return_value=governance), \
             patch.object(mod, "_custody_transition", side_effect=custody_rows()) as custody, \
             patch.object(
                 mod,
                 "_load_organization_append_owner",
                 return_value=SimpleNamespace(aggregate_transition=fail),
             ):
            result = mod.execute(Path(td), request, transport=self.transport())

        self.assertEqual(result["disposition"], "ALLOW")
        action = result["manifest_directed_action"]
        self.assertEqual(action["execution_result"], "FAILED")
        self.assertIsNone(action["governance_disposition"])
        self.assertEqual(
            action["failed_predicate"],
            "MANIFEST_DIRECTED_ORGANIZATION_APPEND_COMPLETED",
        )
        self.assertEqual(custody.call_count, 4)
        self.assertEqual(
            action["failure_closure"]["transition_id"],
            "MANIFEST_DIRECTED_ORGANIZATION_APPEND_FAILED",
        )

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
