from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "workers" / "healer_failure_mailbox_shadow_worker.py"

spec = importlib.util.spec_from_file_location("healer_failure_mailbox_shadow_worker", WORKER_PATH)
worker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(worker)


def invocation(claim_id: str = "claim-shadow-001") -> dict:
    return {
        "task": {
            "task_id": worker.TASK_ID,
            "worker_id": worker.WORKER_ID,
            "claim_id": claim_id,
        },
        "handoff": {
            "authority": {
                "credential_authority": "TV/TVC",
                "mailbox_credential_available_to_worker": False,
                "non_tv_tvc_secret_or_token_allowed": False,
            }
        },
    }


class HealerFailureMailboxShadowWorkerTests(unittest.TestCase):
    def test_registry_and_adapter_contracts_are_credential_neutral(self) -> None:
        registry = json.loads((ROOT / "control" / "worker-registry.d" / "healer-failure-mailbox-shadow-001.json").read_text(encoding="utf-8"))
        adapter = json.loads((ROOT / "control" / "process-worker-adapters.d" / "healer-failure-mailbox-shadow-001.json").read_text(encoding="utf-8"))
        handoff = json.loads((ROOT / "handoffs" / "HEALER-FAILURE-MAILBOX-LIVE-SHADOW-001.json").read_text(encoding="utf-8"))

        task = registry["tasks"][0]
        registered_worker = registry["workers"][0]
        adapter_entry = adapter["adapters"][0]

        self.assertEqual(task["task_id"], worker.TASK_ID)
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertIsNone(task["claim_id"])
        self.assertEqual(registered_worker["worker_id"], worker.WORKER_ID)
        self.assertEqual(registered_worker["adapter_ref"], "process:healer-failure-mailbox-shadow-v1")
        self.assertEqual(adapter_entry["adapter_ref"], registered_worker["adapter_ref"])
        self.assertTrue(adapter_entry["enabled"])
        self.assertEqual(registry["credential_authority"], "TV/TVC")
        self.assertFalse(registry["github_token_required"])
        self.assertFalse(registry["non_tv_tvc_secret_or_token_allowed"])
        self.assertFalse(handoff["authority"]["mailbox_credential_available_to_worker"])

        allowed = set(adapter_entry["env_allowlist"])
        self.assertEqual(
            allowed,
            {
                "STEGVERSE_HEALER_SOURCE_ROOT",
                "STEGVERSE_HEALER_SHADOW_BATCH_PATH",
                "STEGVERSE_HEALER_SHADOW_MANIFEST_PATH",
                "HOME",
                "XDG_STATE_HOME",
                "LOCALAPPDATA",
            },
        )
        self.assertFalse(any("TOKEN" in name or "GMAIL" in name or "OAUTH" in name for name in allowed))

    def test_invocation_requires_claim_and_tv_tvc_boundary(self) -> None:
        worker.validate_invocation(invocation())

        missing_claim = invocation("")
        with self.assertRaisesRegex(RuntimeError, "claim"):
            worker.validate_invocation(missing_claim)

        wrong_authority = invocation()
        wrong_authority["handoff"]["authority"]["credential_authority"] = "OTHER"
        with self.assertRaisesRegex(RuntimeError, "credential authority drift"):
            worker.validate_invocation(wrong_authority)

        mailbox_credential = invocation()
        mailbox_credential["handoff"]["authority"]["mailbox_credential_available_to_worker"] = True
        with self.assertRaisesRegex(RuntimeError, "may not receive mailbox credentials"):
            worker.validate_invocation(mailbox_credential)

    def test_forbidden_mailbox_or_github_credential_blocks_before_execution(self) -> None:
        with patch.dict(os.environ, {"GMAIL_TOKEN": "forbidden"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "credential-bearing environment forbidden"):
                worker.execute(invocation())
        with patch.dict(os.environ, {"GITHUB_TOKEN": "forbidden"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "credential-bearing environment forbidden"):
                worker.execute(invocation())

    def test_manifest_must_attest_no_mailbox_mutation_and_tv_tvc(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "healer"
            batch = root / "batch.jsonl"
            manifest = root / "manifest.json"
            home = root / "home"
            node = home / ".stegverse" / "node.json"
            node.parent.mkdir(parents=True)
            node.write_text(json.dumps({
                "declared": True,
                "credential_authority": "TV/TVC",
                "github_token_required": False,
                "declaration_source": "test",
            }), encoding="utf-8")
            batch.write_text("\n", encoding="utf-8")
            manifest.write_text(json.dumps({
                "batch_id": "b1",
                "source_count": 0,
                "window_start": "2026-08-18T19:00:00-07:00",
                "window_end": "2026-08-18T19:01:00-07:00",
                "source_ref": "test://source",
                "mailbox_mutated": True,
                "credential_authority": "TV/TVC",
            }), encoding="utf-8")

            env = {
                "HOME": str(home),
                worker.ROOT_ENV: str(source),
                worker.BATCH_ENV: str(batch),
                worker.MANIFEST_ENV: str(manifest),
            }
            with patch.object(worker, "NODE_MARKERS", (node,)), patch.dict(os.environ, env, clear=True):
                with self.assertRaisesRegex(RuntimeError, "mailbox_mutated=false"):
                    worker.execute(invocation())

            value = json.loads(manifest.read_text(encoding="utf-8"))
            value["mailbox_mutated"] = False
            value["credential_authority"] = "OTHER"
            manifest.write_text(json.dumps(value), encoding="utf-8")
            with patch.object(worker, "NODE_MARKERS", (node,)), patch.dict(os.environ, env, clear=True):
                with self.assertRaisesRegex(RuntimeError, "credential authority must be TV/TVC"):
                    worker.execute(invocation())


if __name__ == "__main__":
    unittest.main()
