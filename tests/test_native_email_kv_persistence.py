from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import persist_native_email_incidents_to_kv as kv
from scripts import run_native_email_action_monitor_kv_guard as guard


INCIDENT = {
    "incident_id": "INC-GITHUB-FAILURE-EXAMPLE",
    "kind": "GITHUB_FAILURE_EMAIL_CLUSTER",
    "normalized_repository": "StegVerse-Labs/example",
    "normalized_workflow": "validation",
    "normalized_error_signature": "unit-test-failure",
    "observation_count": 2,
    "observation_refs": ["gmail-message-2", "gmail-message-1"],
    "state": "INCIDENT_PROPOSED_NOT_ADMITTED",
    "task_ingress_required": True,
    "email_observation_is_execution_evidence": False,
    "incident_proposal_mints_execution_authority": False,
}


class FakeInner:
    def __init__(self, kv_root: Path):
        self.kv_root = kv_root
        self.calls: list[str] = []
        self.archive_saw_persisted_record = False
        self.archive_payload = None

    def call(self, operation: str, **payload):
        self.calls.append(operation)
        if operation == "ARCHIVE_IDS":
            self.archive_payload = dict(payload)
            records = list((self.kv_root / kv.KV_RELATIVE_ROOT).glob("*.json"))
            self.archive_saw_persisted_record = bool(records)
            return {
                "schema": "stegverse.native-email-broker-response/v1",
                "operation": operation,
                "credential_authority": "TV/TVC",
                "credential_material_exported": False,
                "provider_operation_authority_transferred": False,
                "archived_ids": list(payload.get("message_ids") or []),
                "failed_ids": [],
            }
        raise AssertionError(operation)


class NativeEmailKVPersistenceTests(unittest.TestCase):
    def knowledge_vault(self, base: Path) -> Path:
        root = base / "KnowledgeVault"
        (root / "_System").mkdir(parents=True)
        return root

    def test_writer_is_append_only_idempotent_and_exact_byte_verified(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.knowledge_vault(Path(td))
            first = kv.persist_incident(INCIDENT, kv_root=root)
            second = kv.persist_incident(INCIDENT, kv_root=root)
            self.assertEqual(first["state"], "KV_STORED_VERIFIED")
            self.assertEqual(first["result"], "STORED_VERIFIED")
            self.assertTrue(first["exact_byte_readback_verified"])
            self.assertEqual(second["result"], "NOOP_EXISTING_IDENTICAL")
            self.assertEqual(first["record_hash"], second["record_hash"])
            self.assertEqual(first["relative_path"], second["relative_path"])

    def test_archive_call_happens_only_after_kv_record_exists_and_binds_governance_context(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.knowledge_vault(Path(td))
            inner = FakeInner(root)
            wrapped = guard.KVGuardedBroker(inner, root)
            wrapped.live_incidents = [dict(INCIDENT)]
            reviewed = ["gmail-message-1", "gmail-message-2"]
            result = wrapped.call("ARCHIVE_IDS", message_ids=reviewed)
            self.assertTrue(inner.archive_saw_persisted_record)
            self.assertEqual(result["archived_ids"], reviewed)
            self.assertEqual(len(wrapped.kv_receipts), 1)
            self.assertTrue(wrapped.kv_receipts[0]["exact_byte_readback_verified"])
            context = inner.archive_payload["governance_context"]
            self.assertEqual(context["schema"], guard.ARCHIVE_CONTEXT_SCHEMA)
            self.assertEqual(context["task_id"], guard.TASK_ID)
            self.assertEqual(context["cosv_task_vector"], guard.COSV_TASK_VECTOR)
            self.assertEqual(context["reviewed_message_ids"], reviewed)
            self.assertEqual(context["incident_count"], 1)
            self.assertEqual(context["kv_write_receipts"], wrapped.kv_receipts)
            self.assertTrue(context["kv_before_archive_required"])
            self.assertFalse(context["credential_material_present"])

    def test_zero_incident_archive_still_binds_exact_reviewed_set(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.knowledge_vault(Path(td))
            inner = FakeInner(root)
            wrapped = guard.KVGuardedBroker(inner, root)
            wrapped.live_incidents = []
            wrapped.call("ARCHIVE_IDS", message_ids=["informational-message"])
            context = inner.archive_payload["governance_context"]
            self.assertEqual(context["reviewed_message_ids"], ["informational-message"])
            self.assertEqual(context["incident_count"], 0)
            self.assertEqual(context["kv_write_receipts"], [])

    def test_missing_kv_fails_before_archive_provider_call(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing-KnowledgeVault"
            inner = FakeInner(missing)
            wrapped = guard.KVGuardedBroker(inner, missing)
            wrapped.live_incidents = [dict(INCIDENT)]
            # The guard imports the writer as a top-level script module while this
            # test imports it through the namespace package, so the concrete custom
            # exception class has two Python module identities. RuntimeError is the
            # stable public failure contract across both import paths.
            with self.assertRaisesRegex(RuntimeError, "kv_root_not_materialized"):
                wrapped.call("ARCHIVE_IDS", message_ids=["gmail-message-1"])
            self.assertEqual(inner.calls, [])


if __name__ == "__main__":
    unittest.main()
