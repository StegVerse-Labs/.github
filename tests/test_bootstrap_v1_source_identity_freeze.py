from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers import bootstrap_v1_source_identity_freeze_worker as worker


def upstream(ids=None, **overrides):
    identities = ids or {
        "stegverse.sdk": "sha256:" + "1" * 64,
        "stegverse.stegcore": "sha256:" + "2" * 64,
        "stegverse.core-lite": "sha256:" + "3" * 64,
        "stegverse.master-records": "sha256:" + "4" * 64,
    }
    value = {
        "schema": "stegverse.sv-dn1.production-source-prep-receipt/v2",
        "state": "COMPLETE",
        "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
        "source_identity_scheme": "sha256-content-manifest",
        "source_identities": identities,
        "source_roots": {k: "/var/lib/stegverse/source/" + k for k in identities},
        "network_source_fetch_performed": False,
        "github_platform_required": False,
        "credential_used": False,
        "github_token_used": False,
        "repository_writeback_performed": False,
    }
    value.update(overrides)
    return value


def invocation():
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "task": {
            "task_id": worker.TASK_ID,
            "worker_id": worker.WORKER_ID,
            "claim_id": "claim-bootstrap-v1",
            "heartbeat_timing": {"fencing_token": 23},
        },
    }


class BootstrapV1SourceIdentityFreezeTests(unittest.TestCase):
    def test_catalog_is_platform_neutral_and_exact_four(self):
        receipt = upstream()
        ids = worker.validate_upstream(receipt)
        catalog = worker.build_catalog(receipt, ids)
        self.assertEqual(catalog["schema"], "stegverse.bootstrap.source-catalog/v1")
        self.assertEqual(catalog["catalog_version"], "1.0.0")
        self.assertEqual(catalog["component_count"], 4)
        self.assertEqual([x["component_id"] for x in catalog["components"]], list(worker.COMPONENTS))
        self.assertFalse(catalog["github_platform_required"])
        self.assertFalse(catalog["specific_external_platform_required"])
        self.assertFalse(catalog["network_locator_required"])
        self.assertFalse(catalog["package_integrity_confers_execution_authority"])
        self.assertEqual(catalog["execution_authority"], "NONE")

    def test_incomplete_or_platform_dependent_upstream_fails(self):
        with self.assertRaisesRegex(worker.UpstreamPending, "has not completed"):
            worker.validate_upstream(upstream(state="HANDOFF_READY"))
        with self.assertRaisesRegex(RuntimeError, "platform/network dependency"):
            worker.validate_upstream(upstream(github_platform_required=True))
        with self.assertRaisesRegex(RuntimeError, "platform/network dependency"):
            worker.validate_upstream(upstream(network_source_fetch_performed=True))
        bad = upstream()
        bad["source_identities"].pop("stegverse.master-records")
        bad["source_roots"].pop("stegverse.master-records")
        with self.assertRaisesRegex(RuntimeError, "component set mismatch"):
            worker.validate_upstream(bad)

    def test_execute_freezes_idempotently_and_conflict_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            prep = base / "prep"
            bound = base / "freeze"
            (prep / "receipts").mkdir(parents=True)
            (prep / "receipts/latest.json").write_text(json.dumps(upstream()))
            env = {worker.SOURCE_PREP_ENV: str(prep), worker.BOUND_ENV: str(bound)}
            with mock.patch.dict("os.environ", env, clear=True):
                first = worker.execute(invocation())
                second = worker.execute(invocation())
                self.assertEqual(first["catalog_sha256"], second["catalog_sha256"])
                catalog_path = bound / "catalog/bootstrap-v1-source-catalog.json"
                frozen = json.loads(catalog_path.read_text())
                frozen["components"][0]["source_identity"] = "sha256:" + "f" * 64
                catalog_path.write_text(json.dumps(frozen))
                with self.assertRaisesRegex(worker.FrozenIdentityConflict, "FROZEN_SOURCE_IDENTITY_CONFLICT"):
                    worker.execute(invocation())

    def test_missing_upstream_main_returns_handoff_ready(self):
        with tempfile.TemporaryDirectory() as td:
            with (
                mock.patch.dict("os.environ", {worker.SOURCE_PREP_ENV: td, worker.BOUND_ENV: td + "/bound"}, clear=True),
                mock.patch("sys.stdin", io.StringIO(json.dumps(invocation()) + "\n")),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                self.assertEqual(worker.main(), 0)
                result = json.loads(stdout.getvalue())
            self.assertEqual(result["state"], "HANDOFF_READY")
            self.assertEqual(result["transition_id"], "BOOTSTRAP_V1_SOURCE_PREP_RECEIPT_PENDING")
            self.assertFalse(result["blocker"]["github_platform_required"])
            self.assertFalse(result["blocker"]["human_action_required"])

    def test_handoff_registry_adapter_are_zero_authority(self):
        root = Path(__file__).resolve().parents[1]
        handoff = json.loads((root / "handoffs/BOOTSTRAP-V1-SOURCE-IDENTITY-FREEZE-001.json").read_text())
        registry = json.loads((root / "control/worker-registry.d/bootstrap-v1-source-identity-freeze-001.json").read_text())
        adapter = json.loads((root / "control/process-worker-adapters.d/bootstrap-v1-source-identity-freeze-001.json").read_text())
        self.assertFalse(handoff["authority"]["github_platform_required"])
        self.assertFalse(handoff["authority"]["network_access_authority"])
        self.assertFalse(handoff["authority"]["package_execution_authority"])
        self.assertFalse(handoff["authority"]["repository_writeback_authority"])
        self.assertEqual(registry["tasks"][0]["state"], "HANDOFF_READY")
        self.assertNotIn("GITHUB_TOKEN", adapter["adapters"][0]["env_allowlist"])
        self.assertEqual(adapter["adapters"][0]["env_allowlist"], [
            "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT",
            "STEGVERSE_BOUND_STATE_ROOT",
            "HOME",
            "PATH",
        ])


if __name__ == "__main__":
    unittest.main()
