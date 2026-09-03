from __future__ import annotations

import base64
import json
from pathlib import Path
import tempfile
import unittest

from heartbeat_runtime.blocker_policy import (
    RESOLUTION_EVIDENCE_PREFIX,
    validate_worker_response_blocker,
)
from heartbeat_runtime.engine_v10 import HeartbeatRuntime, WorkerResponse


def _resolution_ref(contract: dict) -> str:
    raw = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return RESOLUTION_EVIDENCE_PREFIX + base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _handoff(task_id: str, *, depth: int = 0, level: str | None = None) -> dict:
    source_refs = ["source:test"]
    if level:
        source_refs.append(f"resolution-level:{level}")
    return {
        "schema": "stegverse.executable-handoff/v0.1",
        "handoff_id": f"HANDOFF-{task_id}",
        "created_at": "2026-08-12T16:00:00Z",
        "state": "HANDOFF_READY",
        "goal": {
            "goal_id": "GOAL-1",
            "objective": "Complete the originating goal.",
            "success_predicates": ["goal complete"],
            "failure_predicates": ["goal abandoned"],
            "expires_at": None,
            "authority_ceiling": ["test_scope"],
            "successor_policy": "SEPARATE_AUTHORIZATION_REQUIRED_FOR_EXPANSION",
            "max_successor_depth": 8,
        },
        "task": {
            "task_id": task_id,
            "repository": "StegVerse-Labs/.github",
            "source_refs": source_refs,
            "dependencies": [],
            "parent_task_id": None,
            "derivation_reason": None,
            "canonical_owner_ref": "test-owner",
            "canonical_lineage_key": "test-lineage",
            "derivation_depth": depth,
            "priority": "critical",
        },
        "authority": {
            "authority_source": "test-authority",
            "heartbeat_grants_execution_authority": False,
            "policy_version": "test-policy-v1",
        },
        "execution": {
            "required_capabilities": ["test_resolution"],
            "allowed_paths": ["control/**", "handoffs/generated/**", "cost-basis/generated/**"],
            "allowed_services": [],
            "max_actions": 10,
            "max_retries": 2,
            "external_cost_ceiling_usd": 0,
            "runtime_window_beats": 16,
            "rate_class": "test",
        },
        "activation": {
            "carrier": "heartbeat",
            "executor_binding": "AUTHORIZED",
            "authorization_ref": "control/blocker-resolution-policy.json",
            "recheck_trigger": "each heartbeat",
            "checkout_policy": "fenced_atomic_checkout",
        },
        "continuity": {
            "checkpoint_ref": None,
            "handoff_destination": "control/worker-registry.json",
            "master_records_required": True,
            "status_projection": "control/worker-status.json",
        },
        "completion": {
            "next_authorized_action": "continue",
            "terminal_when": ["goal complete"],
        },
        "block": None,
    }


