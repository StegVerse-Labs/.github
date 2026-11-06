"""STAGE_THRESHOLD_DERIVE (resident-runtime/stage_threshold_derive.py, scripts/derive_stage_thresholds.py): NWI-S2 / NWI-S3
thresholds derived from the S1 corpus's observed baseline by the rule declared in the stage manifests, never by hand."""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
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


td = _load("stage_threshold_derive", "resident-runtime/stage_threshold_derive.py")
runner = _load("derive_stage_thresholds", "scripts/derive_stage_thresholds.py")
wi, sg, amr = td.wi, td.sg, td.amr
HB = "469411750"
VERIFIER = "SV-LLM/.github:sandbox/s1_sv_check_receipts.py#sha256:e91be0adefa69b29c98afeb55c37377833d5c0a601d0f6af06a7e9cd483443cc"


def six(r):
    return r["disposition"] != "ALLOW" and all(isinstance(r.get(k), str) and r[k] for k in td.SIX)


def lref(n):  # an organization-ledger receipt ref (LEDGER_RECEIPT_REF form)
    return "refs/stegverse/organization-ledger@%s:receipts/%064x.json" % ("9" * 40, n)


def synthetic(root: Path, verdicts, outcomes_spec, *, ledgered=True):
    """A snapshot over a vendored corpus written under root: one bundle per verdict (ALLOW or FAIL_CLOSED), each change
    admitted (ALLOW) by a ledgered decision; outcomes_spec: per decision index 'MISS' / 'HELD' / None."""
    vend = "corpus"
    files, decisions, outcomes = [], [], []
    for i, v in enumerate(verdicts):
        head, cd = "%040x" % (i + 1), "sha256:%064x" % (i + 1)
        d = root / vend / ("b%d" % i)
        d.mkdir(parents=True)
        r = {"change_digest": cd, "check_id": "unit-tests", "disposition": v, "hb_epoch": HB, "head_sha": head,
             "schema": "stegverse.sv_check_receipt.v1", "verifier_ref": VERIFIER}
        if v != "ALLOW":
            r.update({k: "x-" + k for k in td.SIX})
        (d / "unit-tests.json").write_text(json.dumps(r))
        b = {"repository": "StegVerse-Labs/.github", "head_sha": head, "change_digest": cd, "disposition": v,
             "authentic_ledger_receipt": ledgered, "ledger_receipt_ref": lref(1000 + i), "receipts": {"unit-tests": wi.sha(r)}}
        (d / "bundle.json").write_text(json.dumps(b))
        for name in ("bundle.json", "unit-tests.json"):
            files.append(td.file_entry("b%d/%s" % (i, name), (d / name).read_bytes()))
        decisions.append({"receipt_ref": lref(i), "disposition": "ALLOW", "ledger_seq": i,
                          "change": {"repository": "StegVerse-Labs/.github", "head_commit": head}})
        spec = outcomes_spec[i] if i < len(outcomes_spec) else None
        if spec == "MISS":
            ch = {"change_id": "svc:%064x" % i, "lifecycle_state": "APPLIED", "head": {"change_digest": cd},
                  "touched_paths": [".github/workflows/x.yml"]}
            outcomes.append(amr.al.admission_miss(ch, admission_receipt_ref=lref(i), correcting_ref=lref(2000 + i),
                                                  miss_kind="REVERT", predicate_gap=None, class_ids=[], hb_epoch=HB))
        elif spec == "HELD":
            outcomes.append(amr.admission_outcome_held(admission_receipt_ref=lref(i), evidence_ref=lref(3000 + i),
                                                       observed="later S1 ALLOW bundle at main", hb_epoch=HB))
    source = {"repository": "SV-LLM/.github", "commit": "a" * 40, "path": "evidence/sv-check-receipts"}
    return {"schema": td.SNAPSHOT_SCHEMA, "s1_corpus": {"source": source, "vendored_dir": vend, "files": files,
                                                       "corpus_digest": td.corpus_digest(source, files)},
            "ledger": {"ref": "refs/stegverse/organization-ledger", "commit": "9" * 40, "hb_epoch": HB},
            "decisions": decisions, "outcomes": outcomes}


class Tmp(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=ROOT / "tests"))
        self.addCleanup(shutil.rmtree, self.root)


