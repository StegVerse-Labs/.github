"""Ecosystem offload ratio from committed inputs. Every run and session here is SYNTHETIC."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import compute_ecosystem_offload_ratio as eor  # noqa: E402

LANE_BRANCH = {"repo": "StegVerse-Labs/.github", "head_branch": "claude/roadmap"}


def lanes(**extra):
    value = {"roadmap": [LANE_BRANCH]}
    value.update(extra)
    return {"schema": eor.LANES_SCHEMA, "lanes": value}


def run(run_id, start, end, branch="claude/roadmap", repo="StegVerse-Labs/.github"):
    return {"repo": repo, "run_id": run_id, "workflow": "ci.yml", "head_branch": branch,
            "run_started_at": start, "completed_at": end}


def runs(*items):
    return {"schema": eor.RUNS_SCHEMA, "runs": list(items)}


SESSIONS = "date,lane,session_id,llm_minutes\n2026-10-18,roadmap,session_A,86\n"


class OffloadRatioTests(unittest.TestCase):
    def test_reproduces_the_rm11_cumulative_window_exactly(self):
        # RM11 cumulative: E = 29.0 min, L = 86 min, EOR = 29/115 (25.22%).
        out = eor.compute(runs(run(1, "2026-10-18T12:20:00Z", "2026-10-18T12:40:00Z"),
                               run(2, "2026-10-18T13:00:00Z", "2026-10-18T13:09:00Z")), SESSIONS, lanes())
        (row,) = out["rows"]
        self.assertEqual((row["E_seconds"], row["E_ci_minutes"], row["L_measured_minutes"]), (1740, "29.00", "86.00"))
        self.assertEqual((row["EOR_measured"], row["EOR_measured_percent"], row["measured"]), ("29/115", "25.22", "COMPUTED"))
        self.assertEqual((row["EOR_reported"], row["reported"]), (None, "NONE"))
        self.assertEqual(row["runs"], ["StegVerse-Labs/.github#1", "StegVerse-Labs/.github#2"])

    def test_runs_attribute_to_their_start_day_and_lane(self):
        out = eor.compute(runs(run(1, "2026-10-17T23:59:00Z", "2026-10-18T00:01:00Z"),
                               run(2, "2026-10-18T10:00:00Z", "2026-10-18T10:01:00Z", branch="other",
                                   repo="StegVerse-org/.github")),
                          SESSIONS, lanes(other=[{"repo": "StegVerse-org/.github", "head_branch": "other"}]))
        keyed = {(r["lane"], r["date"]): r for r in out["rows"]}
        self.assertEqual(keyed[("roadmap", "2026-10-17")]["E_seconds"], 120)
        self.assertEqual((keyed[("roadmap", "2026-10-17")]["measured"], keyed[("roadmap", "2026-10-17")]["EOR_measured"]),
                         ("L_NOT_SUPPLIED_FOR_LANE_DAY", None))
        self.assertEqual(keyed[("other", "2026-10-18")]["E_seconds"], 60)
        self.assertEqual(keyed[("roadmap", "2026-10-18")]["EOR_measured"], "0/1")

    def test_unmapped_and_incomplete_runs_are_reported_not_counted(self):
        pending = run(3, "2026-10-18T12:00:00Z", None)
        out = eor.compute(runs(run(1, "2026-10-18T12:00:00Z", "2026-10-18T12:10:00Z", branch="unmapped"), pending),
                          SESSIONS, lanes())
        self.assertEqual(out["unattributed_runs"], ["StegVerse-Labs/.github#1"])
        self.assertEqual(out["incomplete_runs"], ["StegVerse-Labs/.github#3"])
        self.assertEqual(out["rows"][0]["E_seconds"], 0)

    def test_deterministic_and_order_independent(self):
        a, b = run(1, "2026-10-18T12:00:00Z", "2026-10-18T12:07:00Z"), run(2, "2026-10-18T13:00:00Z", "2026-10-18T13:02:30Z")
        self.assertEqual(eor.compute(runs(a, b), SESSIONS, lanes()), eor.compute(runs(b, a), SESSIONS, lanes()))

    def test_malformed_inputs_fail_closed_with_six_fields(self):
        cases = {
            "INPUT_SCHEMA": (runs(), "date,lane\n", lanes()),
            "RUN_LANE_AMBIGUOUS": (runs(), SESSIONS, lanes(twin=[LANE_BRANCH])),
            "INPUT_VALUE_INVALID": (runs(run(1, "2026-10-18T12:00:00Z", "2026-10-18T11:00:00Z")), SESSIONS, lanes()),
        }
        for code, args in cases.items():
            with self.subTest(code=code):
                with self.assertRaises(eor.Refused) as raised:
                    eor.compute(*args)
                result = raised.exception.result
                self.assertEqual((result["disposition"], result["failure_code"]), ("FAIL_CLOSED", code))
                for field in ("failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
                              "owning_existing_goal", "next_attempt"):
                    self.assertTrue(result[field], field)
        for bad in ("2026-10-18,roadmap,s,-1\n", "2026-10-18,roadmap,s,NaN\n", "18/10/2026,roadmap,s,1\n",
                    "2026-10-18,roadmap,s\n"):
            with self.subTest(row=bad):
                with self.assertRaises(eor.Refused):
                    eor.compute(runs(), SESSIONS + bad, lanes())
        for stamp in ("2026-10-18 12:00:00", "2026-02-30T12:00:00Z", 1760788800):
            with self.subTest(stamp=stamp):
                with self.assertRaises(eor.Refused):
                    eor.compute(runs(run(1, stamp, "2026-10-18T12:00:00Z")), SESSIONS, lanes())
        with self.assertRaises(eor.Refused):
            eor.compute(runs(run(1, "2026-10-18T12:00:00Z", "2026-10-18T12:01:00Z"),
                             run(1, "2026-10-18T12:00:00Z", "2026-10-18T12:01:00Z")), SESSIONS, lanes())

    def test_lane_reported_usage_is_kept_apart_and_labelled(self):
        usage = ("date,lane,unit_id,e_minutes,l_minutes,source\n"
                 "2026-10-18,coordinator,C1,3,20,sandbox run (SYNTHETIC)\n"
                 "2026-10-18,coordinator,C2,3,25,chat run (SYNTHETIC)\n"
                 "2026-10-18,roadmap,RM18,0.5,10,local apply (SYNTHETIC)\n")
        out = eor.compute(runs(run(1, "2026-10-18T12:00:00Z", "2026-10-18T12:06:00Z")), SESSIONS, lanes(), usage)
        keyed = {r["lane"]: r for r in out["rows"]}
        coordinator = keyed["coordinator"]
        self.assertEqual((coordinator["E_reported_minutes"], coordinator["L_reported_minutes"], coordinator["EOR_reported"],
                          coordinator["units"], coordinator["reported"]), ("6.00", "45.00", "2/17", ["C1", "C2"], "LANE_REPORTED"))
        self.assertEqual((coordinator["EOR_measured"], coordinator["measured"]), (None, "L_NOT_SUPPLIED_FOR_LANE_DAY"))
        # Measured and reported minutes are never summed into one ratio (WU-V12 defect a).
        roadmap = keyed["roadmap"]
        self.assertEqual((roadmap["E_ci_minutes"], roadmap["L_measured_minutes"], roadmap["EOR_measured"]), ("6.00", "86.00", "3/46"))
        self.assertEqual((roadmap["E_reported_minutes"], roadmap["L_reported_minutes"], roadmap["EOR_reported"]),
                         ("0.50", "10.00", "1/21"))
        self.assertNotIn("EOR", roadmap)
        # WU-V12 repro: a 10-min run plus a 10-min session is 1/2 measured, whatever a lane reports beside it.
        ten = eor.compute(runs(run(9, "2026-10-18T12:00:00Z", "2026-10-18T12:10:00Z")),
                          "date,lane,session_id,llm_minutes\n2026-10-18,roadmap,s1,10\n", lanes(),
                          "date,lane,unit_id,e_minutes,l_minutes,source\n2026-10-18,roadmap,u1,0,30,self\n")["rows"][0]
        self.assertEqual((ten["EOR_measured"], ten["L_measured_minutes"], ten["EOR_reported"]), ("1/2", "10.00", "0/1"))
        for bad in ("date,lane,unit\n", "date,lane,unit_id,e_minutes,l_minutes,source\n2026-10-18,x,U,1,-1,s\n",
                    "date,lane,unit_id,e_minutes,l_minutes,source\n2026-10-18,x,U,1,1,\n",
                    "date,lane,unit_id,e_minutes,l_minutes,source\n2026-10-18,x,U,1,1,s\n2026-10-18,x,U,2,2,s\n"):
            with self.subTest(table=bad):
                with self.assertRaises(eor.Refused):
                    eor.compute(runs(), SESSIONS, lanes(), bad)

    def test_rounding_is_exact_half_even_and_large_values_do_not_crash(self):
        # WU-V12 defect c: e=0.0050000000000000000000000000000001, l=99.995... is 0.01 exactly, not 0.00.
        usage = ("date,lane,unit_id,e_minutes,l_minutes,source\n"
                 "2026-10-18,x,u,0.0050000000000000000000000000000001,99.9949999999999999999999999999999999,s\n")
        row = eor.compute(runs(), "date,lane,session_id,llm_minutes\n",
                          lanes(), usage)["rows"][0]
        self.assertEqual(row["E_reported_minutes"], "0.01")
        self.assertEqual([eor._minutes(eor.Fraction(n, 1000)) for n in (5, 15, 25, 35)], ["0.00", "0.02", "0.02", "0.04"])
        # WU-V12 defect b: a value beyond 28 significant digits is computed, not a traceback.
        big = eor.compute(runs(), "date,lane,session_id,llm_minutes\n2026-10-18,roadmap,s1,1E+30\n", lanes())["rows"][0]
        self.assertEqual(big["L_measured_minutes"], "1" + "0" * 30 + ".00")

    def test_duplicate_sessions_run_id_types_and_impossible_dates_are_refused(self):
        dup = "date,lane,session_id,llm_minutes\n2026-10-18,roadmap,s1,10\n2026-10-18,roadmap,s1,10\n"
        for args in ((runs(), dup, lanes()),
                     (runs(run(1, "2026-10-18T12:00:00Z", "2026-10-18T12:01:00Z"), run("1", "2026-10-18T12:00:00Z", "2026-10-18T12:01:00Z")),
                      SESSIONS, lanes()),
                     (runs(run(True, "2026-10-18T12:00:00Z", "2026-10-18T12:01:00Z")), SESSIONS, lanes()),
                     (runs(), "date,lane,session_id,llm_minutes\n2026-13-45,roadmap,s1,1\n", lanes())):
            with self.subTest(args=str(args)[:80]):
                with self.assertRaises(eor.Refused) as raised:
                    eor.compute(*args)
                self.assertEqual(raised.exception.result["failure_code"], "INPUT_VALUE_INVALID")

    def test_cli_names_each_missing_input_and_reads_no_network(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            (d / "r.json").write_text(json.dumps(runs(run(1, "2026-10-18T12:00:00Z", "2026-10-18T12:30:00Z"))))
            (d / "s.csv").write_text(SESSIONS)
            (d / "l.json").write_text(json.dumps(lanes()))
            script = str(ROOT / "scripts/compute_ecosystem_offload_ratio.py")
            full = ["--ci-runs", str(d / "r.json"), "--sessions", str(d / "s.csv"), "--lanes", str(d / "l.json")]
            done = subprocess.run([sys.executable, script, *full], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0)
            self.assertEqual(json.loads(done.stdout)["rows"][0]["EOR_measured"], "15/58")
            # Without a session table the measured E still computes; the measured ratio is null.
            no_sessions = full[:2] + full[4:]
            done = subprocess.run([sys.executable, script, *no_sessions], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0)
            row = json.loads(done.stdout)["rows"][0]
            self.assertEqual((row["E_seconds"], row["EOR_measured"], row["measured"]), (1800, None, "L_NOT_SUPPLIED_FOR_LANE_DAY"))
            for drop in (0, 4):
                with self.subTest(missing=full[drop]):
                    args = full[:drop] + full[drop + 2:]
                    done = subprocess.run([sys.executable, script, *args], capture_output=True, text=True)
                    self.assertEqual(done.returncode, 1)
                    out = json.loads(done.stdout)
                    self.assertEqual((out["failure_code"], out["evidence"]["input"]), ("INPUT_NOT_SUPPLIED", full[drop]))
        source = (ROOT / "scripts/compute_ecosystem_offload_ratio.py").read_text(encoding="utf-8")
        for forbidden in ("urllib", "http.client", "socket", "requests", "subprocess", "datetime.now", "time.time"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
