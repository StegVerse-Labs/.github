"""Round 5: ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH (JD-P4-3, part-decided by invariant), HB_EPOCH_MISMATCH, the
supplied-epoch-binder-check as a verifier built-in, and the 726248a5 pin. Pure; no clock, no network."""
from __future__ import annotations

import hashlib
import json
import unittest

from tests import test_sv_native_work_items as base

wi, fx, al = base.wi, base.fx, base.al
ROOT, U = base.ROOT, base.wi.UNKNOWN
GOAL163 = "StegVerse-org/.github#163"
INV = "ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH"
CID = "ASC-" + INV + "@ledger_writer"
PIN = "726248a585904b52cfe2eec1754e7ce582f67d6b501bd664bb7bee80bce9b7ef"
HEAD = fx.LABS_BASE["ledger_head"]


def refusal(fn, *a, **k):
    try:
        return fn(*a, **k)
    except wi.Refusal as r:
        return r.record


def six(rec):
    return all(isinstance(rec.get(f), str) and rec[f] for f in wi.SIX_FIELDS) and GOAL163 in rec["owning_existing_goal"]


def reseal(rb, **change):
    body = {k: v for k, v in rb.items() if k != "result_sha256"}
    body.update(change)
    return wi.seal(body, "result_sha256")


def lane_c_refusal(why):
    """The FAIL_CLOSED receipt Lane C's readback emits when the head receipt's epoch is invalid (Labs#3266 @641f4b03,
    sv_change_base_state_readback.py blob fbd453e5: _refuse(base, 'HB_EPOCH_SOURCE_UNOBSERVED', ...)): hb_epoch and
    hb_epoch_source are both present and null on every FAIL_CLOSED."""
    rb = fx.fixture_base_state_readback()
    body = {k: v for k, v in rb.items() if k != "result_sha256"}
    body.update({"hb_epoch": None, "hb_epoch_source": None, "disposition": "FAIL_CLOSED", "failure_code": "HB_EPOCH_SOURCE_UNOBSERVED",
                 "failed_predicate": INV,
                 "required_evidence_or_repair": "the org-ledger head receipt at " + HEAD + " carries a valid $.hb_reference.epoch (" + why + ")",
                 "retry_entrypoint": "resident-runtime/sv_change_base_state_readback.py::evaluate", "owning_existing_goal": "StegVerse-org/.github#164",
                 "next_attempt": "after the org writer appends a head receipt carrying a supplied epoch; no epoch is minted here"})
    return wi.seal(body, "result_sha256")


def lane_c_mismatch(expected, observed="1024"):
    """Lane C's DENY HB_EPOCH_MISMATCH (a contradicting --hb-epoch): the epoch and its source are still sealed."""
    rb = fx.fixture_base_state_readback(hb_epoch=observed)
    body = {k: v for k, v in rb.items() if k != "result_sha256"}
    body.update({"disposition": "DENY", "failure_code": "HB_EPOCH_MISMATCH", "failed_predicate": INV, "expected_hb_epoch": expected,
                 "flag_failure_code": "HB_EPOCH_FLAG_MISMATCH"})
    return wi.seal(body, "result_sha256")


