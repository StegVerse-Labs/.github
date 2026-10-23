"""Lane C (C): TVC-SIGNED-RECEIPT-FORM-001 NEW_IDENTITY request (scope only), sealed scope and recorded plan outcome.

Coordination class B item (2), 2026-10-23: TVC receipts are unsigned, so LLM-adapter#432 had to carry
signatures instead of TVC receipt refs. This request scopes a signed-receipt form for TVC as a registered
task; it builds nothing and edits no registry file. plan is ALLOW at generation 320 -> 321 with no
consequence. Lowest supported mode E0 (committed files only; no clock, network or credential).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "canonical_task_registration_transition.py"
TASK_ID = "TVC-SIGNED-RECEIPT-FORM-001"
REQUEST = f"tests/fixtures/canonical_task_registration/tvc-signed-receipt-form/{TASK_ID}.request.json"
ALLOCATION = "control/goal-task-allocation-requests/lane-c-tvc-signed-receipt-form-2026-10-23.json"
SCOPE_DIGEST = "sha256:808509693f419bfb7a570607ef3faf0723d8e76ed35655b7cc6376b26f9a21e3"
EXPECTED_VECTOR = "10300000002000"


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class TvcSignedReceiptFormTaskRequest(unittest.TestCase):
    def test_request_is_new_identity_scope_only_and_makes_no_registry_edit(self) -> None:
        request = load(REQUEST)
        self.assertEqual(request["registration_mode"], "NEW_IDENTITY")
        self.assertEqual(request["authority_effect"], "NONE_REGISTRATION_ONLY")
        self.assertTrue(request["record"]["goal"].startswith("SCOPE ONLY"))
        self.assertNotIn("cosv_task_vector", request["record"])
        for rel in ("data/canonical-task-records", "control/goal-scope-seals", "control/task-vectors",
                    "control/task-vector-index.d"):
            self.assertFalse((ROOT / rel / f"{TASK_ID}.json").exists(), rel)
        registry = load("data/canonical-task-registry.json")
        self.assertNotIn(TASK_ID, {row.get("task_id") for row in registry.get("tasks", [])})

    def test_scope_is_sealed_with_an_e0_finish_point(self) -> None:
        spec = importlib.util.spec_from_file_location("gss_under_test", ROOT / "scripts" / "goal_scope_seal.py")
        gss = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gss)
        request = load(REQUEST)
        sealed = request["sealed_scope"]
        self.assertEqual(sealed["scope_digest"], SCOPE_DIGEST)
        self.assertEqual(gss.digest(sealed["scope"]), SCOPE_DIGEST)
        self.assertEqual(sealed["scope"]["finish_point"]["lowest_supported_mode"], "E0")
        self.assertIsNone(sealed["supersedes_scope_digest"])

    def test_allocation_request_binds_the_same_digest_without_a_vector(self) -> None:
        alloc = load(ALLOCATION)
        self.assertEqual(alloc["proposed_task_id"], TASK_ID)
        self.assertEqual(alloc["scope_digest"], SCOPE_DIGEST)
        self.assertIsNone(alloc["cosv_task_vector"])
        self.assertEqual(alloc["authority_effect"], "NONE_REQUEST_ONLY")
        self.assertEqual(load(REQUEST)["allocation_request_ref"], ALLOCATION)

    def test_scope_carries_no_key_material_and_routes_custody_to_tv_tvc(self) -> None:
        text = (ROOT / REQUEST).read_text(encoding="utf-8").lower()
        for token in ("private_key", "-----begin", "seed_phrase", "secret_key"):
            self.assertNotIn(token, text)
        deps = {d["dependency_id"]: d for d in load(REQUEST)["record"]["dependencies"]}
        self.assertIn("StegVerse-Labs/TVC#537", deps["CAPABILITY-TVC-SKAP-CUSTODY-REFERENCE-ISSUE"]["ref"])
        self.assertIn("SKAP_VAULT_INTR_READ_CLIENT_NOT_BOUND", deps["CAPABILITY-SKAP-VAULT-INTR-READ-CLIENT"]["ref"])

    def test_plan_is_allow_with_no_consequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "receipt.json"
            proc = subprocess.run([sys.executable, str(SCRIPT), "plan", "--request", str(ROOT / REQUEST),
                                   "--receipt-out", str(out)], cwd=ROOT, capture_output=True, text=True, check=False)
            receipt = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((receipt["mode"], receipt["disposition"]), ("plan", "ALLOW"))
        ev = receipt["evidence"]
        self.assertEqual(ev["cosv_task_vector"], EXPECTED_VECTOR)
        self.assertEqual((ev["predecessor_registry_generation"], ev["successor_registry_generation"]), (320, 321))
        self.assertEqual(ev["scope_digest"], SCOPE_DIGEST)
        self.assertTrue(ev["collision_checkin"].startswith("ALLOW"))
        for flag in ("organization_ledger_appended", "execution_authority_minted",
                     "workercoordinator_claim_or_fence_minted", "intr_admission_minted", "clock_read"):
            self.assertFalse(receipt[flag], flag)
        for rel in ("data/canonical-task-records", "control/goal-scope-seals"):
            self.assertFalse((ROOT / rel / f"{TASK_ID}.json").exists(), "plan wrote " + rel)


if __name__ == "__main__":
    unittest.main()
