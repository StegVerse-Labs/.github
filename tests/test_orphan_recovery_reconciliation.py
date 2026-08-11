from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from heartbeat_runtime.orphan_recovery import (
    RECOVERY_ONLY_CAPABILITY,
    RECOVERY_REQUIRED_CODES,
    orphan_recovery_contract_valid,
    reconcile_quarantined_orphan_recoveries,
)

PARENT_ID = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
RECOVERY_ID = "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28"
PARENT_REF = "handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json"
RECOVERY_REF = f"handoffs/generated/{RECOVERY_ID}.json"
AUTH_REF = f"authorizations/{RECOVERY_ID}.json"
CHECKPOINT = "checkpoints/workers/SHWP-ECOSYSTEM-CHAT-INFERENCE-001/HB25-G20.json"


def parent_handoff() -> dict:
    return {
        "goal": {
            "authority_ceiling": ["bounded sovereign inference observation", "no_external_model_provider_authority"],
        },
        "task": {
            "task_id": PARENT_ID,
            "repository": "StegVerse-Labs/.github",
            "canonical_owner_ref": "StegVerse-org/LLM-adapter#18",
        },
        "authority": {
            "authority_source": "StegVerse-org/LLM-adapter#18 + StegVerse-002/micro-node-runtime#16/#22",
            "heartbeat_grants_execution_authority": False,
            "policy_version": "shwp-single-hb-v0.3-sovereign",
        },
        "execution": {
            "required_capabilities": ["runtime_observation", "durable_state_reconstruction", "bounded_repository_mutation"],
            "allowed_paths": ["receipts/ecosystem-chat-sovereign-inference/**"],
            "allowed_services": [],
            "max_actions": 64,
            "max_retries": 4096,
            "external_cost_ceiling_usd": 0,
            "runtime_window_beats": 4096,
        },
    }


def recovery_handoff() -> dict:
    return {
        "schema": "stegverse.executable-handoff/v0.1",
        "state": "BLOCKED",
        "goal": {
            "authority_ceiling": ["bounded sovereign inference observation"],
            "successor_policy": "NONE",
        },
        "task": {
            "task_id": RECOVERY_ID,
            "repository": "StegVerse-Labs/.github",
            "canonical_owner_ref": "StegVerse-org/LLM-adapter#18",
            "recovery_parent_task_id": PARENT_ID,
            "source_refs": [PARENT_REF, CHECKPOINT, AUTH_REF, "master-records/orchestration:custody/worker-lifecycle/SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001.json"],
            "derivation_depth": 0,
        },
        "authority": {
            "authority_source": "StegVerse-org/LLM-adapter#18 + StegVerse-002/micro-node-runtime#16/#22",
            "heartbeat_grants_execution_authority": False,
            "policy_version": "shwp-single-hb-v0.3-sovereign",
        },
        "execution": {
            "required_capabilities": [RECOVERY_ONLY_CAPABILITY],
            "allowed_paths": ["receipts/ecosystem-chat-sovereign-inference/**"],
            "allowed_services": [],
            "max_actions": 32,
            "max_retries": 2048,
            "external_cost_ceiling_usd": 0,
            "runtime_window_beats": 2048,
        },
        "activation": {"executor_binding": "AUTHORIZED", "authorization_ref": AUTH_REF},
        "continuity": {
            "checkpoint_ref": CHECKPOINT,
            "master_records_required": True,
            "master_records_custody_ref": "master-records/orchestration:custody/worker-lifecycle/SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001.json",
        },
        "block": {
            "block_reason": "ORPHAN_RECOVERY_EXECUTOR_AUTHORIZATION_REQUIRED",
            "dependency": f"file:{AUTH_REF}",
        },
    }


def recovery_authorization() -> dict:
    return {
        "schema": "stegverse.bounded-worker-authorization/v0.1",
        "state": "ADMITTED",
        "task_id": RECOVERY_ID,
        "parent_task_id": PARENT_ID,
        "authority_source": "StegVerse-org/LLM-adapter#18 + StegVerse-002/micro-node-runtime#16/#22",
        "allowed_capabilities": [RECOVERY_ONLY_CAPABILITY],
        "allowed_paths": ["receipts/ecosystem-chat-sovereign-inference/**"],
        "allowed_services": [],
        "old_fencing_token": 20,
        "old_authority_revival_allowed": False,
        "parent_task_execution_authority": False,
        "successor_parent_authority_granted": False,
        "heartbeat_grants_execution_authority": False,
        "availability_grants_execution_authority": False,
        "github_token_required": False,
        "authority_effect": "CONTINUITY_RECONSTRUCTION_ONLY",
    }


