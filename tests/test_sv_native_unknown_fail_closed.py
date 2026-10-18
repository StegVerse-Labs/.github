"""Orchestrator decision UNKNOWN_IN_NATIVE_RECORD (contract invariant: UNKNOWN is FAIL_CLOSED, never DENY): a NATIVE record
field holding UNKNOWN_NOT_AUTHENTICALLY_OBSERVED is FAIL_CLOSED UNKNOWN_IN_NATIVE_RECORD with all six fields; DENY stays
only for values that were observed and are wrong. Pure functions over fixtures; no clock, no network."""
from __future__ import annotations

import json
import unittest

from tests import test_sv_native_work_items as base
from tests import test_sv_round3_invariants as r3

wi, fx, al = base.wi, base.fx, base.al
ROOT, U = base.ROOT, base.wi.UNKNOWN
refusal, six = r3.refusal, r3.six
CID = "ASC-NATIVE_RECORD_FIELDS_ARE_OBSERVED@transition"


def kg():
    return fx.known_good_change(fx.SURFACE_PATH["transition"])


def obs_of(ch):
    return wi.admission_inputs(ch, fx.LABS_BASE, fx.signoff_receipts_for(ch), fx.fixture_base_state_readback(), fx.fixture_resolved_issues(ch))


class ValidateRecordTests(unittest.TestCase):
    def test_change_field_holding_unknown_is_fail_closed_with_six_fields(self):
        for field in ("owning_goal", "declared_session", "hb_epoch"):
            out = refusal(wi.validate_change, base.reseal_change(dict(kg(), **{field: U})))
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                             ("FAIL_CLOSED", "UNKNOWN_IN_NATIVE_RECORD", "NATIVE_RECORD_FIELDS_ARE_OBSERVED"), field)
            self.assertTrue(six(out), field)
            self.assertEqual(out["unknown"], ["/" + field])

    def test_embedded_and_nested_unknown_is_fail_closed(self):
        ch = kg()
        ch = base.reseal_change(dict(ch, required_checks_ref={**ch["required_checks_ref"], "blob_sha": U}))
        self.assertEqual(refusal(wi.validate_change, ch)["disposition"], "FAIL_CLOSED")
        ch = base.reseal_change(dict(kg(), owning_goal="goal " + U))
        out = refusal(wi.validate_change, ch)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "UNKNOWN_IN_NATIVE_RECORD"))

    def test_issue_field_holding_unknown_is_fail_closed(self):
        out = refusal(wi.validate_issue, base.nativize_issue(base.ISSUES[0], owning_goal=U))
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "UNKNOWN_IN_NATIVE_RECORD"))
        self.assertTrue(six(out))

    def test_observed_wrong_values_stay_deny(self):
        n = base.nativize_issue(base.ISSUES[0])
        withprov = dict(n, migration_flags=[])
        out = refusal(wi.validate_issue, withprov)
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "MIGRATION_FIELDS_ON_NATIVE_RECORD"))
        out = refusal(wi.validate_change, dict(kg(), record_mode="NATIVE-ish"))
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "RECORD_MODE_INVALID"))

    def test_writer_evidence_class_enum_is_not_a_sentinel_field(self):
        ch = kg()
        ch["content"] = [{**c, "writer_session": {"session": None, "evidence_class": U}} for c in ch["content"]]
        self.assertEqual(wi.sentinel_pointers(ch), [])


