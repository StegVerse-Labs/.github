"""CI run-duration export from saved Actions run records. Every run here is SYNTHETIC."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import compute_ecosystem_offload_ratio as eor  # noqa: E402
import export_ci_run_durations as export  # noqa: E402

BRANCH = "claude/roadmap"


def api_run(run_id, start, end, branch=BRANCH, status="completed", repo="StegVerse-Labs/.github"):
    return {"id": run_id, "repository": {"full_name": repo}, "head_branch": branch, "head_sha": "a" * 40,
            "path": ".github/workflows/ci.yml", "status": status, "conclusion": "success",
            "run_started_at": start, "updated_at": end}


def page(*runs):
    return {"total_count": len(runs), "workflow_runs": list(runs)}


class ExportTests(unittest.TestCase):
    def test_keeps_completed_runs_on_the_branch_and_day_deduplicated_and_sorted(self):
        documents = {"a.json": page(api_run(2, "2026-10-18T13:00:00Z", "2026-10-18T13:05:00Z"),
                                    api_run(1, "2026-10-18T12:00:00Z", "2026-10-18T12:10:00Z"),
                                    api_run(3, "2026-10-18T12:00:00Z", "2026-10-18T12:01:00Z", branch="other"),
                                    api_run(4, "2026-10-18T12:00:00Z", "2026-10-18T12:01:00Z", status="in_progress"),
                                    api_run(5, "2026-10-17T12:00:00Z", "2026-10-17T12:01:00Z")),
                     "b.json": [page(api_run(1, "2026-10-18T12:00:00Z", "2026-10-18T12:10:00Z"))]}
        out = export.convert(documents, {BRANCH}, "2026-10-18", "SYNTHETIC")
        self.assertEqual([r["run_id"] for r in out["runs"]], [1, 2])
        self.assertEqual((out["schema"], out["runs"][0]["workflow"], out["runs"][0]["completed_at"]),
                         (eor.RUNS_SCHEMA, "ci.yml", "2026-10-18T12:10:00Z"))
        # The export is the EOR script's measured-E input: 15 minutes for the lane-day.
        lanes = {"schema": eor.LANES_SCHEMA, "lanes": {"roadmap": [{"repo": "StegVerse-Labs/.github", "head_branch": BRANCH}]}}
        row = eor.compute(out, "date,lane,session_id,llm_minutes\n", lanes)["rows"][0]
        self.assertEqual((row["E_seconds"], row["E_ci_minutes"], row["EOR_measured"]), (900, "15.00", None))

    def test_malformed_and_missing_inputs_fail_closed(self):
        for document in ({"runs": []}, [{"workflow_runs": "x"}], page({"id": 1})):
            with self.subTest(document=str(document)[:40]):
                with self.assertRaises(export.Refused) as raised:
                    export.convert({"x.json": document}, {BRANCH}, None, "s")
                self.assertIn(raised.exception.result["failure_code"], ("INPUT_SCHEMA", "INPUT_VALUE_INVALID"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "r.json"
            path.write_text(json.dumps(page()), encoding="utf-8")
            script = str(ROOT / "scripts/export_ci_run_durations.py")
            for args, missing in ((["--branch", BRANCH, "--source", "s"], "--runs"),
                                  (["--runs", str(path), "--source", "s"], "--branch"),
                                  (["--runs", str(path), "--branch", BRANCH], "--source")):
                with self.subTest(missing=missing):
                    done = subprocess.run([sys.executable, script, *args], capture_output=True, text=True)
                    self.assertEqual(done.returncode, 1)
                    self.assertEqual(json.loads(done.stdout)["evidence"]["input"], missing)
        source = (ROOT / "scripts/export_ci_run_durations.py").read_text(encoding="utf-8")
        for forbidden in ("urllib", "http.client", "socket", "requests", "subprocess", "datetime.now", "time.time"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
