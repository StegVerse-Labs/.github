from __future__ import annotations

import json
import py_compile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OrganizationFederationBindingTests(unittest.TestCase):
    def test_federation_inputs_are_complete_and_fail_closed(self) -> None:
        federation=json.loads((ROOT/"control"/"organization-federation.json").read_text(encoding="utf-8"))
        tasks=json.loads((ROOT/"control"/"organization-task-registry.json").read_text(encoding="utf-8"))
        self.assertEqual(federation["organization_count"], len(federation["organizations"]))
        self.assertEqual(len(tasks["tasks"]), federation["organization_count"])
        self.assertEqual(federation["coverage"]["unassigned"], 0)
        self.assertEqual(tasks["coverage"]["unassigned"], 0)
        blocked=[x for x in tasks["tasks"] if x["state"]=="BLOCKED"]
        self.assertTrue(all(x.get("release_condition") and x.get("next_action") for x in blocked))

    def test_worker_compiles_and_handoff_preserves_non_authority(self) -> None:
        py_compile.compile(str(ROOT/"workers"/"organization_federation_readiness_worker.py"), doraise=True)
        handoff=json.loads((ROOT/"handoffs"/"SHWP-ALL-ORG-FEDERATION-001.json").read_text(encoding="utf-8"))
        authority=handoff["authority"]
        self.assertEqual(authority["credential_authority"], "TV/TVC")
        self.assertFalse(authority["heartbeat_grants_execution_authority"])
        self.assertIn(authority.get("github_token_runtime_authority"), (False, "NONE"))

if __name__ == "__main__":
    unittest.main()
