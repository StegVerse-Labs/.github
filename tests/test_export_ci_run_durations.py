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
                                  (["--runs", str(path), "--source", "s"], "--branch|--lanes|--all-branches"),
                                  (["--runs", str(path), "--source", "s", "--branch", BRANCH, "--all-branches"],
                                   "--branch|--lanes|--all-branches"),
                                  (["--runs", str(path), "--branch", BRANCH], "--source")):
                with self.subTest(missing=missing):
                    done = subprocess.run([sys.executable, script, *args], capture_output=True, text=True)
                    self.assertEqual(done.returncode, 1)
                    self.assertEqual(json.loads(done.stdout)["evidence"]["input"], missing)
        source = (ROOT / "scripts/export_ci_run_durations.py").read_text(encoding="utf-8")
        for forbidden in ("urllib", "http.client", "socket", "requests", "subprocess", "datetime.now", "time.time"):
            self.assertNotIn(forbidden, source)


    def test_lane_map_or_all_branches_select_runs_and_compute_reports_repositories(self):
        runs = page(api_run(1, "2026-10-18T12:00:00Z", "2026-10-18T12:10:00Z"),
                    api_run(2, "2026-10-18T12:00:00Z", "2026-10-18T12:20:00Z", branch="main"),
                    api_run(3, "2026-10-18T12:00:00Z", "2026-10-18T12:05:00Z", branch="laneb/x",
                            repo="StegVerse-org/StegVerse-SDK"))
        lanes = {"schema": eor.LANES_SCHEMA, "lanes": {
            "roadmap": [{"repo": "StegVerse-Labs/.github", "head_branch": BRANCH}],
            "B": [{"repo": "StegVerse-org/StegVerse-SDK", "head_branch": "laneb/x"}]}}
        with tempfile.TemporaryDirectory() as directory:
            runs_path, lanes_path = Path(directory) / "r.json", Path(directory) / "l.json"
            runs_path.write_text(json.dumps(runs), encoding="utf-8")
            lanes_path.write_text(json.dumps(lanes), encoding="utf-8")
            script = str(ROOT / "scripts/export_ci_run_durations.py")
            outputs = {}
            for flag in (["--lanes", str(lanes_path)], ["--all-branches"]):
                done = subprocess.run([sys.executable, script, "--runs", str(runs_path), "--source", "s", *flag],
                                      capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, done.stdout)
                outputs[flag[0]] = json.loads(done.stdout)
        self.assertEqual(sorted(r["run_id"] for r in outputs["--lanes"]["runs"]), [1, 3])
        self.assertEqual(sorted(r["run_id"] for r in outputs["--all-branches"]["runs"]), [1, 2, 3])
        usage = ("date,lane,unit_id,e_minutes,l_minutes,source\n2026-10-18,roadmap,u1,0,20,s\n"
                 "2026-10-18,B,u2,0,15,s\n2026-10-18,C,u3,0,99,s\n")
        out = eor.compute(outputs["--all-branches"], "date,lane,session_id,llm_minutes\n", lanes, usage)
        repos = {r["repo"]: r for r in out["repositories"]}
        self.assertEqual((repos["StegVerse-Labs/.github"]["runs"], repos["StegVerse-Labs/.github"]["E_ci_minutes"],
                          repos["StegVerse-Labs/.github"]["E_attributed_minutes"],
                          repos["StegVerse-Labs/.github"]["E_unattributed_minutes"]), (2, "30.00", "10.00", "20.00"))
        self.assertEqual(repos["StegVerse-org/StegVerse-SDK"]["lanes"], {"B": "5.00"})
        cumulative = out["cumulative"]
        # Measured E counts lane-attributed runs only; lane C has no measured E, so its L is left out.
        self.assertEqual((cumulative["E_ci_minutes"], cumulative["EOR_measured"], cumulative["measured"]),
                         ("15.00", None, "L_NOT_SUPPLIED"))
        self.assertEqual((cumulative["L_committed_minutes"], cumulative["EOR_committed"], cumulative["committed_lane_days"]),
                         ("35.00", "3/10", ["B:2026-10-18", "roadmap:2026-10-18"]))
        # A dated export covers only its day: committed L on another day is not paired with E = 0.
        dated = export.convert({"r.json": runs}, None, "2026-10-18", "s")
        self.assertEqual(dated["date"], "2026-10-18")
        out = eor.compute(dated, "date,lane,session_id,llm_minutes\n", lanes,
                          usage + "2026-10-17,roadmap,u0,0,50,s\n")
        other_day = {(r["lane"], r["date"]): r for r in out["rows"]}[("roadmap", "2026-10-17")]
        self.assertEqual((other_day["EOR_committed"], other_day["committed"]), (None, "E_NOT_MEASURED_FOR_DAY"))
        self.assertEqual((out["cumulative"]["L_committed_minutes"], out["cumulative"]["EOR_committed"]), ("35.00", "3/10"))


if __name__ == "__main__":
    unittest.main()
