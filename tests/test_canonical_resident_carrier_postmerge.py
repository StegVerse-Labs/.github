from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CanonicalResidentCarrierPostMergeTests(unittest.TestCase):
    def test_contract_and_propagation_task_preserve_single_substrate(self):
        contract = json.loads((ROOT / "control/canonical-resident-carrier-contract.json").read_text())
        task = json.loads((ROOT / "tasks/CANONICAL-RESIDENT-CARRIER-PROPAGATION-VERIFY-001.json").read_text())
        receipt = json.loads((ROOT / "receipts/canonical-resident-carrier/propagation-verification-001.json").read_text())
        self.assertEqual(contract["heartbeat"]["progression_dependency"], "OSCILLATOR_ONLY")
        self.assertFalse(contract["heartbeat"]["grants_execution_authority"])
        self.assertEqual(contract["worker_runtime"]["class"], "WorkerCoordinator")
        self.assertFalse(contract["worker_runtime"]["second_worker_runtime_allowed"])
        self.assertEqual(contract["credential_authority"], "TV/TVC")
        self.assertEqual(task["source_merge"], "b1f2bb3e33a1f93850811f0a751b2055519ab4dd")
        self.assertEqual(task["state"], "COMPLETED")
        self.assertFalse(task["user_action_required"])
        self.assertFalse(task["runtime_status_propagated"])
        self.assertEqual(task["completion_receipt_ref"], "receipts/canonical-resident-carrier/propagation-verification-001.json")
        self.assertEqual(task["runtime_status_propagation_gate"], "CONSUMER_SPECIFIC_AUTHENTIC_RESIDENT_EVIDENCE_ONLY")
        self.assertEqual(set(task["destinations"]), {
            "StegVerse-Labs/Site",
            "GCAT-BCAT-Engine/Publisher",
            "StegVerse-Labs/admissibility-wiki",
            "StegVerse-002/stegguardian-wiki",
        })
        self.assertEqual(receipt["state"], "COMPLETED")
        self.assertEqual(receipt["verified_destinations"], 4)
        self.assertTrue(receipt["source_architecture_propagation_complete"])
        self.assertFalse(receipt["runtime_status_propagation_complete"])
        self.assertEqual(receipt["runtime_status_blocker"], "SV002_AND_SV011_AUTHENTIC_RESIDENT_EVIDENCE_NOT_YET_ESTABLISHED")
        self.assertEqual(receipt["credential_authority"], "TV/TVC")
        self.assertEqual(receipt["github_token_runtime_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