def registry() -> dict:
    return {
        "tasks": [
            {
                "task_id": PARENT_ID,
                "state": "BLOCKED",
                "handoff_ref": PARENT_REF,
                "claim_id": None,
                "worker_id": None,
                "worker_instance_id": None,
                "last_checkpoint_ref": CHECKPOINT,
                "archive_reason_codes": ["WORKER_ORPHANED", "OLD_AUTHORITY_RELEASED", "RECOVERY_RECONSTRUCTION_REQUIRED"],
            },
            {
                "task_id": RECOVERY_ID,
                "state": "QUARANTINED",
                "handoff_ref": RECOVERY_REF,
                "claim_id": None,
                "worker_id": None,
                "worker_instance_id": None,
                "archive_reason_codes": ["SUCCESSOR_DEPTH_LIMIT_EXCEEDED"],
            },
        ]
    }


def write_fixture(root: Path, *, recovery: dict | None = None, authorization: dict | None = None) -> None:
    parent_path = root / PARENT_REF
    recovery_path = root / RECOVERY_REF
    auth_path = root / AUTH_REF
    parent_path.parent.mkdir(parents=True, exist_ok=True)
    recovery_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    parent_path.write_text(json.dumps(parent_handoff()), encoding="utf-8")
    recovery_path.write_text(json.dumps(recovery or recovery_handoff()), encoding="utf-8")
    auth_path.write_text(json.dumps(authorization or recovery_authorization()), encoding="utf-8")


class OrphanRecoveryReconciliationTests(unittest.TestCase):
    def test_authorized_recovery_root_is_reconciled_to_blocked_not_parent_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_fixture(root)
            reg = registry()
            valid, reason = orphan_recovery_contract_valid(root, registry_task=reg["tasks"][1], registry=reg)
            self.assertTrue(valid, reason)
            events: list[dict] = []
            reconciled = reconcile_quarantined_orphan_recoveries(
                root,
                reg,
                epoch=30,
                event=lambda epoch, event_type, **payload: events.append({"epoch": epoch, "event_type": event_type, **payload}),
            )
            self.assertEqual(reconciled, [RECOVERY_ID])
            task = reg["tasks"][1]
            self.assertEqual(task["state"], "BLOCKED")
            self.assertEqual(task["archive_reason_codes"], RECOVERY_REQUIRED_CODES)
            self.assertIsNone(task["claim_id"])
            self.assertIsNone(task["worker_id"])
            self.assertEqual(events[-1]["event_type"], "orphan_recovery_quarantine_reconciled")
            self.assertFalse(events[-1]["old_authority_reused"])
            self.assertFalse(events[-1]["successor_authority_granted"])

    def test_scope_expansion_remains_quarantined(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bad = recovery_handoff()
            bad["execution"]["allowed_paths"].append("**")
            write_fixture(root, recovery=bad)
            reg = registry()
            valid, reason = orphan_recovery_contract_valid(root, registry_task=reg["tasks"][1], registry=reg)
            self.assertFalse(valid)
            self.assertEqual(reason, "RECOVERY_SCOPE_EXPANSION_DETECTED")
            self.assertEqual(reconcile_quarantined_orphan_recoveries(root, reg, epoch=30), [])

    def test_live_old_claim_prevents_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_fixture(root)
            reg = registry()
            reg["tasks"][0]["claim_id"] = "old-claim-must-not-live"
            valid, reason = orphan_recovery_contract_valid(root, registry_task=reg["tasks"][1], registry=reg)
            self.assertFalse(valid)
            self.assertEqual(reason, "RECOVERY_PARENT_OLD_AUTHORITY_NOT_ENDED")

    def test_goal_successor_shape_is_rejected_for_orphan_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bad = recovery_handoff()
            bad["task"]["parent_task_id"] = PARENT_ID
            bad["task"]["derivation_depth"] = 1
            write_fixture(root, recovery=bad)
            reg = registry()
            valid, reason = orphan_recovery_contract_valid(root, registry_task=reg["tasks"][1], registry=reg)
            self.assertFalse(valid)
            self.assertEqual(reason, "RECOVERY_MUST_BE_CONTINUITY_ROOT_NOT_SUCCESSOR")

    def test_authorization_cannot_enable_old_authority_or_github_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bad_auth = recovery_authorization()
            bad_auth["old_authority_revival_allowed"] = True
            bad_auth["github_token_required"] = True
            write_fixture(root, authorization=bad_auth)
            reg = registry()
            valid, reason = orphan_recovery_contract_valid(root, registry_task=reg["tasks"][1], registry=reg)
            self.assertFalse(valid)
            self.assertEqual(reason, "RECOVERY_BOUNDED_AUTHORIZATION_INVALID")


if __name__ == "__main__":
    unittest.main()
