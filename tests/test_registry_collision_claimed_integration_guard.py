"""Owner-held CLAIMED_INTEGRATION shards are collision guards and hard collisions.

Regressions for the two coordinated predicates in
scripts/evaluate_task_registry_collision_checkin.py: the omitted-shard loader
and the hard-collision predicate (StegVerse-Labs/.github#3369, #3195).
Each test fails on the pre-repair evaluator, which loaded and hardened only
CHECKED_OUT owners.
"""
from __future__ import annotations
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("claimed_integration_collision", ROOT / "scripts/evaluate_task_registry_collision_checkin.py")
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gate)

SURFACE = "INTERNAL_CANONICAL_WORK_BOOTSTRAP"


def owner(tid, coordination="ACTIVE", checkout="CHECKED_OUT", component="shared-gate"):
    return {"task_id": tid, "correlation_id": tid, "root_correlation_id": tid,
            "coordination_state": coordination, "checkout_state": checkout,
            "repository": "StegVerse-Labs/.github",
            "targets": {"repositories": ["StegVerse-Labs/.github"], "components": [component]}}


class _Harness(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def invoke(self, registry, task_id, components=("shared-gate",)):
        output = io.StringIO()
        payload = {"task_id": task_id, "caller_surface": SURFACE,
                   "observed_registry_generation": registry["generation"],
                   "checkin_context": {"session_id": "claimed-integration-guard-test",
                                       "repository": "StegVerse-Labs/.github",
                                       "components_under_mutation": list(components)}}
        with (mock.patch.object(gate, "load_registry", return_value=registry),
              mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
              mock.patch.dict(os.environ, {"STEGVERSE_TASK_REGISTRY_EVENT_LEDGER": str(self.root / "events.jsonl")}),
              contextlib.redirect_stdout(output)):
            gate.main()
        return json.loads(output.getvalue())


class OmittedShardGuardTests(_Harness):
    def setUp(self):
        super().setUp()
        self.records = self.root / "records"
        self.records.mkdir()
        patcher = mock.patch.object(gate, "RECORDS", self.records)
        patcher.start()
        self.addCleanup(patcher.stop)

    def put(self, row):
        (self.records / f"{row['task_id']}.json").write_text(json.dumps(row))

    def test_omitted_active_claimed_integration_shard_is_refused(self):
        self.put(owner("CLAIMED_OWNER", checkout="CLAIMED_INTEGRATION"))
        self.assertEqual(list(gate.load_missing_checked_out_shards({})), ["CLAIMED_OWNER"])
        result = self.invoke({"generation": 7, "tasks": [owner("CANDIDATE")]}, "CANDIDATE")
        self.assertEqual(result["disposition"], "STOP_COLLISION")
        self.assertEqual(result["hard_collision_task_ids"], ["CLAIMED_OWNER"])
        self.assertEqual(result["unregistered_checked_out_shard_ids"], ["CLAIMED_OWNER"])
        self.assertEqual(result["authority_effect"], "NONE")

    def test_omitted_inactive_or_released_shards_are_allowed(self):
        # Identical scope to the active claimed owner; only coordination or
        # checkout state differs, so only the active owner may guard.
        self.put(owner("CLAIMED_OWNER", checkout="CLAIMED_INTEGRATION"))
        self.put(owner("RETIRED_CLAIM", coordination="RETIRED", checkout="CLAIMED_INTEGRATION"))
        self.put(owner("CLOSED_CLAIM", coordination="CLOSED", checkout="CLAIMED_INTEGRATION"))
        self.put(owner("RELEASED_OWNER", checkout="RELEASED"))
        self.put(owner("UNCLAIMED_OWNER", checkout="UNCLAIMED"))
        self.assertEqual(list(gate.load_missing_checked_out_shards({})), ["CLAIMED_OWNER"])
        result = self.invoke({"generation": 7, "tasks": [owner("CANDIDATE")]}, "CANDIDATE")
        self.assertEqual(result["hard_collision_task_ids"], ["CLAIMED_OWNER"])
        (self.records / "CLAIMED_OWNER.json").unlink()
        self.assertEqual(gate.load_missing_checked_out_shards({}), {})
        allowed = self.invoke({"generation": 7, "tasks": [owner("CANDIDATE")]}, "CANDIDATE")
        self.assertEqual(allowed["disposition"], "CONTINUE")
        self.assertEqual(allowed["hard_collision_task_ids"], [])
        self.assertEqual(allowed["unregistered_checked_out_shard_ids"], [])

    def test_checked_out_and_claimed_integration_shards_are_both_hard(self):
        self.put(owner("CHECKED_OWNER"))
        self.put(owner("CLAIMED_OWNER", checkout="CLAIMED_INTEGRATION"))
        result = self.invoke({"generation": 7, "tasks": [owner("CANDIDATE")]}, "CANDIDATE")
        self.assertEqual(result["disposition"], "STOP_COLLISION")
        self.assertEqual(sorted(result["hard_collision_task_ids"]), ["CHECKED_OWNER", "CLAIMED_OWNER"])
        self.assertEqual(result["unregistered_checked_out_shard_ids"], ["CHECKED_OWNER", "CLAIMED_OWNER"])

    def test_registered_claimed_integration_owner_is_hard_only_while_active(self):
        active = owner("REGISTERED_CLAIM", checkout="CLAIMED_INTEGRATION")
        retired = owner("RETIRED_CLAIM", coordination="RETIRED", checkout="CLAIMED_INTEGRATION")
        result = self.invoke({"generation": 7, "tasks": [owner("CANDIDATE"), active, retired]}, "CANDIDATE")
        self.assertEqual(result["disposition"], "STOP_COLLISION")
        self.assertEqual(result["hard_collision_task_ids"], ["REGISTERED_CLAIM"])
        self.assertEqual(result["unregistered_checked_out_shard_ids"], [])


class Issue3369RealRegistrationTests(_Harness):
    """The real #3369 candidate against the real aggregate and shard directory."""

    TASK_ID = "PROTOCOL-V1-MINIMUM-PACKET-CONFORMANCE-001"
    # Scope stated in #3369: packet/ledger work in .github and the SDK, bound to
    # a WorkerCoordinator claim/fence. A test fixture, not an admission.
    COMPONENTS = ("workercoordinator-claim-fence",)

    def setUp(self):
        super().setUp()
        self.registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text(encoding="utf-8"))
        registered = {row["task_id"] for row in self.registry["tasks"]}
        self.omitted_claimed = sorted(
            path.stem for path in (ROOT / "data/canonical-task-records").glob("*.json")
            if path.stem not in registered and self._claimed(path))

    @staticmethod
    def _claimed(path):
        row = json.loads(path.read_text(encoding="utf-8"))
        return (isinstance(row, dict) and row.get("task_id") == path.stem
                and str(row.get("coordination_state") or "").upper() in gate.ACTIVEISH
                and str(row.get("checkout_state") or "").upper() == "CLAIMED_INTEGRATION")

    def test_unregistered_candidate_stops_only_because_unregistered(self):
        result = self.invoke(self.registry, self.TASK_ID, self.COMPONENTS)
        self.assertEqual(result["disposition"], "STOP_NOT_REGISTERED")
        self.assertEqual(result["session_action"], "END_OR_REGISTER_BEFORE_MUTATION")
        # Every omitted active CLAIMED_INTEGRATION shard is now a collision
        # guard, so registration is the only remaining reason to stop here.
        self.assertTrue(self.omitted_claimed)
        guarded = gate.load_missing_checked_out_shards(gate.load_records())
        self.assertTrue(set(self.omitted_claimed) <= set(guarded))

    def test_registered_candidate_collides_with_omitted_claimed_integration_owner(self):
        candidate = {"task_id": self.TASK_ID, "correlation_id": self.TASK_ID,
                     "root_correlation_id": self.TASK_ID,
                     "coordination_state": "PROPOSED", "checkout_state": "UNCLAIMED",
                     "targets": {"repositories": ["StegVerse-Labs/.github", "StegVerse-org/StegVerse-SDK"],
                                 "components": list(self.COMPONENTS)}}
        registry = {**self.registry, "tasks": [*self.registry["tasks"], candidate]}
        result = self.invoke(registry, self.TASK_ID, self.COMPONENTS)
        overlapping = sorted(
            tid for tid in self.omitted_claimed
            if set(self.COMPONENTS) & set((json.loads((ROOT / f"data/canonical-task-records/{tid}.json")
                                                      .read_text(encoding="utf-8")).get("targets") or {}).get("components") or []))
        self.assertTrue(overlapping)
        self.assertEqual(result["disposition"], "STOP_COLLISION")
        self.assertTrue(set(overlapping) <= set(result["hard_collision_task_ids"]))
        self.assertTrue(set(self.omitted_claimed) <= set(result["unregistered_checked_out_shard_ids"]))
        self.assertEqual(result["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
