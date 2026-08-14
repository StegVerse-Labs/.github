from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import workers.formalism_manifold_implementation_admission_worker as worker


class ImplementationAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_root = worker.ROOT

    def tearDown(self) -> None:
        worker.ROOT = self.original_root

    def _config(self) -> dict:
        return {
            "reconciliation_receipt": "receipts/formalism-manifold-orchestration/SHWP-FORMALISM-MANIFOLD-RECONCILIATION-001.json",
            "owners": {"StegVerse-Labs/StegCore": {"authority_class": "RUNTIME", "requires_mirror_handoff": True}},
            "seed_deltas": [{
                "delta_id": "MANIFOLD-GOVERNANCE-RUNTIME-KERNEL-001",
                "kind": "RUNTIME_IMPLEMENTATION",
                "owner_repository": "StegVerse-Labs/StegCore",
                "proposed_paths": ["MANIFOLD_GOVERNANCE_MIRROR_HANDOFF.md", "src/stegcore/manifold_governance.py", "tests/test_manifold_governance.py"],
                "authority_ceiling": ["canonical_steggate_unchanged"],
                "objective": "bounded manifold kernel"
            }]
        }

    def _complete_reconciliation(self, root: Path) -> None:
        path = root / "receipts/formalism-manifold-orchestration/SHWP-FORMALISM-MANIFOLD-RECONCILIATION-001.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"state": "COMPLETED", "result": {"reconciled": True}}), encoding="utf-8")

    def _owner(self, root: Path) -> Path:
        owner = root / "stegcore"
        owner.mkdir(parents=True)
        (owner / "STEGCORE_MIRROR_HANDOFF.md").write_text("# StegCore Mirror Handoff\ncanonical runtime authority\n", encoding="utf-8")
        return owner

    def test_missing_reconciliation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worker.ROOT = root
            result = worker.evaluate(self._config(), {})
            self.assertEqual(result["state"], "BLOCKED")
            self.assertEqual(result["reason"], "RECONCILIATION_RECEIPT_MISSING")

    def test_complete_reconciliation_emits_owner_manifest_without_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worker.ROOT = root
            self._complete_reconciliation(root)
            owner = self._owner(root)
            (root / "control/worker-registry.d").mkdir(parents=True)
            result = worker.evaluate(self._config(), {"StegVerse-Labs/StegCore": owner})
            self.assertEqual(result["state"], "COMPLETED")
            self.assertEqual(len(result["owner_work_manifests"]), 1)
            manifest = result["owner_work_manifests"][0]
            self.assertEqual(manifest["claim_state"], "READY_FOR_SEPARATE_OWNER_ADMISSION")
            self.assertFalse(manifest["coordinator_mutation_authority"])
            self.assertFalse(manifest["github_token_required"])
            self.assertEqual(manifest["credential_authority"], "TV/TVC")

    def test_missing_owner_source_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worker.ROOT = root
            self._complete_reconciliation(root)
            (root / "control/worker-registry.d").mkdir(parents=True)
            result = worker.evaluate(self._config(), {})
            self.assertEqual(result["state"], "BLOCKED")
            self.assertEqual(result["blocked_deltas"][0]["reason"], "OWNER_SOURCE_NOT_MATERIALIZED")

    def test_active_owner_scope_collision_blocks_admission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worker.ROOT = root
            self._complete_reconciliation(root)
            owner = self._owner(root)
            handoffs = root / "handoffs"
            handoffs.mkdir()
            (handoffs / "ACTIVE.json").write_text(json.dumps({
                "task": {"repository": "StegVerse-Labs/StegCore"},
                "execution": {"allowed_paths": ["src/stegcore/**"]}
            }), encoding="utf-8")
            fragments = root / "control/worker-registry.d"
            fragments.mkdir(parents=True)
            (fragments / "active.json").write_text(json.dumps({
                "schema": "stegverse.worker-registry-fragment/v0.1",
                "tasks": [{"task_id": "OTHER", "state": "HANDOFF_READY", "handoff_ref": "handoffs/ACTIVE.json"}]
            }), encoding="utf-8")
            result = worker.evaluate(self._config(), {"StegVerse-Labs/StegCore": owner})
            self.assertEqual(result["state"], "BLOCKED")
            self.assertEqual(result["blocked_deltas"][0]["reason"], "ACTIVE_OWNER_SCOPE_COLLISION")


if __name__ == "__main__":
    unittest.main()
