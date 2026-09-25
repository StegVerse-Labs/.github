"""Fail-closed component-010 missing-owner and session-chain regressions."""
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
SPEC = importlib.util.spec_from_file_location("component010_collision", ROOT / "scripts/evaluate_task_registry_collision_checkin.py")
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gate)
from task_registry_checkin_event_history import append_event, load_events


def owner(tid, component="shared-gate"):
    return {"task_id": tid, "correlation_id": tid, "root_correlation_id": tid,
            "coordination_state": "ACTIVE", "checkout_state": "CHECKED_OUT",
            "repository": "StegVerse-Labs/.github",
            "targets": {"repositories": ["StegVerse-Labs/.github"], "components": [component]}}


class Component010ProjectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        patcher = mock.patch.object(gate, "RECORDS", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def put(self, row, filename=None):
        (self.root / ((filename or row["task_id"]) + ".json")).write_text(json.dumps(row))

    def invoke(self, registry, payload):
        output = io.StringIO()
        with (mock.patch.object(gate, "load_registry", return_value=registry),
              mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
              mock.patch.dict(os.environ, {"STEGVERSE_TASK_REGISTRY_EVENT_LEDGER": str(self.root / "events.jsonl")}),
              contextlib.redirect_stdout(output)):
            gate.main()
        return json.loads(output.getvalue())

    def test_omitted_checked_out_owner_is_collision_only_and_not_registered(self):
        registered, omitted = owner("REGISTERED"), owner("MISSING_OWNER")
        self.put(omitted)
        missing = gate.load_missing_checked_out_shards({"REGISTERED": registered})
        self.assertEqual(list(missing), ["MISSING_OWNER"])
        self.assertNotIn("MISSING_OWNER", {"REGISTERED": registered})
        self.assertEqual(gate.overlap(registered, missing["MISSING_OWNER"])[1], ["shared-gate"])

    def test_retired_and_unclaimed_shards_do_not_impersonate_checked_out_owner(self):
        retired = owner("RETIRED")
        retired["coordination_state"] = "RETIRED"
        released = owner("UNCLAIMED")
        released["checkout_state"] = "UNCLAIMED"
        self.put(retired)
        self.put(released)
        self.assertEqual(gate.load_missing_checked_out_shards({}), {})

    def test_auxiliary_session_note_is_not_a_canonical_owner(self):
        (self.root / "SOME-TASK.current-session-note.json").write_text(json.dumps({
            "goal_task_id": "SOME-TASK", "session_claim": "CURRENT_SESSION",
            "authentic_skap_observation": "NOT_PROVEN"}))
        self.assertEqual(gate.load_missing_checked_out_shards({}), {})
        forged = owner("SOME-TASK")
        (self.root / "SOME-TASK.current-session-note.json").write_text(json.dumps(forged))
        with self.assertRaisesRegex(ValueError, "path identity mismatch"):
            gate.load_missing_checked_out_shards({})

    def test_path_and_registered_identity_mismatches_fail_closed(self):
        self.put(owner("EXPECTED"), filename="WRONG")
        with self.assertRaisesRegex(ValueError, "path identity mismatch"):
            gate.load_missing_checked_out_shards({})
        (self.root / "WRONG.json").unlink()
        current = owner("EXPECTED")
        self.put(current)
        with self.assertRaisesRegex(ValueError, "correlation_id mismatch"):
            gate.load_missing_checked_out_shards({"EXPECTED": {**current, "correlation_id": "FORGED"}})

    def test_omitted_owner_stops_and_retains_immediate_predecessor(self):
        candidate = owner("REGISTERED")
        self.put(owner("MISSING_OWNER"))
        result = self.invoke({"generation": 223, "tasks": [candidate]}, {
            "task_id": "REGISTERED", "caller_surface": "AI_SESSION_GATE",
            "observed_registry_generation": 223,
            "checkin_context": {"session_id": "inert-test", "repository": "StegVerse-Labs/.github",
                                "components_under_mutation": ["shared-gate"]}})
        self.assertEqual(result["disposition"], "STOP_COLLISION")
        self.assertEqual(result["hard_collision_task_ids"], ["MISSING_OWNER"])
        self.assertEqual(result["unregistered_checked_out_shard_ids"], ["MISSING_OWNER"])
        self.assertTrue(result["unregistered_shards_are_collision_guards_only"])
        events = load_events(self.root / "events.jsonl")
        self.assertEqual([event["event_type"] for event in events], ["CHECK_IN", "STOPPED"])
        self.assertEqual(events[0]["event_sha256"], result["checkin_event_sha256"])
        self.assertEqual(events[1]["predecessor_event_sha256"], events[0]["event_sha256"])
        self.assertEqual(events[1]["event_sha256"], result["stopped_event_sha256"])
        self.assertTrue(all(event["authority_effect"] == "NONE" for event in events))

    def test_stale_generation_stops_before_overlap_evaluation(self):
        result = self.invoke({"generation": 223, "tasks": [owner("REGISTERED")]}, {
            "task_id": "REGISTERED", "caller_surface": "AI_SESSION_GATE",
            "observed_registry_generation": 222, "checkin_context": {"session_id": "stale-test"}})
        self.assertEqual(result["disposition"], "STOP_STALE_COORDINATION")
        self.assertFalse(result["write_pr_merge_handoff_claim_admissible"])
        self.assertEqual(load_events(self.root / "events.jsonl")[0]["registry_disposition"],
                         "STOP_STALE_COORDINATION")

    def test_corrupt_predecessor_rejected_before_recent_collision_readback(self):
        path = self.root / "checkin-events.jsonl"
        disp = {"task_id": "REGISTERED", "disposition": "CONTINUE", "authority_effect": "NONE"}
        first = append_event(path, {"event_type": "CHECK_IN", "task_id": "REGISTERED",
                                    "session_id": "s1", "registry_disposition": disp})
        append_event(path, {"event_type": "RETURNED", "task_id": "REGISTERED",
                            "session_id": "s1", "registry_disposition": disp})
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(rows[1]["predecessor_event_sha256"], first["event_sha256"])
        rows[1]["predecessor_event_sha256"] = "sha256:" + "0" * 64
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
        with self.assertRaisesRegex(ValueError, "event hash mismatch|predecessor chain mismatch"):
            load_events(path)

    def test_current_registered_task_evaluator_does_not_crash_on_real_shards(self):
        # Hosted source-only diagnostic, never an authenticated resident check-in.
        import subprocess
        candidate = json.loads((ROOT / "data/canonical-task-registry.json").read_text())
        env = dict(os.environ, STEGVERSE_TASK_REGISTRY_EVENT_LEDGER=str(self.root / "integration.jsonl"))
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_task_registry_collision_checkin.py")],
                              cwd=ROOT, input=json.dumps({
                                  "task_id": "SDK-UNTRUSTED-DEPENDENCY-EXECUTION-BOUNDARY-001",
                                  "caller_surface": "INTERNAL_CANONICAL_WORK_BOOTSTRAP",
                                  "observed_registry_generation": candidate["generation"],
                                  "checkin_context": {"session_id": "inert-source-only-diagnostic",
                                      "repository": "StegVerse-org/StegVerse-SDK",
                                      "components_under_mutation": ["sdk:untrusted-dependency-contract-and-inert-tests"]}}),
                              text=True, capture_output=True, env=env, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((self.root / "integration.jsonl").exists())


    def test_existing_resident_refresh_carries_gate_closure_not_runtime_ledger(self):
        source = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
        required = ("scripts/evaluate_task_registry_ai_session_checkin.py",
                    "scripts/evaluate_task_registry_collision_checkin.py",
                    "scripts/task_registry_checkin_event_history.py",
                    "scripts/validate_task_registration_substrate_resolution.py",
                    "scripts/audit_task_registry_session_gate_backlog.py",
                    "data/canonical-task-registry.json",
                    "data/task-registry-ai-ingress-policy.json",
                    "data/task-registry-general-checkin-caller-policy.json")
        self.assertTrue(all('Path("' + path + '")' in source for path in required))
        self.assertNotIn('Path("runtime/task-registry/checkin-events.jsonl")', source)


if __name__ == "__main__":
    unittest.main()
