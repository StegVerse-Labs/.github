"""STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE (Q-SV-NATIVE-BOOTSTRAP, decided by invariant): a stage gate is an admitted
transition, so a failing gate receipt is a ledgered failing check receipt and derive_issue_from_check_receipt applies to it
unchanged. Conditions (a)-(d) at admission, the gate check declared by the stage manifest, and the per-repository ledger
binding. Pure; no clock, no network."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest

from tests import test_sv_native_work_items as base
from tests import sv_ledger_fixtures as lf

wi, fx, al = base.wi, base.fx, base.al
ROOT = base.ROOT
GOAL163 = "StegVerse-org/.github#163"
INV = "STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE"
GATE = "nwi-s0-exit-gate"
MANIFEST = "data/sv-work-items/stages/NWI-S0.json"
COMMIT = "c" * 40
OBS_BASE = dict(fx.LABS_BASE)
S1_RUN = "SV-LLM/.github#46@64b90721"

import importlib.util, sys  # noqa: E402
sg = sys.modules.get("stage_gate")
if sg is None:
    _s = importlib.util.spec_from_file_location("stage_gate", ROOT / "resident-runtime/stage_gate.py")
    sg = importlib.util.module_from_spec(_s); sys.modules["stage_gate"] = sg; _s.loader.exec_module(sg)


def refusal(fn, *a, **k):
    try:
        return fn(*a, **k)
    except wi.Refusal as r:
        return r.record


def gate_receipt(verifier_ref=S1_RUN, code="STAGE_EVIDENCE_UNOBSERVED"):
    """The receipt the NWI-S1 verifier emits when the NWI-S0 exit gate fails (sv-check-receipt.v1, six fields)."""
    return {"schema": wi.CHECK_RECEIPT_SCHEMA, "check_id": GATE, "disposition": "FAIL_CLOSED", "change_digest": "sha256:" + "a" * 64,
            "head_sha": "b" * 40, "hb_epoch": "1024", "verifier_ref": verifier_ref, "failure_code": code,
            "failed_predicate": "UNKNOWN_NEVER_YIELDS_PASS", "required_evidence_or_repair": "a receipted outcome for every exit predicate",
            "retry_entrypoint": "resident-runtime/stage_gate.py::evaluate_gate", "owning_existing_goal": GOAL163,
            "next_attempt": "re-evaluate with the receipts; nothing moved"}


def ledgered(receipt, commit=COMMIT):
    repo = lf.repo_receipt(receipt, 1024)
    org = lf.org_receipt(repo, 1024, boundary_evidence=lf.boundary())
    return lf.ledger_objects(commit, org, repo), lf.org_ref(commit, org), org, repo


def resolving_change(issue_ids, *, path=fx.SURFACE_PATH["transition"], extra_content=(), writer=fx.SESSION):
    ch = fx.known_good_change(path)
    ch["content"] = [{**c, "writer_session": {"session": writer, "evidence_class": "DECLARED"}} for c in ch["content"]] + list(extra_content)
    ch["touched_paths"] = sorted(c["path"] for c in ch["content"])
    ch["resolves"] = sorted(issue_ids)
    return base.reseal_change(dict(ch, declared_session=writer))


def admit(ch, facts, fixture_mode=False):
    obs = wi.admission_inputs(ch, fx.LABS_BASE, fx.signoff_receipts_for(ch), fx.fixture_base_state_readback(), facts)
    return refusal(wi.verify_resolutions, obs, fixture_mode=fixture_mode)


class GateCheckDeclarationTests(unittest.TestCase):
    def test_manifest_declares_the_gate_as_an_s1_check(self):
        m = json.loads((ROOT / MANIFEST).read_text())
        c = m["exit_gate_check"]
        self.assertEqual((c["check_id"], c["offline_command"]["verifier_ref"], c["surface"]), (GATE, wi.S1_VERIFIER_REF, MANIFEST))
        self.assertIn("SV-LLM/.github#46", c["minter"]); self.assertIn("#3255", c["appender"]); self.assertIn("#3270", c["appender"])
        self.assertEqual(sg.gate_check(m)["check_id"], GATE)
        self.assertEqual(wi.GATE_CHECKS[GATE]["declared_in"]["rule_id"], "NWI-S0#exit_gate_check." + GATE)
        # home: the stage manifest, not the required-checks row (no SV_CHANGE requires a stage gate)
        self.assertNotIn(GATE, wi.REQUIRED_CHECKS["checks"])
        self.assertNotIn(GATE, {c for v in wi.REQUIRED_CHECKS["surface_kinds"].values() for c in v["checks"]})
        self.assertIn(GATE, wi.declared_check_ids())
        schema = json.loads((ROOT / "schemas/sv-check-receipt.v1.schema.json").read_text())
        self.assertIn(GATE, schema["properties"]["check_id"]["enum"])
        self.assertEqual(wi.check_command_surface(GATE), MANIFEST)
        out = wi.check_command(GATE, [])
        self.assertEqual((out["disposition"], out["argv"]), ("ALLOW", None))

    def test_gate_outcome_names_its_check(self):
        out = sg.evaluate_gate("NWI-S0", "NWI-S1", {}, hb_epoch="1024")
        self.assertEqual((out["disposition"], out["failure_code"], out["gate_check_id"]), ("FAIL_CLOSED", "STAGE_EVIDENCE_UNOBSERVED", GATE))

    def test_a_gate_check_not_emitted_by_s1_is_refused(self):
        m = json.loads((ROOT / MANIFEST).read_text())
        for bad in ({**m["exit_gate_check"], "minter": "P1 Ecosystem AI Lane (d8cbc58c)"},
                    {**m["exit_gate_check"], "offline_command": {**m["exit_gate_check"]["offline_command"], "verifier_ref": "SV-LLM/.github#460"}}):
            out = refusal(sg.gate_check, {**m, "exit_gate_check": bad})
            self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "STAGE_GATE_CHECK_NOT_S1_EMITTED"))


class DerivationTests(unittest.TestCase):
    def test_failing_gate_receipt_derives_a_native_issue_unchanged(self):
        objs, ref, org, repo = ledgered(gate_receipt())
        iss = wi.derive_issue_from_check_receipt(objs, ref, observed_base=OBS_BASE)
        self.assertEqual(iss["record_mode"], "NATIVE")
        self.assertEqual(iss["surface"], {"kind": wi.surface_kind(MANIFEST), "path": MANIFEST})
        self.assertEqual(iss["violated_invariant"], {"repository": "StegVerse-Labs/.github", "file": MANIFEST,
                                                     "rule_id": "NWI-S0#exit_gate_check." + GATE, "blob_sha": None, "invariant_declared": True})
        self.assertEqual(iss["source_receipt"]["receipt_sha256"], org["receipt_sha256"])
        self.assertEqual(iss["opened_by_session"], wi.ISSUE_DERIVATION_SESSION)
        again = wi.derive_issue_from_check_receipt(objs, ref, observed_base=OBS_BASE)
        self.assertEqual(again["issue_id"], iss["issue_id"])  # deterministic: one receipt, one issue

    def test_not_ledgered_derives_nothing(self):
        objs, ref, org, repo = ledgered(gate_receipt())
        out = refusal(wi.derive_issue_from_check_receipt, {}, ref, observed_base=OBS_BASE)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "SOURCE_RECEIPT_NOT_LEDGERED"))


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.objs, self.ref, self.org, self.repo = ledgered(gate_receipt())
        self.iss = wi.derive_issue_from_check_receipt(self.objs, self.ref, observed_base=OBS_BASE)
        self.facts = wi.resolved_issue_facts([self.iss], self.objs)

    def test_facts_from_the_ledger_bytes(self):
        f, = self.facts
        hexs = self.org["receipt_sha256"].split(":")[1], self.repo["receipt_sha256"].split(":")[1]
        self.assertEqual(f["receipt_ledger_paths"], sorted(["receipts/%s.json" % hexs[0], "source-receipts/%s.json" % hexs[1]]))
        self.assertEqual((f["verifier_ref"], f["emitter_session"], f["check_id"], f["fixture_only"]), (S1_RUN, S1_RUN, GATE, False))
        self.assertEqual(f["derived_issue_ids_from_receipt"], [self.iss["issue_id"]])
        self.assertIn("sha256:" + hashlib.sha256(self.objs[COMMIT + ":receipts/%s.json" % hexs[0]]).hexdigest(), f["receipt_file_sha256"])
        self.assertEqual(wi.resolved_issue_facts([self.iss], {}), [])  # not ledgered: no fact

    def test_clean_change_resolves_the_issue(self):
        # commit 4 (GATE_RECEIPT_PAIR_RESOLVES_GATE_DERIVED_ISSUE): the base-side receipt alone sources the issue but never resolves
        # it; ALLOW needs the head-side ALLOW receipt (tests/test_nwi_gate_receipt_pair.py)
        ch = resolving_change([self.iss["issue_id"]])
        out = admit(ch, self.facts)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("FAIL_CLOSED", "GATE_PAIR_HEAD_RECEIPT_MISSING", "GATE_RECEIPT_PAIR_RESOLVES_GATE_DERIVED_ISSUE"))

    def test_a_self_sourced_issue_is_deny(self):
        f, = self.facts
        led_path = f["receipt_ledger_paths"][0]
        org_bytes = self.objs[COMMIT + ":" + next(p for p in f["receipt_ledger_paths"] if p.startswith("receipts/"))]
        cases = {
            "touches the ledger path": resolving_change([self.iss["issue_id"]], extra_content=[
                {"path": led_path, "blob_digest": "sha256:" + "d" * 64, "deleted": False, "writer_session": {"session": fx.SESSION, "evidence_class": "DECLARED"}}]),
            "carries the receipt bytes": resolving_change([self.iss["issue_id"]], extra_content=[
                {"path": "docs/gate-receipt.json", "blob_digest": "sha256:" + hashlib.sha256(org_bytes).hexdigest(), "deleted": False,
                 "writer_session": {"session": fx.SESSION, "evidence_class": "DECLARED"}}]),
            "written by the emitter": resolving_change([self.iss["issue_id"]], writer=S1_RUN),
        }
        for name, ch in cases.items():
            out = admit(ch, self.facts)
            self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                             ("DENY", "SV_CHANGE_SELF_SOURCED_ISSUE", "RESOLVING_CHANGE_DID_NOT_SOURCE_ITS_ISSUE"), name)
        # a receipt whose verifier_ref is not the NWI-S1 verifier
        for ref in ("P1 Ecosystem AI Lane (d8cbc58c)", "SV-LLM/.github#460", "SV-LLM/.github#46x"):
            objs, lref, _, _ = ledgered(gate_receipt(verifier_ref=ref))
            iss = wi.derive_issue_from_check_receipt(objs, lref, observed_base=OBS_BASE)
            out = admit(resolving_change([iss["issue_id"]]), wi.resolved_issue_facts([iss], objs))
            self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "SV_CHANGE_SELF_SOURCED_ISSUE"), ref)
        for ok in ("SV-LLM/.github#46", "SV-LLM/.github#46@64b90721", "SV-LLM/.github#46:run-1"):
            self.assertTrue(wi.is_s1_verifier(ok), ok)

    def test_one_receipt_derives_one_issue(self):
        other = copy.deepcopy(self.iss)
        other["disposition"] = {**other["disposition"], "failed_predicate": "STAGE_GATE_PASSES"}
        other["issue_id"] = wi.issue_identity(other)
        other = wi.seal({k: v for k, v in other.items() if k != "issue_sha256"}, "issue_sha256")
        self.assertNotEqual(other["issue_id"], self.iss["issue_id"])
        out = refusal(wi.validate_issue_set, [self.iss, other])
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("FAIL_CLOSED", "SV_ISSUE_SOURCE_RECEIPT_COLLISION", "ONE_RECEIPT_DERIVES_ONE_ISSUE"))
        facts = wi.resolved_issue_facts([self.iss], self.objs, issue_set=[self.iss, other])
        out = admit(resolving_change([self.iss["issue_id"]]), facts)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "SV_ISSUE_SOURCE_RECEIPT_COLLISION"))
        self.assertEqual(wi.resolved_issue_facts([other], self.objs), [])  # not what the receipt derives: unobserved

    def test_two_changes_cannot_resolve_one_receipt_issue(self):
        first = resolving_change([self.iss["issue_id"]])
        resolved = wi.seal({**{k: v for k, v in self.iss.items() if k != "issue_sha256"}, "lifecycle_state": "RESOLVED",
                            "resolved_by": first["change_id"]}, "issue_sha256")
        facts = wi.resolved_issue_facts([resolved], self.objs)
        second = resolving_change([self.iss["issue_id"]], path="resident-runtime/another_repair.py")
        out = admit(second, facts)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("DENY", "SV_ISSUE_ALREADY_RESOLVED", "RECEIPT_DERIVED_ISSUE_IS_RESOLVED_ONCE"))
        self.assertEqual(admit(first, facts)["failure_code"], "GATE_PAIR_HEAD_RECEIPT_MISSING")  # its own resolution is not a second one

    def test_3264_stays_resolves_nothing_until_the_receipt_is_ledgered(self):
        ch = resolving_change([])  # what #3264 cites today: nothing (no gate receipt is on the ledger)
        self.assertEqual(refusal(wi.validate_change, ch)["failure_code"], "SV_CHANGE_RESOLVES_NOTHING")
        out = admit(ch, [])
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "SV_CHANGE_RESOLVES_NOTHING"))
        # citing the id the receipt WOULD derive, before the org writer appends it: no fact, still resolves nothing
        early = resolving_change([self.iss["issue_id"]])
        out = admit(early, wi.resolved_issue_facts([self.iss], {}))
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "SV_CHANGE_RESOLVES_NOTHING"))
        # fixture facts never count on the real path
        out = admit(early, fx.fixture_resolved_issues(early))
        self.assertEqual(out["failure_code"], "SV_CHANGE_RESOLVES_NOTHING")
        self.assertEqual(admit(early, fx.fixture_resolved_issues(early), fixture_mode=True)["disposition"], "ALLOW")
        out = wi.admit(wi.admission_inputs(ch, fx.LABS_BASE, fx.signoff_receipts_for(ch), fx.fixture_base_state_readback(), []), fixture_mode=True)
        self.assertEqual((out["disposition"], out["failure_code"]), ("DENY", "SV_CHANGE_RESOLVES_NOTHING"))

    def test_migrated_issues_are_never_admissible(self):
        mig = base.jsonl("data/sv-work-items/migration/sv-issues.jsonl")[0]
        self.assertEqual(mig["record_mode"], "MIGRATED_HISTORICAL")
        facts = wi.resolved_issue_facts([mig], {})
        ch = resolving_change([mig["issue_id"]])
        out = admit(ch, facts)
        self.assertEqual((out["disposition"], out["failure_code"], out["failed_predicate"]),
                         ("FAIL_CLOSED", "HISTORICAL_RECORD_NOT_ADMISSIBLE", "ADMITTED_RECORDS_ARE_NATIVE"))


class LedgerBindingTests(unittest.TestCase):
    def test_readback_of_another_repository_ledger_is_unobserved(self):
        ch = fx.known_good_change(fx.SURFACE_PATH["transition"])
        rb = fx.fixture_base_state_readback()
        other = wi.seal({**{k: v for k, v in rb.items() if k != "result_sha256"}, "repository": "StegVerse-org/.github"}, "result_sha256")
        for r, want in ((rb, "ALLOW"), (other, "HB_EPOCH_SOURCE_UNOBSERVED")):
            obs = wi.admission_inputs(ch, fx.LABS_BASE, fx.signoff_receipts_for(ch), r, fx.fixture_resolved_issues(ch))
            out = wi.admit(obs, fixture_mode=True)
            self.assertEqual(out.get("failure_code") or out["disposition"], want)
        self.assertEqual(obs["target_repository"], "StegVerse-Labs/.github")


class InvariantRecordTests(unittest.TestCase):
    INV = {i["invariant_id"]: i for i in json.loads((ROOT / "data/sv-work-items/invariants.json").read_text())["invariants"]}

    def test_recorded(self):
        e = self.INV[INV]
        self.assertIn("Q-SV-NATIVE-BOOTSTRAP", e["decides"])
        self.assertEqual(set(e["conditions"]), {"a", "b", "c", "d"})
        self.assertEqual(e["conditions"]["a"]["failure_code"], "SV_CHANGE_SELF_SOURCED_ISSUE")
        self.assertIn("Q-P1-EPOCH-PROVENANCE", json.dumps(e))
        b = self.INV["CHANGE_BINDS_TARGET_REPOSITORY_LEDGER"]
        self.assertIn("2acec0e1", json.dumps(b)); self.assertIn("a5bb54d8", json.dumps(b))

    def test_old_candidate_name_is_gone(self):
        token = "BOOTSTRAP_" + "SELF_ADMISSION"
        for d in ("docs", "data/sv-work-items", "resident-runtime", "scripts", "schemas", "tests"):
            for p in (ROOT / d).rglob("*"):
                if p.is_file() and p.suffix in (".py", ".json", ".jsonl", ".md"):
                    self.assertNotIn(token, p.read_text(errors="ignore"), str(p))


class CorpusTests(unittest.TestCase):
    CORPUS = base.jsonl("data/admission-scenarios/corpus.jsonl")
    CLASSES = al.latest_classes(base.jsonl("data/admission-scenarios/classes.jsonl"))

    def test_conditions_are_corpus_classes_that_fire(self):
        want = {"CHANGE_RESOLVES_CLAIMED_SV_ISSUES": "SV_CHANGE_RESOLVES_NOTHING", "RESOLVING_CHANGE_DID_NOT_SOURCE_ITS_ISSUE": "SV_CHANGE_SELF_SOURCED_ISSUE",
                "ONE_RECEIPT_DERIVES_ONE_ISSUE": "SV_ISSUE_SOURCE_RECEIPT_COLLISION", "RECEIPT_DERIVED_ISSUE_IS_RESOLVED_ONCE": "SV_ISSUE_ALREADY_RESOLVED",
                "ADMITTED_RECORDS_ARE_NATIVE": "HISTORICAL_RECORD_NOT_ADMISSIBLE"}
        for pred, code in want.items():
            cid = "ASC-" + pred + "@transition"
            self.assertEqual(self.CLASSES[cid]["expected_failure_code"], code)
            mine = [s for s in self.CORPUS if s["scenario_class"] == cid]
            self.assertEqual(sum(s["expected_disposition"] == "ALLOW" for s in mine), 1)
            for s in mine:
                out = wi.admit(s["observed_inputs"], fixture_mode=True)
                self.assertEqual((out["disposition"], out.get("failure_code")), (s["expected_disposition"], s["expected_failure_code"]), s["scenario_id"])
        ids = {s["scenario_id"] for s in self.CORPUS}
        self.assertIn("ASC-CHANGE_RESOLVES_CLAIMED_SV_ISSUES@transition/resolves", ids)  # (c), the #3264 case
        self.assertIn("ASC-ADMITTED_RECORDS_ARE_NATIVE@transition/resolved_issues[0].record_mode", ids)  # (d)


if __name__ == "__main__":
    unittest.main()
