import hashlib
import importlib.util
import json
import tempfile
import types
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_admission_job_observation.py"
spec = importlib.util.spec_from_file_location("evaluate_admission_job_observation", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

HEAD = "646bab278dd7c5abf9b86adbd089d6ecbf86412b"
OTHER = "eeb6f9bdfc7a10fafa2610058a66bf30e2e75ea5"
JOBS = ["consolidated-source-validators", "ratchet", "validate"]
EPOCH = 40
SIX = set(m.SIX_FIELDS)


def run(name, conclusion="success", status="completed", sha=HEAD, rid=1, started="2026-10-18T03:00:00Z"):
    r = {"name": name, "status": status, "conclusion": conclusion, "id": rid, "started_at": started}
    if sha is not ...:
        r["head_sha"] = sha
    return r


def ev(runs, head=HEAD, jobs=JOBS, **kw):
    kw.setdefault("hb_epoch", EPOCH)
    return m.evaluate({"check_runs": runs}, head, jobs, **kw)


class AdmissionJobObservationTests(unittest.TestCase):
    def assertSixFieldFailClosed(self, rec, code):
        self.assertEqual(rec["decision"], m.FAIL_CLOSED)
        self.assertEqual(rec["failure_code"], code)
        self.assertTrue(SIX <= set(rec))
        self.assertTrue(all(isinstance(rec[f], str) and rec[f] for f in SIX))
        self.assertTrue(m.seal_verifies(rec))

    def test_all_expected_jobs_success_is_ready(self):
        r = ev([run(j) for j in JOBS])
        self.assertEqual(r["decision"], m.READY)
        self.assertEqual(r["counts"], {m.PASS: 3, m.FAIL: 0, m.UNKNOWN: 0})

    def test_path_filtered_job_with_no_run_is_unknown_not_pass(self):
        # Labs#3224 at 646bab27: validate never triggered; two other jobs passed.
        r = ev([run("consolidated-source-validators"), run("ratchet")])
        self.assertEqual(r["decision"], m.NOT_READY)
        v = [j for j in r["jobs"] if j["job"] == "validate"][0]
        self.assertEqual(v["state"], m.UNKNOWN)
        self.assertIn("NO_CHECK_RUN_AT_HEAD", v["reason"])

    def test_skipped_neutral_cancelled_stale_null_are_unknown(self):
        for c in ("skipped", "neutral", "cancelled", "stale", None):
            r = ev([run("validate", conclusion=c)], jobs=["validate"])
            self.assertEqual(r["jobs"][0]["state"], m.UNKNOWN, c)
            self.assertEqual(r["decision"], m.NOT_READY)

    def test_pending_is_unknown(self):
        r = ev([run("ratchet", status="in_progress", conclusion=None)], jobs=["ratchet"])
        self.assertEqual(r["jobs"][0]["state"], m.UNKNOWN)

    def test_failure_class_is_fail(self):
        for c in ("failure", "timed_out", "action_required", "startup_failure"):
            r = ev([run("ratchet", conclusion=c)], jobs=["ratchet"])
            self.assertEqual(r["jobs"][0]["state"], m.FAIL, c)

    def test_run_for_other_head_is_not_evidence(self):
        r = ev([run("validate", sha=OTHER)], jobs=["validate"])
        self.assertEqual(r["jobs"][0]["state"], m.UNKNOWN)
        self.assertEqual(r["runs_not_evidence_for_head"], 1)

    def test_scenario_HEADLESS_CHECK_RUN_NOT_EVIDENCE_FOR_HEAD(self):
        # Lane C finding (2): head_sha null, missing or mismatched must be UNKNOWN, never PASS.
        for sha in (None, ..., "", OTHER, HEAD.upper()):
            r = ev([run("validate", sha=sha)], jobs=["validate"])
            self.assertEqual(r["jobs"][0]["state"], m.UNKNOWN, repr(sha))
            self.assertEqual(r["decision"], m.NOT_READY, repr(sha))

    def test_scenario_HEADLESS_CHECK_RUN_NOT_EVIDENCE_FOR_HEAD_mutation_negative(self):
        # Re-introduce the old filter (`not in (None, head_sha)`) into a copy of the source.
        # The mutant must admit the headless run, which proves the scenario test above catches it.
        src = SCRIPT.read_text(encoding="utf-8")
        new = 'return run.get("head_sha") == head_sha'
        old = 'return run.get("head_sha") in (None, head_sha)'
        self.assertEqual(src.count(new), 1)
        mutant = types.ModuleType("mutant")
        exec(compile(src.replace(new, old), "mutant", "exec"), mutant.__dict__)
        doc = {"check_runs": [run("validate", sha=None)]}
        self.assertEqual(mutant.evaluate(doc, HEAD, ["validate"], hb_epoch=EPOCH)["decision"], m.READY)
        self.assertEqual(m.evaluate(doc, HEAD, ["validate"], hb_epoch=EPOCH)["decision"], m.NOT_READY)

    def test_retry_resolved_by_latest_started_at(self):
        runs = [run("validate", "failure", rid=2, started="2026-10-18T01:00:00Z"),
                run("validate", "success", rid=1, started="2026-10-18T02:00:00Z")]
        self.assertEqual(ev(runs, jobs=["validate"])["decision"], m.READY)
        runs = [run("validate", "success", rid=1, started="2026-10-18T01:00:00Z"),
                run("validate", "failure", rid=2, started="2026-10-18T02:00:00Z")]
        self.assertEqual(ev(runs, jobs=["validate"])["jobs"][0]["state"], m.FAIL)

    def test_empty_expectation_is_six_field_fail_closed(self):
        for jobs in ([], None, [""]):
            self.assertSixFieldFailClosed(ev([], jobs=jobs), "EXPECTED_JOBS_NOT_DECLARED")

    def test_short_or_invalid_sha_is_six_field_fail_closed(self):
        for sha in (HEAD[:8], HEAD.upper(), HEAD[:-1] + "g", None, 123):
            self.assertSixFieldFailClosed(ev([], head=sha), "HEAD_SHA_INVALID")

    def test_hb_epoch_missing_or_invalid_is_fail_closed(self):
        self.assertSixFieldFailClosed(ev([run(j) for j in JOBS], hb_epoch=None), "HB_EPOCH_NOT_SUPPLIED")
        for bad in ("31", 31, "-40", "4.0", " 40", True, "x"):
            self.assertSixFieldFailClosed(ev([run(j) for j in JOBS], hb_epoch=bad), "HB_EPOCH_INVALID")
        self.assertEqual(ev([run(j) for j in JOBS], hb_epoch="32")["hb_epoch"], 32)

    def test_malformed_document_and_change_digest_are_fail_closed(self):
        self.assertSixFieldFailClosed(m.evaluate(None, HEAD, JOBS, hb_epoch=EPOCH), "CHECK_RUNS_DOCUMENT_MALFORMED")
        self.assertSixFieldFailClosed(ev([], change_digest_value="sha256:abc"), "CHANGE_DIGEST_INVALID")

    def test_seal_and_change_digest_follow_tvc_rule(self):
        content = [{"path": "b", "blob_digest": "sha256:" + "1" * 64, "writer_session": "s", "deleted": False},
                   {"path": "a", "blob_digest": "sha256:" + "2" * 64, "writer_session": "s", "deleted": False}]
        canon = json.dumps(sorted(content, key=lambda e: e["path"]), sort_keys=True,
                           separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        cd = m.change_digest(content)
        self.assertEqual(cd, "sha256:" + hashlib.sha256(canon).hexdigest())
        rec = ev([run(j) for j in JOBS], change_digest_value=cd)
        self.assertEqual(rec["change_digest"], cd)
        self.assertEqual(rec["hb_epoch"], EPOCH)
        self.assertTrue(m.seal_verifies(rec))
        body = {k: v for k, v in rec.items() if k != m.SEAL_FIELD}
        self.assertEqual(rec[m.SEAL_FIELD], "sha256:" + hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest())
        tampered = dict(rec, decision=m.NOT_READY)
        self.assertFalse(m.seal_verifies(tampered))

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "runs.json"
            p.write_text(json.dumps({"check_runs": [run(j) for j in JOBS[:2]]}), encoding="utf-8")
            args = ["--check-runs", str(p), "--head-sha", HEAD, "--hb-epoch", "40"] + sum((["--expect", j] for j in JOBS), [])
            self.assertEqual(m.main(args), 1)
            p.write_text(json.dumps({"check_runs": [run(j) for j in JOBS]}), encoding="utf-8")
            self.assertEqual(m.main(args), 0)
            self.assertEqual(m.main(["--check-runs", str(p), "--head-sha", HEAD, "--expect", "validate"]), 2)
            self.assertEqual(m.main(["--check-runs", str(p), "--head-sha", HEAD, "--hb-epoch", "40"]), 2)


if __name__ == "__main__":
    unittest.main()