class PredicateTests(unittest.TestCase):
    RB = fx.fixture_base_state_readback()

    def verify(self, supplied="1024", rb="fixture", head=HEAD, fixture_mode=True):
        return refusal(wi.verify_admission_hb_epoch, supplied, self.RB if rb == "fixture" else rb, head, fixture_mode=fixture_mode)

    def test_equal_epoch_allows(self):
        out = self.verify()
        self.assertEqual((out["disposition"], out["hb_epoch"], out["ledger_head"]), ("ALLOW", "1024", HEAD))
        self.assertEqual(self.verify("01024")["disposition"], "ALLOW")  # integer value
        self.assertEqual(self.verify("2048", reseal(self.RB, hb_epoch=2048))["disposition"], "ALLOW")  # an int slot passes 726248a5

    def test_unobserved(self):
        rb = self.RB
        src = rb["hb_epoch_source"]
        cases = {
            "absent": None, "not an object": [], "wrong schema": reseal(rb, schema="stegverse.other/v1"),
            "broken seal": {**rb, "result_sha256": "sha256:" + "0" * 64}, "no seal": {k: v for k, v in rb.items() if k != "result_sha256"},
            "tampered body": {**rb, "hb_epoch": "2048"},
            "not ALLOW (Lane C refusal, clock)": lane_c_refusal("HB_EPOCH_INVALID: the carrier's derived_from_clock is not exactly false"),
            "not ALLOW (Lane C refusal, non-int)": lane_c_refusal("hb_reference.epoch is not an int"),
            "other head": reseal(rb, base_ref={**rb["base_ref"], "ledger_head": "f" * 40}),
            "source other head": reseal(rb, hb_epoch_source={**src, "ledger_head": "f" * 40}),
            "source other field": reseal(rb, hb_epoch_source={**src, "field": "$.hb_epoch"}),
            "no source": reseal(rb, hb_epoch_source=None),
            "Lane C FAIL_CLOSED (both null)": reseal(rb, disposition="FAIL_CLOSED", failure_code="BASE_STATE_NOT_OBSERVED",
                                                     hb_epoch=None, hb_epoch_source=None),
            "FAIL_CLOSED carrying an epoch anyway": reseal(rb, disposition="FAIL_CLOSED", failure_code="BASE_STATE_NOT_OBSERVED"),
            "DENY other than HB_EPOCH_MISMATCH": reseal(rb, disposition="DENY", failure_code="BASE_STALE"),
            "old source key receipt_sha256": reseal(rb, hb_epoch_source={"ledger_head": HEAD, "field": src["field"],
                                                                         "receipt_sha256": "sha256:" + "3" * 64}),
            "receipt not the ledger path": reseal(rb, hb_epoch_source={**src, "receipt": "sha256:" + "3" * 64}),
            "receipt under source-receipts/": reseal(rb, hb_epoch_source={**src, "receipt": "source-receipts/" + "3" * 64 + ".json"}),
            "slot null": reseal(rb, hb_epoch=None), "slot float": reseal(rb, hb_epoch=1024.0), "slot bool": reseal(rb, hb_epoch=True),
            "slot coerced": reseal(rb, hb_epoch=" 1024"), "slot below anchor": reseal(rb, hb_epoch="31"),
            "derived_from_clock": reseal(rb, hb_epoch_source={**src, "derived_from_clock": True}),
            "derived_from_clock not exactly false": reseal(rb, hb_epoch_source={**src, "derived_from_clock": 0}),
        }
        for name, r in cases.items():
            out = self.verify(rb=r)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                             ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED", INV), name)
            self.assertTrue(six(out), name)
            self.assertEqual(out["retry_entrypoint"], "resident-runtime/sv_work_items.py::verify_admission_hb_epoch")
        self.assertEqual(self.verify(head="x")["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")

    def test_fixture_readback_counts_only_in_fixture_mode(self):
        self.assertEqual(self.verify(fixture_mode=False)["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")
        real = reseal(self.RB, fixture_only=False, hb_epoch_source={**self.RB["hb_epoch_source"], "receipt": "receipts/" + "3" * 64 + ".json"})
        self.assertEqual(self.verify(rb=real, fixture_mode=False)["disposition"], "ALLOW")

    def test_lane_c_producer_semantics(self):
        """Labs#3266 @641f4b03: sealed on ALLOW and on DENY HB_EPOCH_MISMATCH; null on FAIL_CLOSED; receipt is a ledger path."""
        self.assertEqual(set(self.RB["hb_epoch_source"]), {"ledger_head", "receipt", "field"})
        self.assertEqual(self.verify("1024", lane_c_mismatch("1025"))["disposition"], "ALLOW")  # the epoch was observed
        out = self.verify("1025", lane_c_mismatch("1025"))
        self.assertEqual((out["disposition"], out["failure_code"], out["expected"]), ("DENY", "HB_EPOCH_MISMATCH", "1024"))
        real = reseal(self.RB, fixture_only=False, hb_epoch_source={**self.RB["hb_epoch_source"], "receipt": "receipts/" + "3" * 64 + ".json"})
        self.assertEqual(self.verify(rb=real, fixture_mode=False)["disposition"], "ALLOW")
        out = self.verify(rb=reseal(self.RB, fixture_only=False), fixture_mode=False)  # UNKNOWN receipt outside a fixture
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"))
        rc = lane_c_refusal("HB_EPOCH_INVALID")
        self.assertIn("hb_epoch_source", rc)
        self.assertIsNone(rc["hb_epoch_source"])
        self.assertIsNone(rc["hb_epoch"])

    def test_readback_pin(self):
        self.assertEqual(wi.BASE_STATE_READBACK_PIN["blob"], "fbd453e531fc8d8f62261d2a72bc7a596798a445")
        entry = next(i for i in json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())["invariants"] if i["invariant_id"] == INV)
        self.assertEqual(entry["readback_pin"], wi.BASE_STATE_READBACK_PIN)

    def test_mismatch_is_deny(self):
        for supplied in ("1025", "32", "1024x", " 1024", 1024):
            out = self.verify(supplied)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]), ("DENY", "HB_EPOCH_MISMATCH", INV), supplied)
            self.assertTrue(six(out))
            self.assertEqual(out["expected"], "1024")

    def test_unknown_supplied_epoch_is_fail_closed_never_deny(self):
        """Contract invariant (narrowed): where the supplied value is the epoch source, absent, JSON null, "", "null" and the
        UNKNOWN sentinel are FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED, before 726248a5; an optional cross-check left out proceeds
        on the sealed epoch; malformed values are DENY HB_EPOCH_MISMATCH, and so is a well-formed mismatch."""
        for name, supplied in (("JSON null", None), ("empty string", ""), ("string null", "null"), ("sentinel", U)):
            out = self.verify(supplied)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                             ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED", INV), name)
            self.assertTrue(six(out))
            self.assertNotIn("supplied_epoch_rule", out)
        # an optional cross-check left out is not a failure: nothing to compare, the sealed epoch stands
        out = self.verify(wi.HB_EPOCH_NOT_CROSS_CHECKED)
        self.assertEqual((out["disposition"], out["hb_epoch"], out["cross_checked"]), ("ALLOW", "1024", False))
        out = self.verify(wi.HB_EPOCH_NOT_CROSS_CHECKED, rb=None)  # ...but the sealed source must still be observed
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"))
        # the sentinel's case variants, "NULL" and whitespace are not the sentinel: malformed -> DENY
        for supplied in ("unknown_not_authentically_observed", "NULL", " ", "None"):
            self.assertEqual(self.verify(supplied)["failure_code"], "HB_EPOCH_MISMATCH", supplied)
        # absent: a change with no hb_epoch (the record field is the epoch source) reaches admission as supplied_hb_epoch None
        ch = fx.known_good_change(fx.SURFACE_PATH["ledger_writer"])
        ch = base.reseal_change({k: v for k, v in ch.items() if k != "hb_epoch"})
        obs = wi.admission_inputs(ch, fx.LABS_BASE, fx.signoff_receipts_for(ch), fx.fixture_base_state_readback(), fx.fixture_resolved_issues(ch))
        self.assertIsNone(obs["supplied_hb_epoch"])
        out = wi.admit(obs, fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"))
        # the divergence from the kernel function is deliberate and recorded (precedence), the pin unchanged
        self.assertEqual(wi.kernel.supplied_epoch_failure(None)[0], "HB_EPOCH_NOT_SUPPLIED")
        for v in (U, "", "null"):
            self.assertEqual(wi.kernel.supplied_epoch_failure(v)[0], "HB_EPOCH_INVALID", v)
        self.assertEqual(wi.KERNEL_RULE_SHA256, PIN)
        pin = wi.REQUIRED_CHECKS["checks"]["supplied-epoch-binder-check"]["predicate_pins"]["726248a5"]
        self.assertEqual(pin["sha256"], PIN)
        self.assertIn("FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED", pin["precedence"])
        entry = next(i for i in json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())["invariants"] if i["invariant_id"] == INV)
        self.assertEqual(entry["supplied_epoch_rule"]["precedence"], pin["precedence"])
        self.assertIn("never DENY", entry["supplied_epoch_ruling"]["statement"])
        # malformed -> DENY; well-formed mismatch -> DENY
        for supplied in ("abc", "31", True):
            self.assertEqual(self.verify(supplied)["failure_code"], "HB_EPOCH_MISMATCH", supplied)
        self.assertEqual((self.verify("1025")["disposition"], self.verify("1025")["failure_code"]), ("DENY", "HB_EPOCH_MISMATCH"))
        # with an unobserved sealed source the outcome is FAIL_CLOSED whatever is supplied
        for supplied in (None, "", "null", U, "abc", "1025"):
            self.assertEqual(self.verify(supplied, rb=None)["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")

    def test_supplied_epoch_failing_726248a5_is_deny_mismatch(self):
        """Orchestrator ruling: the supplied side is DENY HB_EPOCH_MISMATCH; only the sealed side is FAIL_CLOSED."""
        for supplied in ("abc", "+33", "31", "0031", "1024.0", " 1024", 1024, True, False, "unknown_not_authentically_observed"):
            if supplied != 1024 or supplied is True:  # an int 1024 passes 726248a5 but is not ASCII text, so it is still refused
                self.assertIsNotNone(wi.kernel.supplied_epoch_failure(supplied), supplied)
            out = self.verify(supplied)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]), ("DENY", "HB_EPOCH_MISMATCH", INV), supplied)
            self.assertTrue(six(out))
        self.assertIn("HB_EPOCH_INVALID", self.verify("+33")["supplied_epoch_rule"])
        self.assertIn("below the HB32 anchor", self.verify("31")["supplied_epoch_rule"])
        # a sealed epoch of 33 does not rescue a coerced '+33'
        self.assertEqual(self.verify("+33", reseal(self.RB, hb_epoch="33"))["failure_code"], "HB_EPOCH_MISMATCH")
        self.assertEqual(self.verify("33", reseal(self.RB, hb_epoch="33"))["disposition"], "ALLOW")
        # leading zeros: 726248a5 accepts them, so equality is by integer value
        self.assertIsNone(wi.kernel.supplied_epoch_failure("01024"))
        self.assertEqual(self.verify("01024")["disposition"], "ALLOW")
        self.assertEqual(self.verify("00033", reseal(self.RB, hb_epoch="33"))["disposition"], "ALLOW")
        # with an unobserved source the supplied value is never reached
        for supplied in ("+33", "31", "1024"):
            self.assertEqual(self.verify(supplied, rb=None)["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")
        inv = json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())
        ruling = {i["invariant_id"]: i for i in inv["invariants"]}[INV]["supplied_epoch_ruling"]
        self.assertIn("DENY HB_EPOCH_MISMATCH", ruling["statement"])

    def test_rule_pin_resolves_and_is_enforced(self):
        src = (ROOT / "org-kernel/kernel.py").read_text(encoding="utf-8")
        self.assertEqual(wi.supplied_epoch_rule_sha256(src), PIN)
        self.assertEqual(wi.KERNEL_RULE_SHA256, PIN)
        self.assertEqual(wi.SUPPLIED_EPOCH_RULE_SHA256, PIN)
        lines = src.splitlines()
        self.assertTrue(lines[235].startswith("def supplied_epoch_failure"))  # org-kernel/kernel.py:236
        self.assertEqual((lines[268].strip(), lines[269], lines[270][:4]), ("return None", "", "def "))  # segment = :236-269
        tampered = src.replace('"HB_EPOCH_INVALID", "hb_epoch "', '"HB_EPOCH_INVALID", "epoch "', 1)
        self.assertNotEqual(wi.supplied_epoch_rule_sha256(tampered), PIN)
        old = wi.KERNEL_RULE_SHA256
        try:
            wi.KERNEL_RULE_SHA256 = wi.supplied_epoch_rule_sha256(tampered)
            self.assertEqual(self.verify()["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")
        finally:
            wi.KERNEL_RULE_SHA256 = old
        row = json.loads((ROOT / "data/sv-work-items/required-checks.json").read_text())
        pin = row["checks"]["supplied-epoch-binder-check"]["predicate_pins"]["726248a5"]
        self.assertEqual((pin["sha256"], pin["path"], pin["function"]), (PIN, "org-kernel/kernel.py", "supplied_epoch_failure"))
        blob = hashlib.sha1(b"blob %d\0" % len(src.encode()) + src.encode()).hexdigest()
        self.assertEqual(pin["file_blob_at_fc19b532"], blob)  # kernel.py unchanged since fc19b532


class AdmissionTests(unittest.TestCase):
    def obs(self, path=fx.SURFACE_PATH["ledger_writer"], rb="fixture", hb="1024"):
        ch = fx.known_good_change(path)
        if hb != "1024":
            ch = base.reseal_change(dict(ch, hb_epoch=hb))
        return wi.admission_inputs(ch, fx.LABS_BASE, fx.signoff_receipts_for(ch), fx.fixture_base_state_readback() if rb == "fixture" else rb,
                                   fx.fixture_resolved_issues(ch))

    def test_ledger_writer_admission_binds_the_readback_epoch(self):
        self.assertEqual(wi.admit(self.obs(), fixture_mode=True)["disposition"], "ALLOW")
        out = wi.admit(self.obs(rb=None), fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"))
        out = wi.admit(self.obs(hb="2048"), fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "HB_EPOCH_MISMATCH"))
        # outside fixture_mode the fixture receipts never count (the checks fail first)
        self.assertNotEqual(wi.admit(self.obs())["disposition"], "ALLOW")

    def test_every_admission_binds_the_readback_epoch(self):
        row = json.loads((ROOT / "data/sv-work-items/required-checks.json").read_text())
        self.assertIn("supplied-epoch-binder-check", row["surface_kinds"]["all"]["checks"])
        self.assertEqual([k for k, v in row["surface_kinds"].items() if "supplied-epoch-binder-check" in v["checks"]], ["all"])
        for kind, path in sorted(fx.SURFACE_PATH.items()) + [("doc", "docs/example.md")]:
            self.assertIn("supplied-epoch-binder-check", wi.required_for([path])[0], kind)
            if kind == "doc":
                continue
            self.assertEqual(wi.admit(self.obs(path), fixture_mode=True)["disposition"], "ALLOW", kind)
            out = wi.admit(self.obs(path, rb=None), fixture_mode=True)
            self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"), kind)
            out = wi.admit(self.obs(path, hb="2048"), fixture_mode=True)
            self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "HB_EPOCH_MISMATCH"), kind)

    def test_every_positive_control_carries_a_sealed_fixture_readback(self):
        for s in base.jsonl("data/admission-scenarios/corpus.jsonl"):
            if s["expected_disposition"] == "ALLOW":
                rb = s["observed_inputs"]["hb_epoch_readback"]
                self.assertEqual(rb["result_sha256"], wi.sha({k: v for k, v in rb.items() if k != "result_sha256"}), s["scenario_id"])
                self.assertIs(rb["fixture_only"], True)
                self.assertEqual(rb["unobserved_fields"], ["bound_main_commit", "hb_epoch", "hb_epoch_source/receipt", "sources"])
                self.assertEqual(rb["hb_epoch"], s["observed_inputs"]["supplied_hb_epoch"])

    def test_inputs_carry_the_supplied_epoch_and_readback(self):
        o = self.obs()
        self.assertEqual(o["supplied_hb_epoch"], "1024")
        self.assertEqual(o["hb_epoch_readback"], fx.fixture_base_state_readback())
        self.assertIsNone(self.obs(rb=None)["hb_epoch_readback"])


