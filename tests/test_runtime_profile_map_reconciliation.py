from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


mod = load_module(
    "consume_runtime_profile_map_reconciliation",
    "control/resident-execution-request.d/consume-runtime-profile-map-reconciliation.py",
)


class RuntimeProfileMapReconciliationTests(unittest.TestCase):
    def test_request_contract_is_non_authorizing(self):
        request = json.loads((ROOT / "control/resident-execution-request.d/runtime-profile-map-reconciliation-001.json").read_text(encoding="utf-8"))
        mod.validate_request(request)
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["oscillator_grants_execution_authority"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_waits_for_custody_before_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            request = json.loads((ROOT / "control/resident-execution-request.d/runtime-profile-map-reconciliation-001.json").read_text(encoding="utf-8"))
            target = runtime / mod.REQUEST_REL
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(request), encoding="utf-8")
            result = mod.consume(ROOT, runtime, env={})
            self.assertEqual(result["state"], "WAITING_FOR_MASTER_RECORDS_CUSTODY")
            self.assertEqual(result["authority_effect"], "NONE_WAIT_ONLY")


if __name__ == "__main__":
    unittest.main()
