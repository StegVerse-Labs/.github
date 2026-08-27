from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class COSVLivePacketTaskVectorTests(unittest.TestCase):
    def test_live_packet_task_vector_is_visible_and_canonical(self) -> None:
        record = json.loads((ROOT / "control" / "task-vectors" / "COSV-LIVE-PACKET-AUTOMATION-006.json").read_text())
        fragment = json.loads((ROOT / "control" / "worker-registry.d" / "cosv-live-packet-automation-006.json").read_text())
        task = fragment["tasks"][0]

        self.assertTrue(cosv.validate_record(record))
        self.assertEqual(record["exact_metrics"]["symbol_order"], "LRUIVGOCMTBEAP")
        self.assertEqual(record["vector"], "50000000100000")
        self.assertEqual(task["source_state_vector_ref"], "control/task-vectors/COSV-LIVE-PACKET-AUTOMATION-006.json")
        self.assertEqual(task["machine_readable_state"]["cosv"]["vector"], record["vector"])
        self.assertEqual(task["machine_readable_state"]["cosv"]["vector_state"], "EMITTED")
        self.assertEqual(task["machine_readable_state"]["cosv"]["authority_effect"], "NONE")
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertIsNone(task["claim_id"])
        self.assertFalse(task["archive_eligible"])


if __name__ == "__main__":
    unittest.main()
