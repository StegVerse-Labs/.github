from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/runtime-solution-registry.d/hb32-existing-runtime-solutions.json"


class HB32RuntimeSolutionRegistryTests(unittest.TestCase):
    def test_registry_reuses_existing_runtime_surfaces_without_authority_escalation(self) -> None:
        value = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(value["schema"], "stegverse.runtime-solution-registry-fragment/v1")
        self.assertEqual(value["authority_effect"], "NONE_DISCOVERY_ONLY")
        self.assertFalse(value["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(value["authority"]["oscillator_grants_execution_authority"])
        self.assertEqual(value["authority"]["worker_claim_authority"], "WORKERCOORDINATOR")
        self.assertEqual(value["authority"]["transition_authority"], "INTERLOCK_INTR")
        self.assertEqual(value["authority"]["credential_authority"], "TV/TVC")
        self.assertEqual(value["authority"]["github_token_runtime_authority"], "NONE")

        classes = {item["problem_class"]: item for item in value["solutions"]}
        required = {
            "CARRIER_START_REPORTED_WITHOUT_OSCILLATOR_PROGRESS",
            "RESIDENT_WORKER_MISSING",
            "RESIDENT_WORKER_PREVIOUSLY_PROVEN_BUT_STALE",
            "SELF_HEALED_WORKER_FIRST_CYCLE_STARVED_BY_LONG_MAINTENANCE",
            "RESIDENT_SOURCE_STALE_OR_INCOMPLETE",
            "DURABLE_RUNTIME_NATIVE_BOOTSTRAP_INCOMPLETE",
            "TASK_REQUEST_NOT_CONSUMED_WHILE_RUNTIME_PATH_EXISTS",
        }
        self.assertTrue(required.issubset(classes))
        self.assertEqual(
            classes["SELF_HEALED_WORKER_FIRST_CYCLE_STARVED_BY_LONG_MAINTENANCE"]["canonical_fix_refs"],
            ["55c03313d72dde2f067434c87cd3691ec0682c14"],
        )
        self.assertEqual(
            classes["RESIDENT_WORKER_PREVIOUSLY_PROVEN_BUT_STALE"]["canonical_fix_refs"],
            ["511b82e26dcfce0d799f861df23b605fb837ac56"],
        )
        for item in value["solutions"]:
            self.assertTrue(item["reuse"])
            self.assertTrue(item["do_not_create"])


if __name__ == "__main__":
    unittest.main()