class DeclaredRuleTests(unittest.TestCase):
    def test_both_metric_thresholds_declare_the_derivation_rule(self):
        t = {(x["stage_id"], x["predicate"]): x for x in td.targets(sg.load_stages())}
        self.assertEqual(set(t), {("NWI-S2", "SV_LLM_VERDICT_AGREEMENT_RATE"), ("NWI-S3", "ADMISSION_MISS_RATE")})
        for x in t.values():
            d = x["derivation"]
            self.assertEqual(d["transition"], td.TRANSITION)
            self.assertIn(d["formula"], td.FORMULAS)
            self.assertEqual(x["rule_digest"], wi.sha(d))
            self.assertTrue(d["rule"] and d["rule_id"] and d["min_observations"] >= 1)

    def test_transition_is_declared_in_the_lifecycle(self):
        self.assertIn(td.TRANSITION, [t["transition_class"] for t in wi.LIFECYCLE["transitions"]])


class RealS1BaselineTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads(td.SNAPSHOT_FILE.read_text())
        self.out = td.derive(self.snapshot)

    def test_committed_outputs_are_reproducible(self):
        gen = runner.generated()
        for p, text in gen.items():
            self.assertEqual(p.read_text(), text, p)

    def test_the_vendored_corpus_recomputes_its_digest(self):
        s1 = self.snapshot["s1_corpus"]
        self.assertEqual(s1["source"]["commit"], "a00a72ec54055e11b23841e3718cfd7352ad8a8c")
        self.assertEqual(td.corpus_digest(s1["source"], s1["files"]), s1["corpus_digest"])
        self.assertEqual(self.out["corpus_digest"], s1["corpus_digest"])

    def test_insufficient_baseline_fails_closed_with_six_fields_and_writes_nothing(self):
        self.assertTrue(six(self.out))
        self.assertEqual(self.out["failure_code"], "STAGE_THRESHOLD_BASELINE_INSUFFICIENT")
        self.assertEqual({(i["stage_id"], i["reason"]) for i in self.out["insufficient"]},
                         {("NWI-S2", "BASELINE_UNOBSERVED"), ("NWI-S3", "BASELINE_UNOBSERVED")})
        stages = sg.load_stages()
        self.assertEqual(td.apply(stages, self.out, "x"), stages)
        for m in stages:
            for g in m["exit_gate"]:
                if g["evidence"] == "metric":
                    self.assertIsNone(g["threshold"]["value"])

    def test_s1_verifier_receipts_are_not_ledgered_and_disagree_with_admission(self):
        s2 = next(i for i in self.out["insufficient"] if i["stage_id"] == "NWI-S2")["baseline"]
        reasons = {e["reason"] for e in s2["excluded"]}
        self.assertIn("VERIFIER_RECEIPT_NOT_LEDGERED", reasons)
        joined = [j for j in s2["joined"] if j["admission"] is not None]
        self.assertEqual(len(joined), 3)  # Labs #3225 / #3226 / #3234 heads == their ledgered merge receipts' PR heads
        self.assertTrue(all(j["s1_verdict"] == "FAIL_CLOSED" and j["admission"]["disposition"] == "ALLOW"
                            and j["authentic_ledger_receipt"] is False for j in joined))

    def test_gates_at_e0_stay_threshold_undeclared(self):
        ev = {"SV_LLM_VERDICT_AGREEMENT_RATE": {"receipt_ref": lref(1), "agreement_rate": 1.0}}
        self.assertEqual(sg.evaluate_gate("NWI-S2", "NWI-S3", ev, hb_epoch=HB)["failure_code"], "STAGE_THRESHOLD_UNDECLARED")
        self.assertEqual(sg.evaluate_gate("NWI-S2", "NWI-S3", {}, hb_epoch=HB)["failure_code"], "STAGE_EVIDENCE_UNOBSERVED")


