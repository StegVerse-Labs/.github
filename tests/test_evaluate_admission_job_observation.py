import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_admission_job_observation.py"
spec = importlib.util.spec_from_file_location("evaluate_admission_job_observation", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

HEAD = "646bab278dd7c5abf9b86adbd089d6ecbf86412b"
OTHER = "eeb6f9bdfc7a10fafa2610058a66bf30e2e75ea5"
JOBS = ["consolidated-source-validators", "ratchet", "validate"]


def run(name, conclusion="success", status="completed", sha=HEAD, rid=1, started="2026-10-18T03:00:00Z"):
    return {"name": name, "status": status, "conclusion": conclusion, "head_sha": sha, "id": rid, "started_at": started}


class AdmissionJobObservationTests(unittest.TestCase):
    def test_all_expected_jobs_success_is_ready(self):
        r = m.evaluate({"check_runs": [run(j) for j in JOBS]}, HEAD, JOBS)
        self.assertEqual(r["decision"], m.READY)
        self.assertEqual(r["counts"], {m.PASS: 3, m.FAIL: 0, m.UNKNOWN: 0})

    def test_path_filtered_job_with_no_run_is_unknown_not_pass(self):
        # Labs#3224 at 646bab27: validate never triggered; two other jobs passed.
        r = m.evaluate({"check_runs": [run("consolidated-source-validators"), run("ratchet")]}, HEAD, JOBS)
        self.assertEqual(r["decision"], m.NOT_READY)
        v = [j for j in r["jobs"] if j["job"] == "validate"][0]
        self.assertEqual(v["state"], m.UNKNOWN)
        self.assertIn("NO_CHECK_RUN_AT_HEAD", v["reason"])

    def test_skipped_neutral_cancelled_are_unknown(self):
        for c in ("skipped", "neutral", "cancelled", "stale", None):
            r = m.evaluate({"check_runs": [run("validate", conclusion=c)]}, HEAD, ["validate"])
            self.assertEqual(r["jobs"][0]["state"], m.UNKNOWN, c)
            self.assertEqual(r["decision"], m.NOT_READY)

    def test_pending_is_unknown(self):
        r = m.evaluate({"check_runs": [run("ratchet", status="in_progress", conclusion=None)]}, HEAD, ["ratchet"])
        self.assertEqual(r["jobs"][0]["state"], m.UNKNOWN)

    def test_failure_is_fail(self):
        r = m.evaluate({"check_runs": [run("ratchet", conclusion="failure")]}, HEAD, ["ratchet"])
        self.assertEqual(r["jobs"][0]["state"], m.FAIL)
        self.assertEqual(r["decision"], m.NOT_READY)

    def test_run_for_other_head_is_not_evidence(self):
        r = m.evaluate({"check_runs": [run("validate", sha=OTHER)]}, HEAD, ["validate"])
        self.assertEqual(r["jobs"][0]["state"], m.UNKNOWN)
        self.assertEqual(r["ignored_runs_for_other_heads"], 1)

    def test_latest_attempt_wins(self):
        runs = [run("validate", "failure", rid=1, started="2026-10-18T01:00:00Z"),
                run("validate", "success", rid=2, started="2026-10-18T02:00:00Z")]
        self.assertEqual(m.evaluate({"check_runs": runs}, HEAD, ["validate"])["decision"], m.READY)

    def test_empty_expectation_and_short_sha_refused(self):
        with self.assertRaises(ValueError):
            m.evaluate({"check_runs": []}, HEAD, [])
        with self.assertRaises(ValueError):
            m.evaluate({"check_runs": []}, HEAD[:8], ["validate"])

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "runs.json"
            p.write_text(json.dumps({"check_runs": [run(j) for j in JOBS[:2]]}), encoding="utf-8")
            args = ["--check-runs", str(p), "--head-sha", HEAD] + sum((["--expect", j] for j in JOBS), [])
            self.assertEqual(m.main(args), 1)
            p.write_text(json.dumps({"check_runs": [run(j) for j in JOBS]}), encoding="utf-8")
            self.assertEqual(m.main(args), 0)


if __name__ == "__main__":
    unittest.main()
