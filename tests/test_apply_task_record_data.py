import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apply_task_record_data as atr  # noqa: E402

REGISTRY = ROOT / "data" / "canonical-task-registry.json"
SHARDS = ROOT / "data" / "canonical-task-records"


def first_task_id() -> str:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"][0]["task_id"]


def data(**overrides):
    value = {
        "schema": atr.DATA_SCHEMA,
        "work_items": {first_task_id(): [{"kind": "PULL_REQUEST", "repo": "StegVerse-Labs/.github", "number": 1,
                                          "state": "DRAFT", "head": "abc", "ci": "GREEN", "owner_approved": False}]},
        "human_actions": [{"id": "OQ-T1", "task_id": first_task_id(), "question": "q?", "default_until_answered": "hold",
                           "source_ref": "StegVerse-Labs/.github#1", "state": "OPEN"}],
    }
    value.update(overrides)
    return value


class ApplyTaskRecordDataTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        self.registry = self.dir / "canonical-task-registry.json"
        shutil.copy2(REGISTRY, self.registry)
        self.tip = json.loads(self.registry.read_text(encoding="utf-8"))["generation"]

    def run_apply(self, payload, tip=None, validators=()):
        return atr.apply(payload, registry_path=self.registry, task_shards=SHARDS,
                         tip_generation=self.tip if tip is None else tip, write=True, root=self.dir, validators=validators)

    def test_fence_allows_exactly_tip_plus_one_and_writes_only_the_data(self):
        before = json.loads(self.registry.read_text(encoding="utf-8"))
        report = self.run_apply(data())
        self.assertEqual((report["disposition"], report["generation"], report["files_changed"]), ("ALLOW", self.tip + 1, True))
        after = json.loads(self.registry.read_text(encoding="utf-8"))
        self.assertEqual(after["generation"], self.tip + 1)
        self.assertEqual(after["tasks"][0]["work_items"][0]["number"], 1)
        self.assertEqual(after["human_actions"][-1]["id"], "OQ-T1")
        for key in ("generation", "human_actions"):
            before.pop(key), after.pop(key)
        after["tasks"][0].pop("work_items")
        self.assertEqual(after, before)

    def test_fence_denies_tip_plus_two(self):
        # The working Registry is already one generation ahead of the live tip.
        original = self.registry.read_text(encoding="utf-8")
        with self.assertRaises(atr.Refused) as raised:
            self.run_apply(data(), tip=self.tip - 1)
        self.assertEqual(raised.exception.result["failure_code"], "REGISTRY_GENERATION_NOT_TIP_PLUS_ONE")
        self.assertEqual(set(atr.fence.SIX_FIELDS) - set(raised.exception.result), set())
        self.assertEqual(self.registry.read_text(encoding="utf-8"), original)

    def test_second_run_is_a_no_op(self):
        self.run_apply(data())
        applied = self.registry.read_text(encoding="utf-8")
        report = self.run_apply(data(), tip=self.tip + 1)
        self.assertEqual((report["disposition"], report["files_changed"]), ("NO_CHANGE", False))
        self.assertEqual(self.registry.read_text(encoding="utf-8"), applied)

    def test_unknown_task_id_is_refused(self):
        for payload in (data(work_items={"NO-SUCH-TASK-001": []}),
                        data(human_actions=[{**data()["human_actions"][0], "task_id": "NO-SUCH-TASK-001"}])):
            with self.subTest(payload=list(payload)):
                with self.assertRaises(atr.Refused) as raised:
                    self.run_apply(payload)
                self.assertEqual(raised.exception.result["failure_code"], "RECORD_DATA_UNKNOWN_TASK_ID")

    def test_shard_only_task_is_refused(self):
        in_registry = {t["task_id"] for t in json.loads(REGISTRY.read_text(encoding="utf-8"))["tasks"]}
        shard_only = next(p.stem for p in sorted(SHARDS.glob("*.json")) if p.stem not in in_registry)
        with self.assertRaises(atr.Refused) as raised:
            self.run_apply(data(work_items={shard_only: []}))
        self.assertEqual(raised.exception.result["failure_code"], "RECORD_DATA_TASK_NOT_IN_AGGREGATE_REGISTRY")

    def test_schema_mismatches_are_refused(self):
        bad_item = {"kind": "PULL_REQUEST", "repo": "x", "number": 1, "state": "DRAFT", "owner_approved": False}
        question = data()["human_actions"][0]
        for payload in (data(schema="other/v1"), data(work_items=[]), data(work_items={first_task_id(): [bad_item]}),
                        data(human_actions=[{**question, "question": ""}]), data(human_actions=[question, question])):
            with self.subTest(payload=json.dumps(payload)[:80]):
                with self.assertRaises(atr.Refused) as raised:
                    self.run_apply(payload)
                self.assertEqual(raised.exception.result["failure_code"], "RECORD_DATA_SCHEMA_MISMATCH")

    def test_failed_validator_restores_the_registry(self):
        (self.dir / "scripts").mkdir()
        (self.dir / "scripts" / "fail.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
        original = self.registry.read_text(encoding="utf-8")
        with self.assertRaises(atr.Refused) as raised:
            self.run_apply(data(), validators=("scripts/fail.py",))
        self.assertEqual(raised.exception.result["failure_code"], "RECORD_DATA_POST_APPLY_VALIDATION")
        self.assertEqual(self.registry.read_text(encoding="utf-8"), original)

    def test_writer_preserves_utf8_text(self):
        self.run_apply(data())
        text = self.registry.read_text(encoding="utf-8")
        if any(ord(ch) > 127 for ch in REGISTRY.read_text(encoding="utf-8")):
            self.assertTrue(any(ord(ch) > 127 for ch in text))
        self.assertNotIn("\\u2014", text)

    def test_cli_plan_only_and_refusal_exit_codes(self):
        payload = self.dir / "data.json"
        payload.write_text(json.dumps(data(schema="other/v1")), encoding="utf-8")
        done = subprocess.run([sys.executable, str(ROOT / "scripts/apply_task_record_data.py"), str(payload),
                               "--registry", str(self.registry), "--tip-ref", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertEqual(json.loads(done.stdout)["failure_code"], "RECORD_DATA_SCHEMA_MISMATCH")


if __name__ == "__main__":
    unittest.main()
