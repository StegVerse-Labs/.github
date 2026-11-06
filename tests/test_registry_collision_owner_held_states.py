"""Every owner-held checkout state guards collisions, not only CHECKED_OUT and CLAIMED_INTEGRATION.

At main bb4f1ee four ACTIVE/CLAIMED_IMPLEMENTATION shards and one
ACTIVE/CHECKED_OUT_CURRENT_SESSION shard are omitted from the aggregate and were
unguarded (StegVerse-Labs/.github#3369, #3195, #3372).
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("owner_held_states_collision", ROOT / "scripts/evaluate_task_registry_collision_checkin.py")
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gate)
import cosv


def shard(tid, checkout, state="ACTIVE"):
    return {"task_id": tid, "correlation_id": tid, "root_correlation_id": tid,
            "coordination_state": state, "checkout_state": checkout,
            "targets": {"repositories": ["StegVerse-Labs/.github"], "components": ["shared-gate"]}}


class OwnerHeldStateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        patch = mock.patch.object(gate, "RECORDS", self.root)
        patch.start()
        self.addCleanup(patch.stop)

    def put(self, row):
        (self.root / f"{row['task_id']}.json").write_text(json.dumps(row))

    def test_owner_held_states_cover_every_claimed_lifecycle_state(self):
        claimed = {k for k in cosv.LIFECYCLE if k.startswith("CLAIMED_") or k == "MACHINE_OWNED"}
        self.assertLessEqual(claimed, gate.OWNER_HELD_CHECKOUT_STATES)

    def test_every_owner_held_state_is_an_omitted_shard_guard(self):
        for state in sorted(gate.OWNER_HELD_CHECKOUT_STATES):
            self.put(shard(f"OWNER-{state}", state))
        self.assertEqual(sorted(gate.load_missing_checked_out_shards({})),
                         sorted(f"OWNER-{s}" for s in gate.OWNER_HELD_CHECKOUT_STATES))

    def test_inactive_claimed_owner_is_not_hard_eligible(self):
        for state in sorted(gate.OWNER_HELD_CHECKOUT_STATES - {"CHECKED_OUT"}):
            with self.subTest(state=state):
                self.assertTrue(gate.is_owner_held({"checkout_state": state, "coordination_state": "ACTIVE"}))
                self.assertFalse(gate.is_owner_held({"checkout_state": state, "coordination_state": "RETIRED"}))

    def test_unclaimed_and_handoff_ready_remain_excluded(self):
        for state in ("UNCLAIMED", "NONE", "HANDOFF_READY", "CHECKED_IN"):
            self.put(shard(f"FREE-{state}", state))
        self.assertEqual(gate.load_missing_checked_out_shards({}), {})


if __name__ == "__main__":
    unittest.main()
