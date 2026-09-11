from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wrapper = load("native_email_kv_wrapper", "scripts/consume_native_email_action_monitor_request_kv.py")
trigger = load("native_email_reusable_trigger", "scripts/trigger_reusable_task.py")


class NativeEmailKVEntrypointTests(unittest.TestCase):
    def test_standing_request_uses_kv_enforcing_entrypoint(self):
        request = json.loads((ROOT / "control/resident-execution-request.d/native-email-action-monitor-001.json").read_text(encoding="utf-8"))
        self.assertEqual(request["task_id"], "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001")
        self.assertEqual(request["entrypoint"], "scripts/consume_native_email_action_monitor_request_kv.py")
        self.assertTrue(request["standing_request"])

    def test_runtime_materialization_receipt_resolves_existing_kv_without_env_hop(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"
            kv_root = base / "KnowledgeVault"
            (runtime / "control/kv-provider-materialization").mkdir(parents=True)
            (kv_root / "_System").mkdir(parents=True)
            receipt = {
                "schema": "stegverse.kv.provider-materialization-receipt/v2",
                "materialized_root": str(kv_root),
                "exact_readback_verified": True,
                "credential_authority": "TV/TVC",
                "credential_material_persisted": False,
                "consumer_received_provider_credential": False,
            }
            (runtime / wrapper.KV_RECEIPT_REL).write_text(json.dumps(receipt) + "\n", encoding="utf-8")
            resolved, source = wrapper.resolve_kv_root(runtime, {})
            self.assertEqual(resolved, kv_root.resolve())
            self.assertEqual(source, "RUNTIME_CONTROL_RECEIPT")

    def test_invalid_materialization_receipt_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            (runtime / "control/kv-provider-materialization").mkdir(parents=True)
            (runtime / wrapper.KV_RECEIPT_REL).write_text(json.dumps({
                "schema": "stegverse.kv.provider-materialization-receipt/v2",
                "materialized_root": "/tmp/not-authoritative",
                "exact_readback_verified": False,
                "credential_authority": "TV/TVC",
                "credential_material_persisted": False,
                "consumer_received_provider_credential": False,
            }) + "\n", encoding="utf-8")
            resolved, reason = wrapper.resolve_kv_root(runtime, {})
            self.assertIsNone(resolved)
            self.assertEqual(reason, "RUNTIME_MATERIALIZATION_READBACK_NOT_VERIFIED")

    def test_reusable_native_email_command_uses_kv_enforcing_runner(self):
        command = trigger.build_runner_command(
            trigger.NATIVE_EMAIL_PRIMARY,
            ROOT / trigger.NATIVE_EMAIL_PRIMARY,
            {"source_root": str(ROOT), "runtime_root": str(ROOT / "runtime-test")},
        )
        self.assertEqual(Path(command[1]).name, "consume_native_email_action_monitor_request_kv.py")
        self.assertIn("--source-root", command)
        self.assertIn("--runtime-root", command)

    def test_pre_execution_pending_does_not_satisfy_reusable_slot(self):
        self.assertFalse(wrapper.reusable_slot_satisfied({
            "state": "ATTEMPT_RECORDED",
            "runtime_execution_attempted": False,
            "retry_allowed": True,
            "pending_reason": "KV_ROOT_NOT_MATERIALIZED",
        }))

    def test_missing_kv_proof_does_not_satisfy_reusable_slot(self):
        self.assertFalse(wrapper.reusable_slot_satisfied({
            "state": "ATTEMPT_RECORDED",
            "runtime_execution_attempted": True,
            "retry_allowed": True,
            "pending_reason": "KV_PERSISTENCE_PROOF_REQUIRED",
        }))

    def test_successful_bounded_attempt_satisfies_one_hourly_slot_even_if_task_continues(self):
        self.assertTrue(wrapper.reusable_slot_satisfied({
            "state": "ATTEMPT_RECORDED",
            "runtime_execution_attempted": True,
            "retry_allowed": True,
            "pending_reason": None,
        }))


if __name__ == "__main__":
    unittest.main()