class BlockerResolutionContractTests(unittest.TestCase):
    def test_blocked_response_carries_machine_readable_resolution_contract(self):
        response = {
            "schema": "stegverse.worker-response/v0.1",
            "state": "BLOCKED",
            "transition_id": "POLICY_CONSTRAINT",
            "transition_sequence": 2,
            "blocker": {
                "trigger_type": "FAIL_CLOSED",
                "dependency_class": "SAFETY_POLICY",
                "problem_statement": "Current consequence would violate a safety predicate.",
                "solution_required": True,
                "workaround_candidates": ["derive a compliant alternate route"],
                "next_solution_action": "derive alternate route",
                "resolvable_by_current_worker": False,
                "escalation_target": "COMPONENT_AUTHORITY",
            },
        }
        validate_worker_response_blocker(response)
        refs = response["evidence_refs"]
        self.assertEqual(len(refs), 1)
        self.assertTrue(refs[0].startswith(RESOLUTION_EVIDENCE_PREFIX))

    def test_resolution_task_failure_escalates_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = HeartbeatRuntime(tmp)
            parent = _handoff("RESOLVE-1", depth=1, level="WORKER")
            contract = {
                "resolvable_by_current_worker": True,
                "same_level_retry_authorized": False,
                "workaround_candidate_changed": False,
            }
            self.assertEqual(runtime._target_level(parent, contract), "REPOSITORY_OWNER")

    def test_irreconcilable_governance_collision_escalates_to_human(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = HeartbeatRuntime(tmp)
            parent = _handoff("ESCALATE-4", depth=4, level="ECOSYSTEM_GOVERNANCE")
            contract = {"resolvable_by_current_worker": False}
            self.assertEqual(runtime._target_level(parent, contract), "HUMAN_AUTHORITY")


class RuntimeResolutionTaskTests(unittest.TestCase):
    def test_blocked_worker_is_converted_to_registered_resolution_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoffs").mkdir(parents=True)
            parent_handoff = _handoff("PARENT-1")
            (root / "handoffs" / "parent.json").write_text(json.dumps(parent_handoff), encoding="utf-8")

            contract = {
                "trigger_type": "CONDITIONAL_CONSTRAINT",
                "dependency_class": "INTERNAL_CAPABILITY",
                "problem_statement": "Required internal route is absent.",
                "solution_required": True,
                "workaround_candidates": ["construct the route"],
                "next_solution_action": "construct and validate the route",
                "resolvable_by_current_worker": True,
                "required_capabilities": ["test_resolution"],
                "completion_evidence": ["route exists and validates"],
            }
            ref = _resolution_ref(contract)

            def adapter(task, handoff, epoch):
                return WorkerResponse(
                    state="BLOCKED",
                    transition_id="CONSTRAINT",
                    transition_sequence=1,
                    evidence_refs=(ref,),
                )

            runtime = HeartbeatRuntime(root, adapters={"fake": adapter})
            registry = {
                "generation": 1,
                "workers": [{
                    "worker_id": "worker-1",
                    "status": "BUSY",
                    "adapter_ref": "fake",
                    "capabilities": ["test_resolution"],
                }],
                "tasks": [],
            }
            parent = {
                "task_id": "PARENT-1",
                "goal_id": "GOAL-1",
                "state": "ACTIVE",
                "handoff_ref": "handoffs/parent.json",
                "executor_binding": "BOUND",
                "worker_id": "worker-1",
                "worker_instance_id": "worker-1-HB1-G1",
                "claim_id": "CLAIM-PARENT-1-G1",
                "heartbeat_timing": {
                    "start_epoch": 1,
                    "last_response_epoch": 1,
                    "last_transition_epoch": 1,
                    "current_transition": "ACTIVE",
                    "transition_sequence": 0,
                    "max_missing_response_beats": 2,
                    "expiry_epoch": 100,
                    "expiry_basis": "TASK_CLASS_COST_BASIS",
                    "fencing_token": 1,
                    "renewal_count": 0,
                },
                "archive_eligible": False,
                "archive_reason_codes": [],
                "evidence_refs": [],
            }
            registry["tasks"].append(parent)
            cost_log = {"generation": 0, "records": []}
            events = []

            runtime._invoke(registry, parent, 2, cost_log, events)

            self.assertEqual(parent["state"], "ACTIVATION_PENDING")
            self.assertIsNone(parent["worker_id"])
            children = [task for task in registry["tasks"] if task["task_id"] != "PARENT-1"]
            self.assertEqual(len(children), 1)
            self.assertEqual(children[0]["state"], "HANDOFF_READY")
            self.assertTrue(children[0]["task_id"].startswith("RESOLVE-PARENT-1-"))
            preflight_refs = [
                ref for ref in children[0]["evidence_refs"]
                if isinstance(ref, str) and ref.startswith("receipts/stegindex-preflight/")
            ]
            self.assertEqual(len(preflight_refs), 1)
            preflight_receipt = json.loads((root / preflight_refs[0]).read_text(encoding="utf-8"))
            self.assertEqual(preflight_receipt["preflight"]["state"], "PREFLIGHT_UNAVAILABLE")
            self.assertFalse(preflight_receipt["preflight"]["source_unavailable_is_implementation_missing"])
            admitted = [event for event in events if event["event_type"] == "resolution_task_admitted"]
            self.assertEqual(len(admitted), 1)
            self.assertEqual(admitted[0]["stegindex_preflight_ref"], preflight_refs[0])


if __name__ == "__main__":
    unittest.main()
