"""Owner-apply rehearsal: digest binding, fail-closed inputs and the three-step outcome (fake runner)."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import rehearse_owner_apply as rehearsal  # noqa: E402

SIX = {"failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt"}


def runner(*dispositions):
    calls = []
    answers = iter(dispositions)

    def run(args, cwd):
        calls.append(args)
        return {"disposition": next(answers), "generation": 320}
    return run, calls


class RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data = Path(self.temp.name) / "data.json"
        self.data.write_text('{"schema": "x"}\n', encoding="utf-8")
        self.digest = hashlib.sha256(self.data.read_bytes()).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def refused(self, code, *args, **kwargs):
        with self.assertRaises(rehearsal.Refused) as caught:
            rehearsal.rehearse(*args, **kwargs)
        self.assertEqual(caught.exception.result["failure_code"], code)
        self.assertTrue(SIX <= set(caught.exception.result))
        return caught.exception.result

    def test_absent_file_or_digest_fails_closed(self):
        run, calls = runner()
        self.refused("REHEARSAL_INPUT_NOT_SUPPLIED", self.data, "", "origin/main", Path("."), run)
        self.refused("REHEARSAL_INPUT_NOT_SUPPLIED", self.data.with_name("absent.json"), self.digest, "origin/main",
                     Path("."), run)
        self.assertEqual(calls, [])

    def test_digest_mismatch_fails_closed_before_any_apply(self):
        run, calls = runner()
        result = self.refused("REHEARSAL_DIGEST_MISMATCH", self.data, "0" * 64, "origin/main", Path("."), run)
        self.assertEqual(result["evidence"]["actual"], self.digest)
        self.assertEqual(calls, [])

    def test_plan_apply_rerun_must_be_allow_allow_no_change(self):
        run, calls = runner("ALLOW", "ALLOW", "NO_CHANGE")
        result = rehearsal.rehearse(self.data, self.digest.upper(), "origin/main", Path("."), run)
        self.assertEqual(result["disposition"], "ALLOW")
        self.assertEqual([("--apply" in call) for call in calls], [False, True, False])
        self.assertTrue(all(call[0] == str(self.data.resolve()) for call in calls))
        run, _ = runner("ALLOW", "ALLOW", "ALLOW")
        self.refused("REHEARSAL_NOT_ALLOW", self.data, self.digest, "origin/main", Path("."), run)
        run, _ = runner("FAIL_CLOSED")
        self.refused("REHEARSAL_NOT_ALLOW", self.data, self.digest, "origin/main", Path("."), run)

    def test_already_applied_data_passes_as_no_change(self):
        run, calls = runner("NO_CHANGE")
        result = rehearsal.rehearse(self.data, self.digest, "origin/main", Path("."), run)
        self.assertEqual((result["disposition"], list(result["steps"])), ("ALLOW", ["plan"]))
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
