"""ADMISSION_MISS_RATE producer (resident-runtime/admission_miss_rate.py): admission decisions joined with later observed
outcomes under the definition declared in NWI-S3.json; UNKNOWN never counted; misses fed to SCENARIO_CORPUS_APPEND."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    if name not in sys.modules:
        s = importlib.util.spec_from_file_location(name, ROOT / rel)
        m = importlib.util.module_from_spec(s)
        sys.modules[name] = m
        s.loader.exec_module(m)
    return sys.modules[name]


amr = _load("admission_miss_rate", "resident-runtime/admission_miss_rate.py")
bf = _load("build_sv_native_fixtures", "scripts/build_sv_native_fixtures.py")
ss = _load("schema_subset", "resident-runtime/schema_subset.py")
al, wi, sg = amr.al, amr.wi, amr.sg
HB = "469411750"
CASES = {c["case_id"]: c["input"] for c in
         json.loads((ROOT / "data/sv-work-items/e0-witnesses/nwi-s3-admission-miss-rate.json").read_text())["cases"]}
SNAPSHOT = json.loads((ROOT / "data/sv-work-items/stage-thresholds/s1-baseline-snapshot.json").read_text())


def six(r):
    return r["disposition"] != "ALLOW" and all(isinstance(r.get(k), str) and r[k] for k in amr.SIX)


def lref(n):
    return "refs/stegverse/organization-ledger@%s:receipts/%064x.json" % ("9" * 40, n)


def dec(n, disp, seq, cd=None, base=None):
    return {"receipt_ref": lref(n), "disposition": disp, "ledger_seq": seq,
            "change": {"repository": "StegVerse-Labs/.github", "head_commit": "%040x" % n,
                       **({"change_digest": cd, "base": base} if cd else {})}}


def miss(n, *, correcting=None, gap="MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED", paths=(".github/workflows/x.yml",)):
    ch = {"change_id": "svc:%064x" % n, "lifecycle_state": "APPLIED", "head": {"change_digest": "sha256:%064x" % n},
          "touched_paths": list(paths)}
    return al.admission_miss(ch, admission_receipt_ref=lref(n), correcting_ref=correcting or lref(5000 + n), miss_kind="REVERT",
                             predicate_gap=gap, class_ids=[], hb_epoch=HB)


def held(n):
    return amr.admission_outcome_held(admission_receipt_ref=lref(n), evidence_ref=lref(6000 + n), observed="held", hb_epoch=HB)


class DefinitionTests(unittest.TestCase):
    def test_the_miss_is_defined_in_the_nwi_s3_manifest(self):
        d = amr.definition()
        m = json.loads(amr.STAGE_FILE.read_text())["metric_definitions"]["admission_miss_rate"]
        self.assertEqual(d["definition_sha256"], wi.sha(m))
        self.assertEqual(set(d["miss"]), {"FALSE_ADMIT", "FALSE_REFUSAL"})
        self.assertEqual(d["min_observed_outcomes"], 1)
        self.assertEqual(sorted(d["false_admit_miss_kinds"]), ["CORRECTION", "REFUSAL", "REVERT"])

    def test_an_undefined_metric_fails_closed(self):
        stage = json.loads(amr.STAGE_FILE.read_text()); del stage["metric_definitions"]
        out = amr.admission_miss_rate_e0([dec(1, "ALLOW", 1)], [held(1)], stage=stage)
        self.assertTrue(six(out)); self.assertEqual(out["failure_code"], "ADMISSION_MISS_DEFINITION_UNDECLARED")
        self.assertEqual(out["retry_entrypoint"], amr.ENTRY + "definition")


class ProducerTests(unittest.TestCase):
    def test_current_ledger_value_is_unknown_and_fails_closed(self):
        out = amr.admission_miss_rate_e0(SNAPSHOT["decisions"], SNAPSHOT["outcomes"])
        self.assertTrue(six(out))
        self.assertEqual((out["failure_code"], out["admission_miss_rate"]), ("ADMISSION_MISS_RATE_UNOBSERVED", "UNKNOWN"))
        self.assertEqual(out["counts"]["UNKNOWN"], len(SNAPSHOT["decisions"]))
        self.assertGreater(len(SNAPSHOT["decisions"]), 0)
        self.assertTrue(all(wi.LEDGER_RECEIPT_REF.match(d["receipt_ref"]) for d in SNAPSHOT["decisions"]))
        current = json.loads((ROOT / "data/sv-work-items/stage-thresholds/admission-miss-rate.current.json").read_text())
        self.assertEqual({k: current[k] for k in ("disposition", "failure_code", "admission_miss_rate", "counts")},
                         {k: out[k] for k in ("disposition", "failure_code", "admission_miss_rate", "counts")})

    def test_rate_over_observed_outcomes_only(self):
        out = amr.admission_miss_rate_e0([dec(1, "ALLOW", 1), dec(2, "ALLOW", 2), dec(3, "ALLOW", 3), dec(4, "ALLOW", 4)],
                                         [miss(1), held(2), held(3)])
        self.assertEqual((out["disposition"], out["admission_miss_rate"], out["observed"]), ("ALLOW", 1 / 3, 3))
        self.assertEqual(out["counts"]["UNKNOWN"], 1)
        r = out["record"]
        self.assertEqual(r["record_digest"], wi.sha({k: v for k, v in r.items() if k != "record_digest"}))
        self.assertEqual(out["gate_evidence"]["ADMISSION_MISS_RATE"]["admission_miss_rate"], 1 / 3)
        self.assertEqual([c["origin"] for c in out["learning_candidates"]], ["ADMISSION_MISS"])

    def test_false_refusal_needs_the_same_change_at_the_same_base(self):
        b, cd = {"registry_generation": 1, "ledger_head": "a" * 40}, "sha256:" + "c" * 64
        same = amr.admission_miss_rate_e0([dec(1, "DENY", 1, cd, b), dec(2, "ALLOW", 2, cd, b)], [held(2)])
        self.assertEqual((same["counts"]["FALSE_REFUSAL"], same["admission_miss_rate"]), (1, 0.5))
        other = amr.admission_miss_rate_e0([dec(1, "DENY", 1, cd, b), dec(2, "ALLOW", 2, cd, {**b, "registry_generation": 2})], [held(2)])
        self.assertEqual((other["counts"]["FALSE_REFUSAL"], other["counts"]["UNKNOWN"], other["admission_miss_rate"]), (0, 1, 0.0))
        earlier = amr.admission_miss_rate_e0([dec(1, "DENY", 2, cd, b), dec(2, "ALLOW", 1, cd, b)], [held(2)])
        self.assertEqual(earlier["counts"]["FALSE_REFUSAL"], 0)

    def test_fail_closed_decisions_are_never_misses(self):
        b, cd = {"registry_generation": 1, "ledger_head": "a" * 40}, "sha256:" + "c" * 64
        out = amr.admission_miss_rate_e0([dec(1, "FAIL_CLOSED", 1, cd, b), dec(2, "ALLOW", 2, cd, b)], [held(2)])
        self.assertEqual((out["counts"]["NOT_APPLICABLE"], out["misses"]), (1, 0))

    def test_a_miss_outranks_a_contradicting_held_record(self):
        out = amr.admission_miss_rate_e0([dec(1, "ALLOW", 1)], [miss(1), held(1)])
        self.assertEqual((out["counts"]["FALSE_ADMIT"], out["record"]["joined"][0]["contradicted_held"]), (1, True))

    def test_ungrounded_outcomes_are_not_counted(self):
        tampered = {**held(1), "admission_receipt_ref": lref(2)}
        unledgered = miss(3, correcting="fixture-ledger/receipts/r.json#fixture:r")
        out = amr.admission_miss_rate_e0([dec(1, "ALLOW", 1), dec(2, "ALLOW", 2), dec(3, "ALLOW", 3)],
                                         [tampered, unledgered, {"schema": "other"}])
        self.assertEqual(out["failure_code"], "ADMISSION_MISS_RATE_UNOBSERVED")
        self.assertEqual(len(out["outcomes_not_grounded"]), 3)

    def test_unledgered_and_malformed_decisions_are_excluded(self):
        out = amr.admission_miss_rate_e0([{**dec(1, "ALLOW", 1), "receipt_ref": "receipts/x.json"}, {"disposition": "ALLOW"}], [held(1)])
        self.assertEqual(sorted(e["reason"] for e in out["excluded"]), ["DECISION_MALFORMED", "DECISION_NOT_LEDGERED"])
        self.assertTrue(six(out))

    def test_held_record_requires_grounding(self):
        with self.assertRaises(wi.Refusal) as c:
            amr.admission_outcome_held(admission_receipt_ref=lref(1), evidence_ref="", observed="x", hb_epoch=HB)
        self.assertEqual(c.exception.record["failure_code"], "ADMISSION_OUTCOME_NOT_GROUNDED")


class LearningPathTests(unittest.TestCase):
    def setUp(self):
        self.classes = [json.loads(l) for l in (ROOT / "data/admission-scenarios/classes.jsonl").read_text().splitlines()]
        self.scenarios = [json.loads(l) for l in (ROOT / "data/admission-scenarios/corpus.jsonl").read_text().splitlines()]
        self.kw = dict(known_good=lambda s: bf.known_good(bf.SURFACE_PATH[s]), rule_refs=[bf.REFS["MERGE_AUTHORITY"]],
                       declared_by_session=bf.SESSION, hb_epoch=HB)

    def test_a_counted_miss_is_appended_through_scenario_corpus_append(self):
        out = amr.admission_miss_rate_e0([dec(1, "ALLOW", 1)], [miss(1)])
        n_cls, n_sc = len(self.classes), len(self.scenarios)
        res = amr.learn_from_misses(out["miss_records"], self.classes, self.scenarios, **self.kw)["results"]
        self.assertEqual([r["disposition"] for r in res], ["ALLOW"])
        self.assertEqual(res[0]["transition_class"], "SCENARIO_CORPUS_APPEND")
        self.assertEqual((len(self.classes), len(self.scenarios)), (n_cls + 1, n_sc + 1))
        cls, sc = self.classes[-1], self.scenarios[-1]
        self.assertEqual((cls["class_id"], cls["supersedes"] is not None), ("ASC-MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED@workflow", True))
        self.assertEqual((sc["origin"], sc["source"]["miss_sha256"]), ("ADMISSION_MISS", out["miss_records"][0]["miss_sha256"]))
        schema = json.loads((ROOT / "schemas/admission-corpus.v1.schema.json").read_text())
        self.assertEqual(ss.validate(sc, schema["$defs"]["scenario"]), [])
        self.assertEqual(al.miss_counts(out["miss_records"]), {})
        al.latest_classes(self.classes)

    def test_a_miss_without_bindings_or_surface_fails_closed_and_appends_nothing(self):
        before = (len(self.classes), len(self.scenarios))
        res = amr.learn_from_misses([miss(1, gap="NO_SUCH_PREDICATE"), miss(2, paths=())], self.classes, self.scenarios,
                                    **self.kw)["results"]
        self.assertEqual([r["failure_code"] for r in res], ["PREDICATE_BINDING_UNDECLARED", "ADMISSION_MISS_SURFACE_UNOBSERVED"])
        self.assertTrue(all(six(r) for r in res))
        self.assertEqual((len(self.classes), len(self.scenarios)), before)


class WitnessTests(unittest.TestCase):
    def test_witness_cases_reach_their_terminals(self):
        for cid, inp in CASES.items():
            out = amr.witness_admission_miss_rate(inp)
            self.assertIn(out["disposition"], ("ALLOW", "FAIL_CLOSED"), cid)
            self.assertEqual(out["mode"], "E0")
            if out["disposition"] != "ALLOW":
                self.assertTrue(six(out), cid)

    def test_operating_modes_binds_the_producer_witness(self):
        om = json.loads((ROOT / "data/sv-work-items/operating-modes.json").read_text())
        item = next(i for s in om["stages"] for i in s.get("predicates", []) if i["id"] == "ADMISSION_MISS_RATE")
        self.assertEqual(item["e0_terminal"]["witness"]["entrypoint"], "resident-runtime/admission_miss_rate.py::witness_admission_miss_rate")


if __name__ == "__main__":
    unittest.main()
