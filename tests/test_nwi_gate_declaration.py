"""Commit 3: the NWI-S0 exit-gate declaration Lane B (SV-LLM/.github#46) emits from (evidence producers, the stage-evaluation
subject, the epoch source, cadence) and its FAIL_CLOSED validator; the Labs#3266 repin to 2ba0e329; the canonical
not-cross-checked marker; the public resolved-issue facts function; the sv-change hb_epoch schema rule; and the
contract-pins manifest. Pure; no clock, no network."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import unittest

from tests import test_sv_native_work_items as base
from tests import test_sv_stage_gate_issue as sgi
from tests import sv_ledger_fixtures as lf

wi, fx, ss, sg = base.wi, base.fx, base.ss, sgi.sg
ROOT, U = base.ROOT, base.wi.UNKNOWN
MANIFEST_PATH = "data/sv-work-items/stages/NWI-S0.json"
M = json.loads((ROOT / MANIFEST_PATH).read_text())
GOAL163 = "StegVerse-org/.github#163"
LABS = "StegVerse-Labs/.github"
HEAD = fx.LABS_BASE["ledger_head"]
refusal = sgi.refusal


def six(r):
    return all(isinstance(r.get(f), str) and r[f] for f in wi.SIX_FIELDS) and GOAL163 in r["owning_existing_goal"]


def subject(**over):
    s = {"repository": LABS, "stage_id": "NWI-S0", "manifest_blob": "d" * 40, "evaluated_commit": "e" * 40, "base_ref": dict(fx.LABS_BASE)}
    s.update(over)
    return s


def gate_receipt(subj, check_id="nwi-s0-exit-gate", disposition="FAIL_CLOSED", hb="1024"):
    r = {"schema": wi.CHECK_RECEIPT_SCHEMA, "check_id": check_id, "disposition": disposition, "change_digest": wi.stage_evaluation_digest(subj),
         "head_sha": subj["evaluated_commit"], "hb_epoch": hb, "verifier_ref": "SV-LLM/.github#46@9fbc2e92"}
    if disposition != "ALLOW":
        r.update({"failure_code": "STAGE_EVIDENCE_UNOBSERVED", "failed_predicate": "UNKNOWN_NEVER_YIELDS_PASS",
                  "required_evidence_or_repair": "a receipted outcome for every exit predicate",
                  "retry_entrypoint": "resident-runtime/stage_gate.py::evaluate_gate", "owning_existing_goal": GOAL163,
                  "next_attempt": "re-evaluate with the receipts; nothing moved"})
    return r


class GateDeclarationTests(unittest.TestCase):
    def test_nwi_s0_declaration_is_complete(self):
        out = wi.validate_gate_declaration(M)
        self.assertEqual(out["producers"], {"SV_WORK_ITEM_SCHEMAS_VALIDATE": "schema-validate", "EVERY_MIGRATION_FIXTURE_LOADS": "unit-tests"})
        self.assertEqual(sg.gate_check(M)["producers"], out["producers"])
        for p in M["exit_gate_check"]["evidence_producers"]:
            row = wi.REQUIRED_CHECKS["checks"][p["check_id"]]
            self.assertEqual((p["offline_command"], p["command_paths"], p["expected"]), (row["offline_command"], row["command_paths"], row["expected"]))
        self.assertEqual(wi.check_command("nwi-s0-exit-gate", [])["disposition"], "ALLOW")
        self.assertEqual(M["exit_gate_check"]["hb_epoch"]["readback_pin"]["head"], "2ba0e329c224c94863dac15de3f8011f777cb34f")
        self.assertEqual(M["exit_gate_check"]["cadence"]["per"], "STAGE_EVALUATION")
        self.assertIs(M["exit_gate_check"]["cadence"]["in_required_checks_row"], False)

    def test_each_missing_part_is_fail_closed(self):
        for part in ("evidence_producers", "receipt_form", "evaluation_subject", "hb_epoch", "cadence"):
            m = copy.deepcopy(M); del m["exit_gate_check"][part]
            out = refusal(wi.validate_gate_declaration, m)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                             ("FAIL_CLOSED", "STAGE_GATE_DECLARATION_INCOMPLETE", "STAGE_GATE_DECLARATION_IS_COMPLETE"), part)
            self.assertTrue(six(out), part)
            self.assertTrue(any(x.startswith(part) for x in out["missing"]), (part, out["missing"]))
            g = sg.evaluate_gate("NWI-S0", "NWI-S1", {}, hb_epoch="1024", stages=[m] + sg.load_stages()[1:])
            self.assertEqual((g["disposition"], g["failure_code"]), ("FAIL_CLOSED", "STAGE_GATE_DECLARATION_INCOMPLETE"), part)

    def test_drift_unknown_and_wrong_values_are_fail_closed(self):
        cases = {
            "producer argv drifted from the row": lambda c: c["evidence_producers"][0].__setitem__("offline_command", ["python3", "x.py"]),
            "producer paths drifted": lambda c: c["evidence_producers"][1]["command_paths"].pop(),
            "producer check not a row argv check": lambda c: c["evidence_producers"][0].__setitem__("check_id", "supplied-epoch-binder-check"),
            "producer missing for a predicate": lambda c: c["evidence_producers"].pop(),
            "producer not S1": lambda c: c["evidence_producers"][0].__setitem__("producer", "someone else"),
            "UNKNOWN anywhere": lambda c: c["cadence"].__setitem__("trigger", U),
            "per head": lambda c: c["cadence"].__setitem__("not_per_head", False),
            "in the row": lambda c: c["cadence"].__setitem__("in_required_checks_row", True),
            "old readback pin": lambda c: c["hb_epoch"]["readback_pin"].__setitem__("head", "641f4b03e612d07047e15f2384d24780e2af86c0"),
            "subject field missing": lambda c: c["evaluation_subject"]["fields"].pop("base_ref"),
            "receipt binds a change digest": lambda c: c["receipt_form"].__setitem__("change_digest", "head.change_digest"),
            "other ledger": lambda c: c["receipt_form"].__setitem__("ledger", "StegVerse-org/.github"),
        }
        for name, mut in cases.items():
            m = copy.deepcopy(M); mut(m["exit_gate_check"])
            out = refusal(wi.validate_gate_declaration, m)
            self.assertEqual(out["failure_code"], "STAGE_GATE_DECLARATION_INCOMPLETE", name)

    def test_check_command_refuses_an_incomplete_gate(self):
        import unittest.mock as mock
        broken = copy.deepcopy(M); del broken["exit_gate_check"]["cadence"]
        real = wi.json.loads
        with mock.patch.object(wi.json, "loads", side_effect=lambda t, *a, **k: broken if isinstance(t, str) and '"stage_id": "NWI-S0"' in t else real(t, *a, **k)):
            out = refusal(wi.check_command, "nwi-s0-exit-gate", [])
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "STAGE_GATE_DECLARATION_INCOMPLETE"))

    def test_manifest_without_gate_check_is_not_a_gate_stage(self):
        self.assertIsNone(wi.validate_gate_declaration({k: v for k, v in M.items() if k != "exit_gate_check"}))


class StageEvaluationSubjectTests(unittest.TestCase):
    def test_digest_is_canonical_and_known(self):
        s = subject()
        canon = json.dumps(s, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        self.assertEqual(wi.stage_evaluation_digest(s), "sha256:" + hashlib.sha256(canon).hexdigest())
        self.assertEqual(wi.stage_evaluation_digest(dict(reversed(list(s.items())))), wi.stage_evaluation_digest(s))
        for k, v in (("evaluated_commit", "f" * 40), ("manifest_blob", "c" * 40), ("base_ref", {**fx.LABS_BASE, "registry_generation": 320})):
            self.assertNotEqual(wi.stage_evaluation_digest(subject(**{k: v})), wi.stage_evaluation_digest(s), k)

    def test_unobserved_subject_is_fail_closed(self):
        for k, v in (("evaluated_commit", U), ("manifest_blob", None), ("base_ref", {"ledger_head": HEAD}), ("stage_id", "S0"), ("repository", "")):
            out = refusal(wi.stage_evaluation_digest, subject(**{k: v}))
            self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "STAGE_EVALUATION_SUBJECT_UNOBSERVED"), k)
            self.assertTrue(six(out))
        self.assertEqual(refusal(wi.stage_evaluation_digest, {**subject(), "extra": 1})["failure_code"], "STAGE_EVALUATION_SUBJECT_UNOBSERVED")

    def test_gate_receipt_validates_against_the_unchanged_schema(self):
        schema = json.loads((ROOT / "schemas/sv-check-receipt.v1.schema.json").read_text())
        for cid, disp in (("nwi-s0-exit-gate", "FAIL_CLOSED"), ("nwi-s0-exit-gate", "ALLOW"), ("schema-validate", "ALLOW"), ("unit-tests", "DENY")):
            r = gate_receipt(subject(), cid, disp)
            self.assertEqual(ss.validate(r, schema), [], cid)
            out = wi.validate_gate_receipt(r, subject(), fx.fixture_base_state_readback(), fixture_mode=True)
            self.assertEqual((out["disposition"], out["evaluation_subject_digest"]), ("ALLOW", wi.stage_evaluation_digest(subject())))

    def test_gate_receipt_binding_failures(self):
        rb = fx.fixture_base_state_readback()
        r = dict(gate_receipt(subject()), change_digest="sha256:" + "a" * 64)
        self.assertEqual(refusal(wi.validate_gate_receipt, r, subject(), rb, fixture_mode=True)["failed_predicate"], "STAGE_EVALUATION_SUBJECT_BINDS_RECEIPT")
        r = dict(gate_receipt(subject()), head_sha="f" * 40)
        self.assertEqual(refusal(wi.validate_gate_receipt, r, subject(), rb, fixture_mode=True)["failure_code"], "CHECK_SKIPPED_OR_UNOBSERVED")
        out = refusal(wi.validate_gate_receipt, gate_receipt(subject(), hb="1025"), subject(), rb, fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "HB_EPOCH_MISMATCH"))
        out = refusal(wi.validate_gate_receipt, gate_receipt(subject()), subject(), None, fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"))
        other = subject(repository="StegVerse-org/.github")
        out = refusal(wi.validate_gate_receipt, gate_receipt(other), other, rb, fixture_mode=True)  # per-repo ledger binding
        self.assertEqual(out["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")
        out = refusal(wi.validate_gate_receipt, gate_receipt(subject(), "supplied-epoch-binder-check", "ALLOW"), subject(), rb, fixture_mode=True)
        self.assertEqual(out["failure_code"], "CHECK_NOT_PART_OF_STAGE_EVALUATION")

    def test_evaluate_gate_carries_the_subject(self):
        g = sg.evaluate_gate("NWI-S0", "NWI-S1", {}, hb_epoch="1024", subject=subject())
        self.assertEqual(g["evaluation_subject_digest"], wi.stage_evaluation_digest(subject()))
        self.assertEqual(g["evaluation_subject"], subject())
        self.assertEqual(g["failure_code"], "STAGE_EVIDENCE_UNOBSERVED")
        req = sg.transition_request(g)
        self.assertEqual(req["build_manifest"]["data"]["stage_gate_outcome"]["evaluation_subject_digest"], g["evaluation_subject_digest"])
        g = sg.evaluate_gate("NWI-S0", "NWI-S1", {}, hb_epoch="1024", subject=subject(stage_id="NWI-S1"))
        self.assertEqual(g["failure_code"], "STAGE_EVALUATION_SUBJECT_MISMATCH")

    def test_one_failing_receipt_derives_one_issue(self):
        objs, ref, org, repo = sgi.ledgered(gate_receipt(subject()), commit=HEAD)
        issue = wi.derive_issue_from_check_receipt(objs, ref, observed_base=subject()["base_ref"])
        again = wi.derive_issue_from_check_receipt(objs, ref, observed_base=subject()["base_ref"])
        self.assertEqual(issue["issue_id"], again["issue_id"])
        self.assertEqual(issue["surface"]["path"], MANIFEST_PATH)
        self.assertEqual(issue["violated_invariant"]["rule_id"], "NWI-S0#exit_gate_check.nwi-s0-exit-gate")


class ReadbackRepinTests(unittest.TestCase):
    def test_pin_is_2ba0e329(self):
        self.assertEqual((wi.BASE_STATE_READBACK_PIN["head"], wi.BASE_STATE_READBACK_PIN["blob"], wi.BASE_STATE_READBACK_PIN["sha256"],
                          wi.BASE_STATE_READBACK_PIN["tests_blob"]),
                         ("2ba0e329c224c94863dac15de3f8011f777cb34f", "2c730142254b78a5b9e1c05566fe6f5111b7d571",
                          "88d3b72b3915c71b191b71a0dd7c607dfc675f0490acfe87ec92f808f17eaefe", "31550f4d54555df4683b37401da39067b71cee60"))
        inv = {i["invariant_id"]: i for i in json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())["invariants"]}
        self.assertEqual(inv["ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH"]["readback_pin"], wi.BASE_STATE_READBACK_PIN)

    def test_pinned_blob_when_present(self):
        out = subprocess.run(["git", "rev-parse", "2ba0e329c224c94863dac15de3f8011f777cb34f:resident-runtime/sv_change_base_state_readback.py"],
                             cwd=ROOT, capture_output=True, text=True)
        if out.returncode != 0:
            self.skipTest("2ba0e329 not in the local clone")
        self.assertEqual(out.stdout.strip(), wi.BASE_STATE_READBACK_PIN["blob"])

    def test_omitted_flag_allow_shape_of_2ba0e329_is_observed(self):
        """2ba0e329 adds cross_checked false and hb_epoch_cross_check to an omitted-flag ALLOW; still an observed epoch."""
        rb = fx.fixture_base_state_readback()
        body = {k: v for k, v in rb.items() if k != "result_sha256"}
        body.update({"cross_checked": False, "hb_epoch_cross_check": "HB_EPOCH_NOT_CROSS_CHECKED"})
        rb = wi.seal(body, "result_sha256")
        self.assertEqual(wi.verify_admission_hb_epoch("1024", rb, HEAD, fixture_mode=True)["disposition"], "ALLOW")
        # explicit '' / 'null' / sentinel at the producer: FAIL_CLOSED, both slots null -> unobserved here
        body = {k: v for k, v in fx.fixture_base_state_readback().items() if k != "result_sha256"}
        body.update({"disposition": "FAIL_CLOSED", "failure_code": "HB_EPOCH_SOURCE_UNOBSERVED", "hb_epoch": None, "hb_epoch_source": None})
        out = refusal(wi.verify_admission_hb_epoch, "1024", wi.seal(body, "result_sha256"), HEAD, fixture_mode=True)
        self.assertEqual(out["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")


class MarkerTests(unittest.TestCase):
    def test_canonical_marker(self):
        out = wi.verify_admission_hb_epoch(wi.HB_EPOCH_NOT_CROSS_CHECKED, fx.fixture_base_state_readback(), HEAD, fixture_mode=True)
        self.assertEqual((out["cross_checked"], out["detail"]), (False, "HB_EPOCH_NOT_CROSS_CHECKED"))
        self.assertNotIn("hb_epoch_cross_check", out)
        inv = {i["invariant_id"]: i for i in json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())["invariants"]}
        self.assertEqual(inv["NOT_CROSS_CHECKED_MARKER"]["canonical"], {"cross_checked": False, "detail": "HB_EPOCH_NOT_CROSS_CHECKED"})


class ResolvedIssueFactsTests(unittest.TestCase):
    def setUp(self):
        self.objs, self.ref, _, _ = sgi.ledgered(gate_receipt(subject()), commit=HEAD)
        self.issue = wi.derive_issue_from_check_receipt(self.objs, self.ref, observed_base=fx.LABS_BASE)
        self.ch = sgi.resolving_change([self.issue["issue_id"]])
        self.at = "refs/stegverse/organization-ledger@" + HEAD

    def test_pure_and_rederivable(self):
        a = wi.derive_resolved_issue_facts(self.objs, self.at, self.ch, [self.issue])
        b = wi.derive_resolved_issue_facts(dict(self.objs), self.at, copy.deepcopy(self.ch), [copy.deepcopy(self.issue)])
        self.assertEqual(a, b)
        self.assertEqual(a, wi.resolved_issue_facts([self.issue], self.objs))
        self.assertEqual(a[0]["issue_id"], self.issue["issue_id"])
        self.assertIs(a[0]["fixture_only"], False)

    def test_admission_uses_the_same_function(self):
        obs = wi.admission_inputs(self.ch, fx.LABS_BASE, fx.signoff_receipts_for(self.ch), fx.fixture_base_state_readback(),
                                  ledger_objects=self.objs, ledger_ref=self.at, issue_records=[self.issue])
        self.assertEqual(obs["resolved_issues"], wi.derive_resolved_issue_facts(self.objs, self.at, self.ch, [self.issue]))
        self.assertEqual(wi.verify_resolutions(obs)["resolved"], [self.issue["issue_id"]])  # observed, not fixture: counts outside fixture_mode
        out = refusal(wi.admission_inputs, self.ch, fx.LABS_BASE, (), None, [], ledger_objects=self.objs, ledger_ref=self.at)
        self.assertEqual(out["failure_code"], "RESOLVED_ISSUE_FACTS_DOUBLY_SOURCED")
        ctx = {"current_base": fx.LABS_BASE, "ledger_objects": self.objs, "ledger_ref": self.at, "issue_records": [self.issue],
               "predicate_digest": "sha256:" + "c" * 64, "corpus_head": "sha256:" + "d" * 64,
               "evaluator": lambda o, **k: {"disposition": "ALLOW", "failed_predicate": None, "facts": o["resolved_issues"]}}
        tr = wi.transition("SV_CHANGE_ADMIT", self.ch, hb_epoch="1024", context=ctx)
        self.assertEqual(tr["disposition"], "ALLOW")

    def test_unledgered_or_off_base_receipt_yields_no_fact(self):
        objs, ref, _, _ = sgi.ledgered(gate_receipt(subject()), commit="c" * 40)  # ledgered, but not at the change's base head
        issue = wi.derive_issue_from_check_receipt(objs, ref, observed_base=fx.LABS_BASE)
        ch = sgi.resolving_change([issue["issue_id"]])
        self.assertEqual(wi.derive_resolved_issue_facts(objs, self.at, ch, [issue]), [])
        obs = wi.admission_inputs(ch, fx.LABS_BASE, (), None, ledger_objects=objs, ledger_ref=self.at, issue_records=[issue])
        self.assertEqual(refusal(wi.verify_resolutions, obs)["failure_code"], "SV_CHANGE_RESOLVES_NOTHING")
        self.assertEqual(wi.derive_resolved_issue_facts({}, self.at, self.ch, [self.issue]), [])  # no bytes: unobserved
        self.assertEqual(wi.derive_resolved_issue_facts(self.objs, self.at, self.ch, []), [])  # no record: unobserved

    def test_ledger_ref_must_be_the_change_base(self):
        for ref in ("refs/stegverse/organization-ledger@" + "c" * 40, "refs/heads/main@" + HEAD, None):
            out = refusal(wi.derive_resolved_issue_facts, self.objs, ref, self.ch, [self.issue])
            self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "RESOLVED_ISSUE_LEDGER_NOT_CHANGE_BASE"), ref)
            self.assertTrue(six(out))

    def test_collision_counted_from_the_issue_pool(self):
        other = dict(self.issue, issue_id="svi:" + "e" * 64)
        f = wi.derive_resolved_issue_facts(self.objs, self.at, self.ch, [self.issue, other])
        self.assertEqual(f[0]["derived_issue_ids_from_receipt"], sorted([self.issue["issue_id"], other["issue_id"]]))


class SvChangeSchemaEpochTests(unittest.TestCase):
    S = json.loads((ROOT / "schemas/sv-change.v1.schema.json").read_text())

    def test_schema_matches_726248a5_for_strings(self):
        kg = fx.known_good_change(fx.SURFACE_PATH["transition"])
        for v in ("32", "1024", "01024", "469411750", "31", "0031", "00", "abc", "", "+33", " 1024"):
            schema_ok = ss.validate(dict(kg, hb_epoch=v), self.S) == []
            self.assertEqual(schema_ok, wi.kernel.supplied_epoch_failure(v) is None, v)

    def test_unobserved_values_stay_schema_invalid_but_fail_closed(self):
        kg = fx.known_good_change(fx.SURFACE_PATH["transition"])
        for v in (None, "", "null", U, "DROP"):
            ch = {k: x for k, x in kg.items() if k != "hb_epoch"} if v == "DROP" else dict(kg, hb_epoch=v)
            self.assertTrue(ss.validate(ch, self.S), v)
            out = refusal(wi.validate_change, base.reseal_change(ch))
            self.assertEqual(out["disposition"], "FAIL_CLOSED", v)

    def test_migrated_sentinel_still_allowed(self):
        self.assertEqual(sum(len(ss.validate(c, self.S)) for c in base.CHANGES), 0)


class ContractPinsTests(unittest.TestCase):
    P = json.loads((ROOT / "data/sv-work-items/contract-pins.json").read_text())

    def test_manifest_matches_the_tree(self):
        self.assertEqual(sorted(self.P["files"]), fx.CONTRACT_FILES)
        for rel, pin in self.P["files"].items():
            data = (ROOT / rel).read_bytes()
            self.assertEqual(pin["sha256"], "sha256:" + hashlib.sha256(data).hexdigest(), rel)
            self.assertEqual(pin["blob"], hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest(), rel)
        self.assertEqual((ROOT / "data/sv-work-items/contract-pins.json").read_text(), fx.build()[fx.CONTRACT_PINS])

    def test_never_lists_itself_and_covers_the_contract(self):
        self.assertNotIn("data/sv-work-items/contract-pins.json", self.P["files"])
        for rel in ("schemas/sv-change.v1.schema.json", "schemas/sv-issue.v1.schema.json", "schemas/sv-check-receipt.v1.schema.json",
                    "data/sv-work-items/invariants.json", "data/sv-work-items/required-checks.json", "resident-runtime/sv_work_items.py",
                    "data/admission-scenarios/classes.jsonl", "data/admission-scenarios/corpus.jsonl", MANIFEST_PATH):
            self.assertIn(rel, self.P["files"])
        self.assertTrue(all(p.startswith("schemas/sv-") or p.startswith("schemas/") for p in self.P["files"] if p.startswith("schemas/")))

    def test_stale_manifest_is_flagged(self):
        out = fx.build()
        out[fx.CONTRACT_PINS] = out[fx.CONTRACT_PINS].replace(self.P["files"]["resident-runtime/sv_work_items.py"]["sha256"], "sha256:" + "0" * 64)
        self.assertNotEqual(out[fx.CONTRACT_PINS], (ROOT / "data/sv-work-items/contract-pins.json").read_text())
        inv = {i["invariant_id"]: i for i in json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())["invariants"]}
        self.assertIn("never lists itself", inv["CONTRACT_PINS_MANIFEST_IS_THE_CONSUMER_PIN"]["statement"])


class SchemaValidateProducerTests(unittest.TestCase):
    def test_build_check_validates_the_schemas(self):
        out = fx.build()
        self.assertEqual(fx.schema_errors(out), [])
        bad = dict(out)
        line = json.loads(out[fx.MIG / "sv-changes.jsonl"].splitlines()[0]); line["hb_epoch"] = "31"
        bad[fx.MIG / "sv-changes.jsonl"] = json.dumps(line) + "\n"
        self.assertEqual(fx.schema_errors(bad)[0]["schema"], "schemas/sv-change.v1.schema.json")


if __name__ == "__main__":
    unittest.main()
