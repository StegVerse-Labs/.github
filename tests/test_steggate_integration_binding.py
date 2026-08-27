from __future__ import annotations

import json
import py_compile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class StegGateIntegrationBindingTests(unittest.TestCase):
    def test_inputs_preserve_tvtvc_and_non_authority(self) -> None:
        management=json.loads((ROOT/"management"/"STEGGATE_HEARTBEAT_CREDENTIAL_INTEGRATION_001.json").read_text())
        adapters=json.loads((ROOT/"control"/"process-worker-adapters.json").read_text())
        subsignals=json.loads((ROOT/"control"/"heartbeat-subsignals.json").read_text())
        handoff=json.loads((ROOT/"handoffs"/"STEGGATE-STABLE-RENDEZVOUS-WORKER-001.json").read_text())
        auth=json.loads((ROOT/"authorizations"/"STEGGATE-STABLE-RENDEZVOUS-WORKER-001.json").read_text())
        self.assertEqual(handoff["task"]["task_id"],"STEGGATE-STABLE-RENDEZVOUS-WORKER-001")
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertEqual(auth["task_id"],"STEGGATE-STABLE-RENDEZVOUS-WORKER-001")
        self.assertEqual(management["credential_authority"],"TV/TVC")
        self.assertEqual(management["github_token_runtime_authority"],"NONE")
        self.assertTrue(adapters)
        self.assertTrue(subsignals)
        py_compile.compile(str(ROOT/"workers"/"steggate_rendezvous_deployment_worker.py"),doraise=True)

if __name__=="__main__":
    unittest.main()
