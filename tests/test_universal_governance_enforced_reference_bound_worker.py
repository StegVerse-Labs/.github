from __future__ import annotations

import importlib.util
from hashlib import sha1
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "workers" / "universal_governance_enforced_reference_bound_worker.py"
SPEC = importlib.util.spec_from_file_location("universal_governance_enforced_reference_bound_worker", PATH)
bound = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bound)


class UniversalGovernanceResidentSourceBindingTests(unittest.TestCase):
    def test_required_commit_is_merged_fresh_binding_source(self):
        self.assertEqual(
            bound.REQUIRED_STEGCORE_COMMIT,
            "7cbef555608f7e154ae575dcbd5b4e65fbf0c85c",
        )
        self.assertIn("src/stegcore/fresh_commit_binding.py", bound.EXPECTED_GIT_BLOBS)

    def test_source_fingerprint_accepts_exact_declared_blobs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            expected = {}
            for index, rel in enumerate(bound.EXPECTED_GIT_BLOBS):
                data = f"fixture-{index}\n".encode()
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                expected[rel] = sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
            with mock.patch.object(bound, "EXPECTED_GIT_BLOBS", expected):
                self.assertEqual(bound.validate_stegcore_source(root), expected)

    def test_source_fingerprint_rejects_stale_local_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = "scripts/run_universal_governance_reference_boundary.py"
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("stale\n", encoding="utf-8")
            with mock.patch.object(bound, "EXPECTED_GIT_BLOBS", {rel: "0" * 40}):
                with self.assertRaisesRegex(bound.base.SourceUnavailable, "not bound"):
                    bound.validate_stegcore_source(root)

    def test_v2_receipt_requires_all_fresh_binding_predicates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "stegcore-reference" / "receipts" / "reference-boundary.latest.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            receipt = {
                "schema": "stegcore.universal-governance-reference-boundary-receipt.v2",
                **{key: True for key in bound.REQUIRED_V2_TRUE},
                "final_target_mutation_count": 1,
                "real_external_system_enforced_activation": False,
            }
            path.write_text(json.dumps(receipt), encoding="utf-8")
            self.assertEqual(bound.validate_v2_runner_receipt(root), receipt)
            receipt["fresh_binding_single_use"] = False
            path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "not fully observed"):
                bound.validate_v2_runner_receipt(root)


if __name__ == "__main__":
    unittest.main()