class AdmissionTests(unittest.TestCase):
    def test_known_good_has_no_unknown_pointers(self):
        self.assertEqual(obs_of(kg())["native_unknown_pointers"], [])
        self.assertEqual(wi.admit(obs_of(kg()), fixture_mode=True)["disposition"], "ALLOW")

    def test_admission_of_a_change_holding_unknown_is_fail_closed(self):
        ch = base.reseal_change(dict(kg(), owning_goal=U))
        o = obs_of(ch)
        self.assertEqual(o["native_unknown_pointers"], ["/owning_goal"])
        out = refusal(wi.evaluate_admission, o, fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("FAIL_CLOSED", "UNKNOWN_IN_NATIVE_RECORD", "NATIVE_RECORD_FIELDS_ARE_OBSERVED"))
        self.assertTrue(six(out))
        self.assertEqual(wi.admit(o, fixture_mode=True)["failure_code"], "UNKNOWN_IN_NATIVE_RECORD")

    def test_pointers_not_observed_is_fail_closed(self):
        o = obs_of(kg())
        del o["native_unknown_pointers"]
        out = wi.admit(o, fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "UNKNOWN_IN_NATIVE_RECORD"))

    def test_hb_epoch_keeps_its_own_fail_closed_code_at_admission(self):
        o = obs_of(base.reseal_change(dict(kg(), hb_epoch=U)))
        self.assertEqual(o["native_unknown_pointers"], [])  # /hb_epoch is excluded (ADMISSION_UNKNOWN_EXCLUDED)
        out = wi.admit(o, fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"))

    def test_migrated_record_is_still_historical_first(self):
        o = obs_of(kg())
        o["record_mode"] = "MIGRATED_HISTORICAL"
        o["native_unknown_pointers"] = ["/owning_goal"]
        self.assertEqual(wi.admit(o, fixture_mode=True)["failure_code"], "HISTORICAL_RECORD_NOT_ADMISSIBLE")


class CorpusTests(unittest.TestCase):
    CORPUS = base.jsonl("data/admission-scenarios/corpus.jsonl")
    CLASSES = base.jsonl("data/admission-scenarios/classes.jsonl")

    def test_class_and_scenario_appended_last(self):
        self.assertEqual(self.CLASSES[-1]["class_id"], CID)
        self.assertEqual((self.CLASSES[-1]["class_version"], self.CLASSES[-1]["expected_disposition"], self.CLASSES[-1]["expected_failure_code"]),
                         (1, "FAIL_CLOSED", "UNKNOWN_IN_NATIVE_RECORD"))
        self.assertEqual([s["scenario_id"] for s in self.CORPUS[-2:]], ["PC-transition/" + CID, CID + "/owning_goal[UNKNOWN]"])
        for s in self.CORPUS[-2:]:
            out = wi.admit(s["observed_inputs"], fixture_mode=True)
            self.assertEqual((out["disposition"], out.get("failure_code")), (s["expected_disposition"], s["expected_failure_code"]))
        self.assertEqual(al.disposition_of("UNKNOWN_IN_NATIVE_RECORD"), "FAIL_CLOSED")

    def test_earlier_ids_unchanged(self):
        import subprocess
        old = subprocess.run(["git", "show", "ae8b105d7504565665bf6918367517ffdcb481fd:data/admission-scenarios/corpus.jsonl"],
                             cwd=ROOT, capture_output=True, text=True)
        if old.returncode != 0:
            self.skipTest("ae8b105d not in the local clone")
        prior = [json.loads(l)["scenario_id"] for l in old.stdout.splitlines()]
        self.assertEqual([s["scenario_id"] for s in self.CORPUS[:len(prior)]], prior)

    def test_replay_row(self):
        rows = base.jsonl("data/admission-scenarios/tvc-replay/replay-map.jsonl")
        row = next(r for r in rows if r["scenario_id"] == CID + "/owning_goal[UNKNOWN]")
        self.assertEqual((row["mutation"]["applies_to"], row["mutation"]["pointer"], row["mutation"]["value"]), ("SV_CHANGE", "/owning_goal", U))
        self.assertEqual((row["expected_disposition"], row["expected_failure_code"]), ("FAIL_CLOSED", "UNKNOWN_IN_NATIVE_RECORD"))

    def test_invariant_recorded(self):
        inv = {i["invariant_id"]: i for i in json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())["invariants"]}
        e = inv["NATIVE_RECORD_FIELDS_ARE_OBSERVED"]
        self.assertEqual((e["unobserved"]["disposition"], e["unobserved"]["failure_code"]), ("FAIL_CLOSED", "UNKNOWN_IN_NATIVE_RECORD"))
        self.assertTrue(six(e["unobserved"]))


if __name__ == "__main__":
    unittest.main()