class BuiltinCommandTests(unittest.TestCase):
    ROW = json.loads((ROOT / "data/sv-work-items/required-checks.json").read_text())
    C = "supplied-epoch-binder-check"

    def test_builtin_declared(self):
        c = self.ROW["checks"][self.C]
        self.assertEqual(c["offline_command"]["verifier_ref"], "SV-LLM/.github#46")
        self.assertEqual((c["command_paths"], c["expected"]), ([], {"disposition": "ALLOW"}))
        self.assertNotIn("command_status", c)
        self.assertTrue(wi.command_declared(self.C))
        out = wi.check_command(self.C, [])
        self.assertEqual((out["disposition"], out["argv"], out["verifier_builtin"]["verifier_builtin"]), ("ALLOW", None, self.C))
        self.assertEqual(wi.check_command_surface(self.C), "data/sv-work-items/required-checks.json")

    def test_malformed_builtin_is_undeclared(self):
        good = self.ROW["checks"][self.C]
        oc = good["offline_command"]
        for bad in ({**good, "offline_command": {**oc, "predicate": ""}}, {**good, "offline_command": {k: v for k, v in oc.items() if k != "verifier_ref"}},
                    {**good, "offline_command": {**oc, "verifier_builtin": "other-check"}}, {**good, "command_paths": ["x.py"]},
                    {**good, "offline_command": U}, {**good, "offline_command": []}):
            row = {**self.ROW, "checks": {**self.ROW["checks"], self.C: bad}}
            self.assertFalse(wi.command_declared(self.C, row))
            out = refusal(wi.check_command, self.C, [], row)
            self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "CHECK_COMMAND_UNDECLARED"))

    def test_receipts_for_the_builtin(self):
        r = {"schema": wi.CHECK_RECEIPT_SCHEMA, "check_id": self.C, "disposition": "ALLOW", "change_digest": "sha256:" + "a" * 64,
             "head_sha": "b" * 40, "hb_epoch": "1024", "verifier_ref": "SV-LLM/.github#46"}
        self.assertEqual(wi.validate_check_receipt(r)["disposition"], "ALLOW")
        fc = {**r, "disposition": "FAIL_CLOSED", "failure_code": "HB_EPOCH_SOURCE_UNOBSERVED", "failed_predicate": INV,
              "required_evidence_or_repair": "x", "retry_entrypoint": "y", "owning_existing_goal": GOAL163, "next_attempt": "z"}
        self.assertEqual(wi.validate_check_receipt(fc)["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")


class CorpusTests(unittest.TestCase):
    CLASSES = base.jsonl("data/admission-scenarios/classes.jsonl")
    CORPUS = base.jsonl("data/admission-scenarios/corpus.jsonl")

    def test_class_by_rule_and_scenarios(self):
        latest = al.latest_classes(self.CLASSES)
        c = latest[CID]
        self.assertEqual((c["class_version"], c["predicate"], c["surfaces"], c["expected_failure_code"], c["expected_disposition"]),
                         (2, INV, [{"kind": "ledger_writer"}], "HB_EPOCH_SOURCE_UNOBSERVED", "FAIL_CLOSED"))  # v2: the UNKNOWN axis
        self.assertEqual([x for x in latest if latest[x]["predicate"] == INV], [CID])  # no other class carries this predicate
        got = {s["generated_from"]["axis"]: (s["expected_disposition"], s["expected_failure_code"]) for s in self.CORPUS if s["scenario_class"] == CID}
        self.assertEqual(got, {None: ("ALLOW", None),
                               "hb_epoch_readback": ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"),
                               "hb_epoch_readback.result_sha256": ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"),
                               "hb_epoch_readback.hb_epoch_source.derived_from_clock": ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"),
                               "hb_epoch_readback.hb_epoch": ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"),
                               "supplied_hb_epoch": ("DENY", "HB_EPOCH_MISMATCH"),
                               "supplied_hb_epoch[UNKNOWN]": ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED")})
        # appended after every earlier scenario; only later classes' scenarios follow it, so no id moved
        ids = [s["scenario_id"] for s in self.CORPUS]
        at = ids.index(CID + "/supplied_hb_epoch[UNKNOWN]")
        later = {c["class_id"] for c in self.CLASSES[-1 - len(fx.BOOTSTRAP_SEEDS):]}
        self.assertNotIn(CID, later)
        self.assertTrue(all(s["scenario_class"] in later for s in self.CORPUS[at + 1:]))
        for s in self.CORPUS:
            if s["scenario_class"] == CID:
                out = wi.admit(s["observed_inputs"], fixture_mode=True)
                self.assertEqual((out["disposition"], out.get("failure_code")), (s["expected_disposition"], s["expected_failure_code"]))
        self.assertIsInstance(next(s for s in self.CORPUS if s["scenario_id"] == CID + "/hb_epoch_readback.hb_epoch")
                              ["observed_inputs"]["hb_epoch_readback"]["hb_epoch"], float)

    def test_gate_refuses_a_wrong_expected_code(self):
        classes, scenarios, _ = fx.corpus()
        n = len(fx.BOOTSTRAP_SEEDS) + 2  # epoch class v2, the bootstrap classes and the native-UNKNOWN class follow epoch v1
        later = {c["class_sha256"] for c in classes[len(classes) - n:]}
        later_ids = {c["class_id"] for c in classes[len(classes) - n:] if c["class_id"] != CID}
        classes = classes[:len(classes) - n]
        scenarios = [s for s in scenarios if s["scenario_class"] not in later_ids and s["source"].get("class_sha256") not in later]
        self.assertEqual(classes[-1]["class_id"], CID)
        pre = [s for s in scenarios if s["scenario_class"] != CID]
        mine = [s for s in scenarios if s["scenario_class"] == CID]
        bad = [wi.seal({**{k: v for k, v in s.items() if k != "scenario_sha256"}, "expected_disposition": "FAIL_CLOSED",
                        "expected_failure_code": "HB_EPOCH_SOURCE_UNOBSERVED"}, "scenario_sha256")
               if s["generated_from"]["axis"] == "supplied_hb_epoch" else s for s in mine]
        out = al.corpus_append(classes[:-1], pre, classes[-1], bad, hb_epoch=fx.FIXTURE_HB_EPOCH)
        self.assertEqual(out["failure_code"], "CLASS_NEVER_FIRES")
        self.assertEqual(al.corpus_append(classes[:-1], pre, classes[-1], mine, hb_epoch=fx.FIXTURE_HB_EPOCH)["disposition"], "ALLOW")

    def test_earlier_classes_unchanged(self):
        import subprocess
        old = subprocess.run(["git", "show", "fc19b5321bb37c5203fe9244441a268e72eaa67b:data/admission-scenarios/classes.jsonl"],
                             cwd=ROOT, capture_output=True, text=True)
        if old.returncode != 0:
            self.skipTest("fc19b532 not in the local clone")
        # fc19b532's classes are a prefix: epoch v1, epoch v2, the 5 bootstrap classes and the native-UNKNOWN class follow
        self.assertEqual([json.loads(l) for l in old.stdout.splitlines()], self.CLASSES[:-3 - len(fx.BOOTSTRAP_SEEDS)])



class KnownAnswerTests(unittest.TestCase):
    """StegVerse-Labs/.github refs/stegverse/organization-ledger @a5bb54d8: HEAD.json names receipt 35810b65, whose sealed
    $.hb_reference.epoch is 469411750 (bytes as read, tests/fixtures/org-ledger-StegVerse-Labs-a5bb54d8)."""
    LH = "a5bb54d81893b392a3ce28182986fc39857807e1"
    RX = "35810b6598e99cef32d9a0f1f97d07394d9f21c540ed7d3a395d9d78b753db3d"

    def objects(self):
        d = ROOT / "tests/fixtures/org-ledger-StegVerse-Labs-a5bb54d8"
        return {self.LH + ":HEAD.json": (d / "HEAD.json").read_bytes(),
                self.LH + ":receipts/" + self.RX + ".json": (d / "receipts" / (self.RX + ".json")).read_bytes()}

    def test_head_a5bb54d8_receipt_35810b65_is_469411750(self):
        objs = self.objects()
        self.assertEqual(json.loads(objs[self.LH + ":HEAD.json"])["receipt_sha256"], "sha256:" + self.RX)
        self.assertEqual(wi.base_ledger_head_epoch(self.LH, objs), 469411750)
        self.assertEqual(self.LH, fx.LABS_BASE["ledger_head"])

    def test_readback_shaped_like_lane_c_yields_469411750(self):
        rb = reseal(fx.fixture_base_state_readback(hb_epoch="469411750"), fixture_only=False,
                    hb_epoch_source={"ledger_head": self.LH, "receipt": "receipts/" + self.RX + ".json", "field": "$.hb_reference.epoch"})
        out = wi.verify_admission_hb_epoch("469411750", rb, self.LH)
        self.assertEqual((out["disposition"], out["hb_epoch"]), ("ALLOW", "469411750"))
        out = refusal(wi.verify_admission_hb_epoch, "469411751", rb, self.LH)
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "HB_EPOCH_MISMATCH"))


if __name__ == "__main__":
    unittest.main()