class SyntheticBaselineTests(Tmp):
    def test_sufficient_baseline_derives_values_and_a_receipt(self):
        snap = synthetic(self.root, ["ALLOW", "ALLOW", "ALLOW", "FAIL_CLOSED"], ["HELD", "HELD", "HELD", "MISS"])
        out = td.derive(snap, root=self.root)
        self.assertEqual(out["disposition"], "ALLOW", out.get("insufficient"))
        self.assertEqual(out["thresholds"], {"NWI-S2:SV_LLM_VERDICT_AGREEMENT_RATE": 0.75, "NWI-S3:ADMISSION_MISS_RATE": 0.4})
        r = out["receipt"]
        self.assertEqual(r["receipt_sha256"], wi.sha({k: v for k, v in r.items() if k != "receipt_sha256"}))
        self.assertEqual(r["corpus_digest"], snap["s1_corpus"]["corpus_digest"])
        stages = sg.load_stages()
        rules = {(t["stage_id"], t["predicate"]): t for t in td.targets(stages)}
        for t in r["targets"]:
            self.assertEqual(t["rule_digest"], rules[(t["stage_id"], t["predicate"])]["rule_digest"])
            self.assertEqual(t["rule_id"], rules[(t["stage_id"], t["predicate"])]["derivation"]["rule_id"])
            self.assertTrue(t["rule"])
        self.assertEqual(td.derive(snap, root=self.root), out)  # deterministic

    def test_gates_evaluate_against_the_derived_thresholds(self):
        snap = synthetic(self.root, ["ALLOW", "ALLOW", "ALLOW", "FAIL_CLOSED"], ["HELD", "HELD", "HELD", "MISS"])
        out = td.derive(snap, root=self.root)
        stages = td.apply(sg.load_stages(), out, "data/sv-work-items/stage-thresholds/derivation-outcome.json")
        self.assertEqual(td.apply(stages, out, "data/sv-work-items/stage-thresholds/derivation-outcome.json"), stages)
        s2 = next(m for m in stages if m["stage_id"] == "NWI-S2")["exit_gate"][0]["threshold"]
        self.assertEqual((s2["value"], s2["derived_by"]["receipt_sha256"]), (0.75, out["receipt"]["receipt_sha256"]))
        gate = lambda cur, nxt, ev: sg.evaluate_gate(cur, nxt, ev, hb_epoch=HB, stages=stages)
        self.assertEqual(gate("NWI-S2", "NWI-S3", {})["failure_code"], "STAGE_EVIDENCE_UNOBSERVED")
        self.assertEqual(gate("NWI-S2", "NWI-S3", {"SV_LLM_VERDICT_AGREEMENT_RATE": {"receipt_ref": lref(5), "agreement_rate": 0.8}})
                         ["disposition"], "ALLOW")
        self.assertEqual(gate("NWI-S2", "NWI-S3", {"SV_LLM_VERDICT_AGREEMENT_RATE": {"receipt_ref": lref(5), "agreement_rate": 0.5}})
                         ["failure_code"], "STAGE_REGRESSION")
        w05 = {"W05_TV_TVC_HELD_INVOCATION_ADMITTED": {"receipt_ref": lref(6), "disposition": "ALLOW"}}
        self.assertEqual(gate("NWI-S3", "NWI-S4", {**w05, "ADMISSION_MISS_RATE": {"receipt_ref": lref(7), "admission_miss_rate": 0.2}})
                         ["disposition"], "ALLOW")
        self.assertEqual(gate("NWI-S3", "NWI-S4", {**w05, "ADMISSION_MISS_RATE": {"receipt_ref": lref(7), "admission_miss_rate": 0.4}})
                         ["failure_code"], "STAGE_REGRESSION")

    def test_unledgered_s1_receipts_are_unobserved(self):
        out = td.derive(synthetic(self.root, ["ALLOW"] * 4, ["HELD"] * 4, ledgered=False), root=self.root)
        self.assertTrue(six(out))
        self.assertEqual({(i["stage_id"], i["reason"]) for i in out["insufficient"]}, {("NWI-S2", "BASELINE_UNOBSERVED")})
        self.assertEqual(out["computed"][0]["stage_id"], "NWI-S3")  # all-or-nothing: nothing is written

    def test_vacuous_and_undersized_baselines_fail_closed(self):
        out = td.derive(synthetic(self.root, ["FAIL_CLOSED"] * 3, ["HELD", "HELD"]), root=self.root)
        self.assertEqual({(i["stage_id"], i["reason"]) for i in out["insufficient"]},
                         {("NWI-S2", "DERIVED_THRESHOLD_VACUOUS"), ("NWI-S3", "BASELINE_BELOW_MIN_OBSERVATIONS")})
        self.assertTrue(six(out))

    def test_tampered_corpus_and_missing_snapshot_fail_closed(self):
        snap = synthetic(self.root, ["ALLOW"] * 3, ["HELD"] * 3)
        (self.root / "corpus/b0/bundle.json").write_text("{}")
        self.assertEqual(td.derive(snap, root=self.root)["failure_code"], "S1_CORPUS_DIGEST_MISMATCH")
        self.assertEqual(td.derive(None)["failure_code"], "S1_BASELINE_SNAPSHOT_UNOBSERVED")
        bad = copy.deepcopy(snap); bad["ledger"]["hb_epoch"] = None
        self.assertTrue(six(td.derive(bad, root=self.root)))

    def test_an_undeclared_rule_is_never_defaulted(self):
        snap = synthetic(self.root, ["ALLOW"] * 3, ["HELD"] * 3)
        stages = copy.deepcopy(sg.load_stages())
        for m in stages:
            for g in m["exit_gate"]:
                if g["evidence"] == "metric":
                    g["threshold"]["derivation"]["formula"] = "MEAN"
        out = td.derive(snap, stages, root=self.root)
        self.assertEqual({i["reason"] for i in out["insufficient"]}, {"STAGE_THRESHOLD_RULE_UNDECLARED"})


if __name__ == "__main__":
    unittest.main()
