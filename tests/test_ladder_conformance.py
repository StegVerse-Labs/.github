"""Ladder-conformance check over the priority goals (StegVerse-org/.github#163): the committed artifacts regenerate
byte-identically, and each refusal the check claims to make is made. stdlib unittest; no network, clock or LLM."""
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
sys.path.insert(0, str(ROOT / "resident-runtime"))
import ladder_conformance as lc  # noqa: E402

_spec = importlib.util.spec_from_file_location("ladder_conformance_cli", ROOT / "scripts/ladder_conformance.py")
cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cli)

KV, GOV = lc.GOALS


def _inputs():
    return cli.load_inputs(lc.BASE)


def _codes(doc, item_id):
    return [f["failure_code"] for r in doc["items"] if r["id"] == item_id for f in r["refusals"]]


def _verdict(doc, item_id):
    return next(r["verdict"] for r in doc["items"] if r["id"] == item_id)


class CommittedArtifacts(unittest.TestCase):
    def test_check_allows_the_committed_artifacts(self):
        out = cli.check()
        self.assertEqual(out["disposition"], "ALLOW", out)

    def test_regeneration_is_byte_identical(self):
        for g, text in cli.build().items():
            self.assertEqual((lc.BASE / "conformance" / (g + ".conformance.json")).read_text(), text, g)

    def test_every_sealed_predicate_is_checked_and_counts_add_up(self):
        for g, text in cli.build().items():
            d = json.loads(text)
            decl = _inputs()["declarations"][g]
            preds = [r["id"] for r in d["items"] if r["kind"] == "PREDICATE"]
            self.assertEqual(sorted(preds), sorted(decl["sealed_expected_evidence_predicates"]), g)
            self.assertEqual(sum(d["counts"][k]["checked"] for k in lc.KINDS), len(d["items"]))
            self.assertEqual(d["gaps"], sum(1 for r in d["items"] if r["verdict"] != "ALLOW"))

    def test_every_non_allow_item_carries_six_fields_and_a_scoped_task(self):
        for g, text in cli.build().items():
            d = json.loads(text)
            for r in d["items"]:
                for f in r["refusals"]:
                    for k in lc.om.SIX:
                        self.assertTrue(isinstance(f.get(k), str) and f[k].strip(), (g, r["id"], k))
                if r["verdict"] != "ALLOW":
                    self.assertTrue(r["scoped_tasks"], (g, r["id"]))

    def test_scoped_tasks_name_the_owning_lane(self):
        lanes = {KV: "Lane D", GOV: "GitHub Product"}
        tasks = _inputs()["tasks"]
        self.assertTrue(tasks)
        for t in tasks:
            self.assertIn(lanes[t["goal"]], t["owning_lane"])
            for k in lc.TASK_SIX:
                self.assertTrue(t[k].strip(), (t["task_id"], k))
            self.assertEqual(t["status"], "SCOPED_TASK_RECORD_ONLY")
        for t in tasks:
            if t["items"] == ["H-KV-HEALTHY-NODE-DETERMINATION"]:
                self.assertTrue(t["owning_lane"].startswith("InTr and Mesh Destinations lane"), t["task_id"])

    def test_two_credential_layers_are_separate_sequential_checks(self):
        d = json.loads(cli.build()[KV])
        layers = {r["id"]: r for r in d["items"] if r["kind"] == "CONSTRAINT" and r["id"] != "ENDPOINT_NOT_A_GITHUB_ORGANIZATION_MEMBER"}
        decl = {i["id"]: i for i in _inputs()["declarations"][KV]["items"]}
        self.assertEqual(sorted(str(decl[i]["layer"]) for i in layers), ["1", "1->2", "2"])
        l1 = next(i for i in layers if decl[i]["layer"] == 1)
        l2 = next(i for i in layers if decl[i]["layer"] == 2)
        seq = next(i for i in layers if decl[i]["layer"] == "1->2")
        for i in (l1, l2):  # each layer refuses on its own, with six fields and its own scoped tasks
            self.assertTrue(layers[i]["refusals"] and layers[i]["scoped_tasks"], i)
        # revision 6 (cvk#258 @b93b06a4 vendoring LLM-adapter#432 @1cbad77e): layer 1 has no bypass of its own and no
        # witness failure (LC-KV-17 closed: an unsigned EPHEMERAL anchor is refused); production ALLOW still needs the
        # transport installed (a code edit, LC-KV-15); LC-KV-16 is closed at #432 @a2ee67e6: the anchor handoff has no
        # bypass, only the TV/TVC-unbound ALLOW path (LC-KV-18)
        self.assertNotIn("LADDER_ACCESS_PATH_BYPASSES_LAYER", _codes(d, l1))
        self.assertIn("LADDER_ALLOW_PATH_UNBOUND", _codes(d, l1))
        self.assertIn("LADDER_ACCESS_PATH_BYPASSES_LAYER", _codes(d, l2))
        self.assertNotIn("LADDER_ACCESS_PATH_BYPASSES_LAYER", _codes(d, "H-KV-ENDPOINT-LEDGER-ANCHOR"))
        self.assertIn("LADDER_ALLOW_PATH_UNBOUND", _codes(d, "H-KV-ENDPOINT-LEDGER-ANCHOR"))
        anc = decl["H-KV-ENDPOINT-LEDGER-ANCHOR"]
        # revision 16 (Coordination ruling): the cvk-only both-ends anchor; KV's own head record decides (ruling A)
        self.assertTrue(anc["e0_terminal"]["by"].startswith("StegVerse-Labs/continuity-vault-kit@77d28d838ec6714044a192d4f549c3ca9366ff3f: "
                                                            "runtime/kv_receipt_ledgers.py::read_receipt_ledger"))
        self.assertEqual(anc["e0_terminal"]["dispositions"], ["ALLOW", "DENY", "FAIL_CLOSED"])
        self.assertEqual(anc["observed_by"], ["cvk263-chain-probe", "cvk263-anchor-production-prerequisites"])
        self.assertEqual([b["id"] for b in anc["allow_path"]["blockers"]],
                         ["KV_RECEIPT_CHAIN_GENESIS_NOT_PINNED", "KV2_STORAGE_ENDPOINT_PENDING_INTERLOCK_INTR",
                          "ORG_CROSSING_READER_NOT_INSTALLED", "KV_RECEIPT_CHAIN_READERS_NOT_ALIGNED"])
        self.assertEqual([r["ref"] for r in anc["external_dependency_refs"]], ["ORG-LEDGER-HEAD-SIGNER-001"])
        self.assertTrue(anc["external_dependency_refs"][0]["owner"].startswith("GitHub Product lane"))
        self.assertIn("no bot does it", anc["external_dependency_refs"][0]["evidence"])
        self.assertIn("held only in the SKAP Vault", anc["external_dependency_refs"][0]["evidence"])
        self.assertNotIn("unadmitted_dependencies", anc)
        res = next(r for r in d["items"] if r["id"] == "H-KV-ENDPOINT-LEDGER-ANCHOR")
        self.assertEqual(sorted(r.get("blocker") for r in res["refusals"] if r["failure_code"] == "LADDER_ALLOW_PATH_UNBOUND"),
                         sorted(b["id"] for b in anc["allow_path"]["blockers"]))
        self.assertEqual(sorted({r["failure_code"] for r in res["refusals"]}),
                         ["LADDER_ALLOW_PATH_UNBOUND", "LADDER_EXTERNAL_DEPENDENCY_PENDING"])
        self.assertEqual([r["external_ref"] for r in res["refusals"] if r["failure_code"] == "LADDER_EXTERNAL_DEPENDENCY_PENDING"],
                         ["ORG-LEDGER-HEAD-SIGNER-001"])
        for w_ in ("KV", "SKAP_VAULT"):
            for c_ in ("KV2_STORAGE_ENDPOINT_PENDING_INTERLOCK_INTR", "KV_RECEIPT_CHAIN_GENESIS_NOT_PINNED",
                       "KV_RECEIPT_CHAIN_GENESIS_PIN_MECHANISM_ORG_HOSTED", "KV_LEDGER_HEAD_SIGNER_NOT_PUBLISHED"):
                self.assertEqual(anc["required_outcomes"]["PROD_PREREQ_%s_%s" % (c_, w_)], ["FAIL_CLOSED"], (c_, w_))
        self.assertEqual(anc["required_outcomes"]["ORG_CROSSING_READER_INSTALLED"], ["FAIL_CLOSED"])
        self.assertEqual(anc.get("bypass_paths") or [], [])
        for s_ in ("PROD_LAYER1_SCRATCH_LEDGER_AND_ASSERTED_IDENTITY", "LAYER1_TRANSPORT_NOT_INSTALLED",
                   "LAYER1_NODE_LEDGER_WITHOUT_ANCHOR", "LAYER1_EPHEMERAL_ANCHORED_BY_UNSIGNED_OPENED_RECORD",
                   "PROD_LAYER1_INJECTED_DISGUISED_EVALUATOR", "LAYER1_EPHEMERAL_OPENED_RECORD_SIGNED_BY_UNPUBLISHED_KEY",
                   "LAYER1_INGRESS_RECORD_NAMES_NO_INSTALLED_TRANSPORT"):
            self.assertIn(s_, decl[l1]["required_outcomes"])
        self.assertNotIn("OPERATING_MODE_E0_WITNESS_FAILED", _codes(d, l1))
        # revision 9: cvk#258 @9551edab refuses the caller-created unlabelled org store, so it is now required
        self.assertEqual(decl[l1]["required_outcomes"]["LAYER1_PERMANENT_ON_CALLER_CREATED_UNLABELLED_ORG_STORE"], ["DENY", "FAIL_CLOSED"])
        # layer 2's TV/TVC bypass is observed at TVC#541: the custody chain's refusals are required
        self.assertIn("skap-custody-chain-probe-tvc541", decl[l2]["observed_by"])
        self.assertIn("CHAIN_LAYER2_NOT_BOUND_TO_LAYER1", decl[l2]["required_outcomes"])
        # revision 9: at TVC#541 @63705c86 the caller-minted rows are FAIL_CLOSED (no designated receipt ledger), so required
        self.assertEqual(decl[l2]["required_outcomes"]["CHAIN_CALLER_MINTED_LAYERS_WITH_TVC537_ISSUED_RECEIPT_AND_CALLER_CLIENT"],
                         ["DENY", "FAIL_CLOSED"])
        self.assertIn("72decca1c0e1d0d60b5801cb01f0fab70ea038dc", decl[l2]["bypass_paths"][0])  # revision 11: narrowed 11 files to 3
        self.assertIn("from 11 files to 3", decl[l2]["bypass_paths"][0])
        # revision 9: TVC#541 @63705c86 takes no caller-minted layer receipts (mint-both tests witnessed as ALLOW = passed);
        # the systemd units naming the legacy root are an external machine on layer 2 (LC-KV-22)
        for s_ in ("TVC541_TEST_P1_MINT_BOTH_IS_FAIL_CLOSED_ON_GATE_READ_THROUGH_AND_PLACE",
                   "TVC541_TEST_P1_MINT_BOTH_BUILD_AND_VALIDATE_FAIL_CLOSED"):
            self.assertEqual(decl[l2]["required_outcomes"][s_], ["ALLOW"], s_)
        self.assertIn("tvc541-mint-both-tests", decl[l2]["observed_by"])
        # revision 11: TVC#541 @72decca1 ships no unit naming the legacy root (LC-KV-22 closed)
        self.assertNotIn("LADDER_EXTERNAL_MACHINE_REQUIRED", _codes(d, l2))
        self.assertFalse(decl[l2].get("external_requirements"))
        self.assertIn("LADDER_ACCESS_LAYERS_COLLAPSED", _codes(d, seq))
        self.assertTrue(set(decl[l1]["required_outcomes"]) and "e0_terminal" in decl[l1])
        # layer 2 now has its own E0 gate (SkapLayer2Gate), witnessed by required refusals, not a class_b record
        self.assertNotIn("class_b", decl[l2])
        self.assertTrue(set(decl[l2]["required_outcomes"]) and "e0_terminal" in decl[l2])
        # the sequence check requires layer 2 to refuse a receipt from a non-pinned or disguised evaluator; LC-KV-10 is
        # closed (object-identity pin), so the sequence carries no witness failure
        self.assertIn("LAYER2_ON_LAYER1_RECEIPT_FROM_NON_PINNED_EVALUATOR", decl[seq]["required_outcomes"])
        self.assertIn("LAYER2_ON_LAYER1_RECEIPT_FROM_DISGUISED_NON_PINNED_EVALUATOR", decl[seq]["required_outcomes"])
        self.assertNotIn("OPERATING_MODE_E0_WITNESS_FAILED", _codes(d, seq))
        self.assertIn("REQUESTER_IS_CURRENTLY_ADMITTED_HEALTHY_NODE", decl[l1]["what"])

    def test_lc_kv_13_has_the_fixed_finish_point(self):
        t = next(t for t in _inputs()["tasks"] if t["task_id"] == "LC-KV-13")
        self.assertEqual(t["finish_point"], "Ends when one live node goes from a receipted registration to layer-1 ALLOW, "
                         "end to end, on real ledger inputs. Anything beyond that is a new registered task.")
        self.assertIn("LLM-adapter#428", t["finish_point_cross_reference"])
        self.assertIn("#429", t["finish_point_cross_reference"])
        self.assertIn("confirmed by Coordination", t["owning_lane_mapping"])
        self.assertTrue(t["owning_lane"].startswith("InTr and Mesh Destinations lane (Lane B"))

    def test_lc_kv_15_is_closed_and_model_conflicts_are_recorded(self):
        tasks = {t["task_id"]: t for t in _inputs()["tasks"]}
        # revision 9: cvk#258 @9551edab vendors #432; LC-KV-15 closed, its remaining transport gap is LC-KV-13's
        self.assertNotIn("LC-KV-15", tasks)
        self.assertNotIn("LC-KV-16", tasks)  # closed in revision 6: (a), (b) and (c) are FAIL_CLOSED at #432 @a2ee67e6
        self.assertNotIn("LC-KV-10", tasks)
        m = tasks["LC-KV-21"]  # revision 16: narrowed to TV/TVC's reader binding to KV's current designation
        self.assertEqual(m["blocker"], "KV_RECEIPT_CHAIN_READERS_NOT_ALIGNED")
        self.assertEqual(m["items"], ["H-KV-ENDPOINT-LEDGER-ANCHOR"])
        self.assertEqual(m["failure_code"], "LADDER_ALLOW_PATH_UNBOUND")
        # re-pins inside TV/TVC's own reader are class A; TVC main @b686a60b does not bind to continuity-vault-kit @77d28d83
        self.assertEqual(m["failure_class"]["class"], "A")
        self.assertTrue(m["owning_lane"].startswith("GitHub Product lane as TV/TVC owner"))
        self.assertIn("77d28d83", m["required_repair"])
        self.assertIn("77d28d83", m["proposed_resolution"])
        self.assertIn("KV_RECEIPT_CHAIN_DESIGNATION_DIGEST_MISMATCH", m["required_repair"])
        for t in tasks.values():  # withdrawn names and ledger-wide encryption are gone from every proposal
            self.assertNotIn("gateway node", t["proposed_resolution"], t["task_id"])
            self.assertNotIn("encrypted contents", t["proposed_resolution"], t["task_id"])
        self.assertNotIn("merge-ready", json.dumps(m))
        self.assertNotIn("LC-KV-22", tasks)  # closed in revision 11: TVC#541 @72decca1 ships no unit naming the legacy root
        for t in (m,):
            for k in ("failure_code", "failed_check", "required_repair", "retry_point", "owning_goal", "next_attempt"):
                self.assertTrue(str(t.get(k) or "").strip(), k)
        f = next(t for t in _inputs()["tasks"] if t["task_id"] == "LC-KV-13")
        self.assertIn("finish_point_model_conflict_note", f)
        for t in tasks.values():  # every open task carries a class, for the cross-goal blocker list
            self.assertIn(t["failure_class"]["class"], ("A", "B", "C"), t["task_id"])

    def test_rev16_anchor_tasks_are_cvk_only(self):
        tasks = {t["task_id"]: t for t in _inputs()["tasks"]}
        # revision 16: the withdrawn edge's tasks are retired (EPHEMERAL signer, org genesis pin, org emitter, membership bypass)
        for tid in ("LC-KV-18", "LC-KV-19", "LC-KV-20", "LC-KV-25"):
            self.assertNotIn(tid, tasks)
        anc = sorted(t["task_id"] for t in tasks.values() if "H-KV-ENDPOINT-LEDGER-ANCHOR" in t["items"])
        self.assertEqual(anc, ["LC-KV-21", "LC-KV-27", "LC-KV-28", "LC-KV-29"])
        exp = {"LC-KV-27": ("KV_RECEIPT_CHAIN_GENESIS_NOT_PINNED", "B", "Lane D (KV and WorkSpace"),
               "LC-KV-28": ("KV2_STORAGE_ENDPOINT_PENDING_INTERLOCK_INTR", "B", "Lane D (KV and WorkSpace)"),
               "LC-KV-29": ("ORG_CROSSING_READER_NOT_INSTALLED", "B", "InTr and Mesh Destinations lane (Lane B"),
               "LC-KV-21": ("KV_RECEIPT_CHAIN_READERS_NOT_ALIGNED", "A", "GitHub Product lane as TV/TVC owner")}
        for tid, (blocker, cls, lane) in exp.items():
            t = tasks[tid]
            self.assertEqual((t["blocker"], t["failure_code"], t["failure_class"]["class"]),
                             (blocker, "LADDER_ALLOW_PATH_UNBOUND", cls), tid)
            self.assertEqual(t["items"], ["H-KV-ENDPOINT-LEDGER-ANCHOR"], tid)
            self.assertTrue(t["owning_lane"].startswith(lane), tid)
            self.assertNotIn("merge-ready", json.dumps(t))
            for k in ("failure_code", "failed_check", "required_repair", "retry_point", "owning_goal", "next_attempt"):
                self.assertTrue(str(t.get(k) or "").strip(), (tid, k))
        self.assertIn("SUPPLIED_HB_EPOCH", tasks["LC-KV-27"]["required_repair"])
        self.assertIn("a fabricated genesis digest is not evidence", tasks["LC-KV-27"]["required_repair"])
        self.assertIn("SITE-CLOUD-KV-4347408852127319cbda574f02e03edb", tasks["LC-KV-28"]["required_repair"])
        self.assertIn("6372641743", tasks["LC-KV-29"]["required_repair"])
        self.assertIn("never a hop inside one org", tasks["LC-KV-29"]["required_repair"])
        self.assertNotIn("H-KV-ENDPOINT-LEDGER-ANCHOR", tasks["LC-KV-05"]["items"])

    def test_rev16_withdrawn_path_cannot_be_rebuilt(self):
        # Coordination ruling: no InTr hop inside an org, no LLM-adapter endpoint without an externally established healthy
        # node, no external machine (ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md:53,60), no ledger dispatch
        withdrawn = ("#431", "#235", "llmad431", "llmad432", "llmad433", "org235", "LLM-adapter#432", "LLM-adapter#433")
        plan = json.loads((cli.BASE / "observation-plan.json").read_text())["goals"][KV]
        for k in ("llmad431", "llmad432", "llmad433", "org235"):
            self.assertNotIn(k, plan["roots"])
        for r in plan["runs"]:
            self.assertNotIn(r.get("root"), ("llmad431", "llmad432", "llmad433", "org235"), r["run_id"])
            for w_ in ("#431", "#235", "llmad431", "org235"):
                self.assertNotIn(w_, json.dumps(r), r["run_id"])
        decl = {i["id"]: i for i in _inputs()["declarations"][KV]["items"]}
        anc = json.dumps(decl["H-KV-ENDPOINT-LEDGER-ANCHOR"])
        for w_ in withdrawn:
            self.assertNotIn(w_, anc, w_)
        for w_ in ("#431", "#235"):
            self.assertNotIn(w_, json.dumps(_inputs()["declarations"]), w_)
            for t in _inputs()["tasks"]:
                self.assertNotIn(w_, json.dumps(t), (t["task_id"], w_))
        st = decl["H-KV-ENDPOINT-LEDGER-ANCHOR"]["observed_state"]
        for q_ in ("ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md:53", "and :60", "6392982821", "6393119202", "c6391743862",
                   "SKAP Vault inside KV is the only PII and credential store for every user", "continuity-vault-kit#275"):
            self.assertIn(q_, st, q_)
        self.assertNotIn("merge-ready", anc)
        obs = json.loads((cli.BASE / "observations" / (KV + ".observations.json")).read_text())
        run = next(r for r in obs["runs"] if r["run_id"] == "cvk263-anchor-production-prerequisites")
        self.assertTrue(run["pin"].endswith("@77d28d838ec6714044a192d4f549c3ca9366ff3f"))
        for o in run["outcomes"]:
            self.assertEqual(o["disposition"], "FAIL_CLOSED", o["subject"])
            for k in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
                      "owning_existing_goal", "next_attempt"):
                self.assertTrue(str(o.get(k) or "").strip(), (o["subject"], k))

    def test_kv_admission_lists_no_barred_ephemeral_dependency(self):
        # #167 c6394287652: H-KV-ADMISSION no longer lists the barred EPHEMERAL StegOS#427; no external machine may be a
        # completion requirement (ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md:53,60)
        decl = {i["id"]: i for i in _inputs()["declarations"][KV]["items"]}
        adm = decl["H-KV-ADMISSION"]
        for dep in adm["unadmitted_dependencies"]:
            self.assertNotIn("StegOS#427", dep)
            self.assertNotIn("EPHEMERAL", dep)
        self.assertIn("the EPHEMERAL path is barred", adm["observed_state"])
        conf = json.loads((cli.BASE / "conformance" / (KV + ".conformance.json")).read_text())
        self.assertNotIn("StegOS#427 (NODE_LEDGER_OPENED at EPHEMERAL generation) draft", json.dumps(conf))

    def test_empty_tvc_signer_file_is_a_class_c_tvc_task(self):
        # Name kept from main for the test ratchet (a test at base must run at head).
        # Revision 16: the empty TVC signer file is no longer a class C TVC task; it is the
        # external dependency ORG-LEDGER-HEAD-SIGNER-001, whose key step is owner-only.
        tasks = {t["task_id"]: t for t in _inputs()["tasks"]}
        self.assertIn("ORG-LEDGER-HEAD-SIGNER-001", tasks["LC-KV-13"]["required_repair"])
        t = tasks["LC-KV-13"]
        for k in ("failure_code", "failed_check", "required_repair", "retry_point", "owning_goal", "next_attempt"):
            self.assertTrue(str(t.get(k) or "").strip(), k)
        self.assertNotIn("LC-KV-17", tasks)  # closed in revision 6: cvk#258 @b93b06a4 refuses the unsigned anchor
        for tid in ("LC-KV-07", "LC-KV-08"):
            self.assertTrue(tasks[tid]["owning_lane"].startswith("GitHub Product lane as TV/TVC owner"), tid)
        self.assertIn("72decca1", tasks["LC-KV-07"]["required_repair"])
        self.assertIn("app_store_connect_skap_custody", tasks["LC-KV-08"]["proposed_resolution"])

    def test_rev11_membership_ruling_watermark_and_bindings(self):
        tasks = {t["task_id"]: t for t in _inputs()["tasks"]}
        d = json.loads(cli.build()[KV])
        g = json.loads(cli.build()[GOV])
        decl = {i["id"]: i for i in _inputs()["declarations"][KV]["items"]}
        gdecl = {i["id"]: i for i in _inputs()["declarations"][GOV]["items"]}
        mem = "ENDPOINT_NOT_A_GITHUB_ORGANIZATION_MEMBER"
        # the membership rule is checked on both goals; at cvk#263 @bf684aad the closed schema refuses every form (LC-KV-24 closed)
        self.assertEqual(decl[mem]["kind"], "CONSTRAINT")
        self.assertEqual(gdecl[mem]["kind"], "CONSTRAINT")
        self.assertIn("cvk263-chain-probe", decl[mem]["observed_by"])
        for f_ in ("TOP_LEVEL_ORGANIZATION_KEY", "TOP_LEVEL_GITHUB_APP_INSTALLATION_ID", "TOP_LEVEL_ORG_PERMISSIONS", "TOP_LEVEL_OWNER_ORG",
                   "WATERMARK_SOURCE_VALUE_ORG_LINKED", "WATERMARK_SOURCE_VALUE_OTHER"):
            for w_ in ("KV", "SKAP_VAULT"):
                self.assertEqual(decl[mem]["required_outcomes"]["MEMBERSHIP_%s_%s" % (f_, w_)], ["DENY", "FAIL_CLOSED"])
        self.assertEqual(decl[mem]["required_outcomes"]["PROD_ORG_MEMBERSHIP_KV"], ["ALLOW"])
        # revision 16: no bypass path remains (TVC main @b686a60b refuses every form; the withdrawn designation path is gone)
        self.assertEqual(sorted(set(_codes(d, mem))), ["LADDER_CONSTRAINT_NOT_IN_SEALED_SCOPE"])
        self.assertFalse(decl[mem].get("bypass_paths"))
        self.assertNotIn("LC-KV-25", tasks)
        self.assertEqual(sorted(set(_codes(g, mem))), ["LADDER_CONSTRAINT_NOT_IN_SEALED_SCOPE", "OPERATING_MODE_E0_TERMINAL_MISSING"])
        self.assertNotIn("LC-KV-24", tasks)
        self.assertNotIn("LC-KV-22", tasks)
        self.assertNotIn("LC-KV-23", tasks)  # closed in revision 14 (Coordination ruling (A), #167 c6392982821)
        exp = {"LC-GOV-09": (mem, "LADDER_CONSTRAINT_NOT_IN_SEALED_SCOPE", "C", "GitHub Product lane"),
               "LC-GOV-10": (mem, "OPERATING_MODE_E0_TERMINAL_MISSING", "B", "GitHub Product lane")}
        for tid, (item, code, cls, lane) in exp.items():
            t = tasks[tid]
            self.assertEqual((t["items"], t["failure_code"], t["failure_class"]["class"]), ([item], code, cls), tid)
            self.assertTrue(t["owning_lane"].startswith(lane), tid)
            for k in ("failure_code", "failed_check", "required_repair", "retry_point", "owning_goal", "next_attempt"):
                self.assertTrue(str(t.get(k) or "").strip(), (tid, k))
            self.assertNotIn("merge-ready", json.dumps(t))
        self.assertIn(mem, tasks["LC-KV-09"]["items"])
        self.assertEqual(tasks["LC-KV-09"]["failure_class"]["class"], "A")
        # the provisional membership ruling is quoted where it is applied
        self.assertIn("6373412055", tasks["LC-GOV-10"]["required_repair"])
        # revision 14, Coordination C-review ruling (A) (#167 c6392982821): KV's own head record is the authority and the caller
        # watermark is an optional claim; an older head is DENY whatever the claim, and the claim is still validated on the current head
        anc = decl["H-KV-ENDPOINT-LEDGER-ANCHOR"]
        self.assertIn("cvk263-chain-probe", anc["observed_by"])
        self.assertIn("6392982821", anc["observed_state"])
        ro = anc["required_outcomes"]
        for w_ in ("KV", "SKAP_VIA_GATE"):
            for f_ in ("NONE", "BARE_STRING_NEWEST", "MALFORMED_SHORT", "MALFORMED_UPPERCASE", "ORG_SOURCED", "EXTRA_KEY"):
                self.assertEqual(ro["REPLAY_OLDER_SIGNED_HEAD_WATERMARK_%s_%s" % (f_, w_)], ["DENY"], (f_, w_))
            for f_ in ("KV_OWN_NEWEST", "FOREIGN_DIGEST", "REGRESSED_TO_PRESENTED_HEAD", "ORG_CROSS_CHECK_NEWEST_WITH_REGRESSED_HEAD"):
                self.assertEqual(ro["REPLAY_OLDER_SIGNED_HEAD_WATERMARK_%s_%s" % (f_, w_)], ["DENY", "FAIL_CLOSED"], (f_, w_))
            self.assertEqual(ro["CURRENT_HEAD_WITHOUT_WATERMARK_" + w_], ["ALLOW"])
            self.assertEqual(ro["CURRENT_HEAD_WATERMARK_MATCHED_" + w_], ["ALLOW"])
            self.assertEqual(ro["CURRENT_HEAD_WATERMARK_FOREIGN_DIGEST_" + w_], ["DENY"])
            self.assertEqual(ro["CURRENT_HEAD_HEAD_RECORD_ABSENT_" + w_], ["FAIL_CLOSED"])
            for f_ in ("BARE_STRING", "MALFORMED_SHORT", "MALFORMED_UPPERCASE", "EXTRA_KEY", "ORG_SOURCED"):
                self.assertEqual(ro["CURRENT_HEAD_WATERMARK_%s_%s" % (f_, w_)], ["FAIL_CLOSED"], (f_, w_))
        self.assertEqual(ro["E0_SKAP_READ_BACK_VIA_SKAPLAYER2GATE"], ["ALLOW"])
        self.assertNotIn("SAME_SIGNAL_REPLAYED_AFTER_THE_PIN", ro)  # the withdrawn planner's rows are gone (revision 16)
        wf = {r.get("probe") for r in next(i for i in d["items"] if i["id"] == "H-KV-ENDPOINT-LEDGER-ANCHOR")["refusals"]
              if r["failure_code"] == "OPERATING_MODE_E0_WITNESS_FAILED"}
        self.assertEqual(wf, set())  # every observed watermark row decides as required at @77d28d83 (revision 15)
        # revision 15 (P1, #163): LC-KV-26 closed by continuity-vault-kit#275 @77d28d83 (Coordination 05:03Z via #167
        # c6393119202: "a crossing record held at both ends (the org side and KV's own ledger), never an InTr hop inside one org")
        self.assertIn("6393119202", anc["observed_state"])
        self.assertIn("continuity-vault-kit#275", anc["observed_state"])
        for w_ in ("KV", "SKAP_VIA_GATE"):
            self.assertEqual(ro["LC_KV_26_BOTH_ENDS_KV_END_ONLY_" + w_], ["FAIL_CLOSED"])
            self.assertEqual(ro["LC_KV_26_BOTH_ENDS_ORG_RECORDS_AN_OLDER_HEAD_ONLY_" + w_], ["FAIL_CLOSED"])
            self.assertEqual(ro["LC_KV_26_BOTH_ENDS_ORG_RECORDS_EVERY_HEAD_" + w_], ["ALLOW"])
            self.assertEqual(ro["LC_KV_26_BOTH_ENDS_ROLLBACK_AFTER_LAST_CROSSING_" + w_], ["DENY"])
        obs = json.loads((cli.BASE / "observations" / (KV + ".observations.json")).read_text())
        probe = next(r for r in obs["runs"] if r["run_id"] == "cvk263-chain-probe")
        self.assertTrue(probe["pin"].endswith("@77d28d838ec6714044a192d4f549c3ca9366ff3f"))
        rows = {o["subject"]: o for o in probe["outcomes"]}
        for w_ in ("KV", "SKAP_VIA_GATE"):
            for c_ in ("KV_END_ONLY", "ORG_RECORDS_AN_OLDER_HEAD_ONLY"):
                r_ = rows["LC_KV_26_BOTH_ENDS_%s_%s" % (c_, w_)]
                self.assertEqual((r_["disposition"], r_["failure_code"], r_["failed_predicate"]),
                                 ("FAIL_CLOSED", "KV_CROSSING_RECORD_NOT_OBSERVED", "KV_HEAD_RECORDED_AT_BOTH_ENDS"), (c_, w_))
            self.assertEqual(rows["LC_KV_26_BOTH_ENDS_ROLLBACK_AFTER_LAST_CROSSING_" + w_]["failure_code"],
                             "KV_LEDGER_HEAD_ROLLBACK_DETECTED")
        # live dependency state: cvk#263 merged; revision 16 re-declares the anchor with no unadmitted dependency
        self.assertNotIn("unadmitted_dependencies", anc)
        # revision 15 live-state refresh: merged or superseded dependencies are no longer listed as unadmitted
        adm = " ".join(decl["H-KV-ADMISSION"]["unadmitted_dependencies"]) + " ".join(gdecl["H-GOV-ADMISSION"]["unadmitted_dependencies"])
        for ref_ in ("#3313 ", "#3311 ", "#3255 ", "#3324 ", "continuity-vault-kit#263"):
            self.assertNotIn(ref_, adm, ref_)
        # GitHub Product: TVC does not bind to continuity-vault-kit @77d28d83 (LC-KV-21 A); LC-KV-08 narrowed to one residual, class A
        self.assertEqual(tasks["LC-KV-08"]["failure_class"]["class"], "A")
        self.assertEqual(tasks["LC-KV-07"]["failure_class"]["class"], "B")
        # the provisional runtime rule still replaces 'appended to refs/stegverse/organization-ledger'
        f = tasks["LC-KV-13"]
        self.assertIn("6372680042", f["finish_point_model_conflict_note"])
        self.assertIn("6372680042", tasks["LC-KV-06"]["required_repair"])

    def test_withdrawn_git_ref_custody_adapter_is_not_proposed(self):
        t = next(t for t in _inputs()["tasks"] if t["task_id"] == "LC-KV-03")
        self.assertNotIn("refs/stegverse/kv-custody", t["proposed_resolution"])
        self.assertIn("withdrawn", t["required_repair"])
        for k in ("InTr", "REQUESTER_IS_CURRENTLY_ADMITTED_HEALTHY_NODE", "TV/TVC", "layer-1", "layer-2"):
            self.assertIn(k, t["proposed_resolution"])
        cb = next(i for i in _inputs()["declarations"][KV]["items"] if i["id"] == "H-KV-DURABLE-CUSTODY-PROVIDER")["class_b"]
        self.assertNotIn("refs/stegverse/kv-custody", cb["required_evidence_or_repair"])

    def test_receipt_binds_inputs_code_and_inspected_heads(self):
        for g, text in cli.build().items():
            d = json.loads(text)
            rc = d["receipt"]
            self.assertFalse(rc["runtime_completion"])
            body = {k: v for k, v in d.items() if k != "receipt"}
            self.assertEqual(rc["document_sha256"], lc.sha256_uri(lc.canonical(body)))
            for p in cli.RECEIPT_INPUTS:
                self.assertEqual(rc["code"][p], lc.sha256_uri((ROOT / p).read_bytes()))
            for p, h in rc["inputs"].items():
                self.assertEqual(lc.sha256_uri((ROOT / p).read_bytes()), h, p)
            for k, root in d["inspected"]["roots"].items():
                self.assertRegex(root["commit"], r"^[0-9a-f]{40}$", k)
            for s in d["inspected"]["sources"]:
                self.assertRegex(s["sha256"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(d["authority_effect"], "NONE_CONFORMANCE_RECORD_ONLY")
            self.assertFalse(d["organization_ledger_appended"])

    def test_observed_raw_outputs_hold_no_local_paths(self):
        for p in (lc.BASE / "observations").rglob("*"):
            if p.is_file():
                self.assertNotIn("/workspace/", p.read_text(), p)

    def test_stale_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "lc"
            shutil.copytree(lc.BASE, base)
            p = base / "conformance" / (KV + ".conformance.json")
            p.write_text(p.read_text().replace('"gaps": ', '"gaps": 1', 1))
            self.assertEqual(cli.check(base)["failure_code"], "LADDER_ARTIFACT_STALE")

    def test_tampered_raw_output_is_unbound(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "lc"
            shutil.copytree(lc.BASE, base)
            raw = next((base / "observations" / "raw").glob("kv-finish-point.out"))
            raw.write_text(raw.read_text() + "x")
            self.assertEqual(cli.check(base)["failure_code"], "OPERATING_MODE_E0_WITNESS_UNBOUND")


class Refusals(unittest.TestCase):
    def setUp(self):
        inp = _inputs()
        self.decl = copy.deepcopy(inp["declarations"][KV])
        self.obs = copy.deepcopy(inp["observations"][KV])
        self.tasks = copy.deepcopy(inp["tasks"])
        self.allowed = "CONSENT_RECEIPT_PRECEDES_EVERY_KV_WRITE_AND_READ"  # observed ALLOW at the finish point

    def item(self, item_id):
        return next(i for i in self.decl["items"] if i["id"] == item_id)

    def run_(self):
        return lc.evaluate(self.decl, self.obs, self.tasks)

    def test_baseline_item_is_allow(self):
        self.assertEqual(_verdict(self.run_(), self.allowed), "ALLOW")

    def test_missing_rung_fails_closed(self):
        del self.item(self.allowed)["degraded_forms"]["E2"]
        d = self.run_()
        self.assertEqual(_verdict(d, self.allowed), "FAIL_CLOSED")
        self.assertIn("LADDER_RUNG_FORM_MISSING", _codes(d, self.allowed))

    def test_owner_action_is_deny(self):
        self.item(self.allowed)["owner_actions"] = ["a person approves the write"]
        d = self.run_()
        self.assertEqual(_verdict(d, self.allowed), "DENY")
        self.assertIn("OPERATING_MODE_OWNER_MUST_ACT", _codes(d, self.allowed))

    def test_owner_gate_wording_is_deny_through_the_standard(self):
        self.item(self.allowed)["degraded_forms"]["E1"] = "held for owner merge"
        d = self.run_()
        self.assertEqual(_verdict(d, self.allowed), "DENY")
        self.assertIn("OPERATING_MODE_OWNER_MUST_ACT", _codes(d, self.allowed))

    def test_provider_name_is_deny_through_the_standard(self):
        self.item(self.allowed)["degraded_forms"]["E1"] = "one gemini lane authors"
        self.assertIn("OPERATING_MODE_REQUIRES_SPECIFIC_PROVIDER", _codes(self.run_(), self.allowed))

    def test_more_than_one_llm_is_deny_through_the_standard(self):
        self.item(self.allowed)["requires_llms"] = 2
        self.assertIn("OPERATING_MODE_REQUIRES_MORE_THAN_ONE_LLM", _codes(self.run_(), self.allowed))

    def test_external_machine_is_deny(self):
        self.item(self.allowed)["external_requirements"] = ["/var/lib/stegverse resident root"]
        self.assertEqual(_verdict(self.run_(), self.allowed), "DENY")

    def test_unbound_observation_fails_closed(self):
        self.item(self.allowed)["observed_by"] = ["no-such-run"]
        self.assertIn("OPERATING_MODE_E0_WITNESS_UNBOUND", _codes(self.run_(), self.allowed))

    def test_pin_mismatch_is_unbound(self):
        for r in self.obs["runs"]:
            if r["run_id"] in ("kv-finish-point", "kv-finish-point-tests"):
                r["pin"] = "StegVerse-Labs/continuity-vault-kit@" + "0" * 40
        self.assertIn("OPERATING_MODE_E0_WITNESS_UNBOUND", _codes(self.run_(), self.allowed))

    def test_undeclared_observed_disposition_fails(self):
        for r in self.obs["runs"]:
            if r["run_id"] == "kv-finish-point":
                for o in r["outcomes"]:
                    if o["subject"] == self.allowed:
                        o["disposition"] = "EXCEPTION"
        self.assertIn("OPERATING_MODE_E0_WITNESS_FAILED", _codes(self.run_(), self.allowed))

    def test_non_allow_without_six_fields_fails(self):
        for r in self.obs["runs"]:
            if r["run_id"] == "kv-finish-point":
                for o in r["outcomes"]:
                    if o["subject"] == self.allowed:
                        o["disposition"] = "FAIL_CLOSED"
        self.assertIn("LADDER_E0_TERMINAL_NOT_SIX_FIELD", _codes(self.run_(), self.allowed))

    def test_allow_path_needing_a_code_edit_fails_closed(self):
        self.item(self.allowed)["allow_path"] = {"state": "UNBOUND", "evidence": "constant"}
        self.assertIn("LADDER_ALLOW_PATH_UNBOUND", _codes(self.run_(), self.allowed))

    def test_finish_without_ledger_binding_fails_closed(self):
        self.item(self.allowed)["finish_handoff"] = True
        self.assertIn("LADDER_FINISH_NOT_LEDGER_BOUND", _codes(self.run_(), self.allowed))

    def test_no_e0_terminal_needs_a_six_field_class_b(self):
        it = self.item("H-KV-DURABLE-CUSTODY-PROVIDER")
        del it["class_b"]["next_attempt"]
        self.assertIn("CLASS_B_RECORD_INCOMPLETE", _codes(self.run_(), "H-KV-DURABLE-CUSTODY-PROVIDER"))

    def test_predicate_coverage_is_enforced(self):
        self.decl["items"] = [i for i in self.decl["items"] if i["id"] != self.allowed]
        d = self.run_()
        self.assertIn("LADDER_PREDICATE_COVERAGE", [f["failure_code"] for f in d["consistency_refusals"]])

    def test_gap_without_task_is_a_mismatch(self):
        self.tasks = [t for t in self.tasks if t["failure_code"] != "LADDER_FINISH_NOT_LEDGER_BOUND" or t["goal"] != KV]
        d = self.run_()
        self.assertEqual(d["consistency"], "FAIL_CLOSED")
        self.assertIn("LADDER_SCOPED_TASK_MISMATCH", [f["failure_code"] for f in d["consistency_refusals"]])

    def test_empty_finish_point_is_a_mismatch(self):
        t = next(t for t in self.tasks if t["task_id"] == "LC-KV-13")
        t["finish_point"] = "  "
        d = self.run_()
        self.assertEqual(d["consistency"], "FAIL_CLOSED")
        self.assertIn("LADDER_SCOPED_TASK_MISMATCH", [f["failure_code"] for f in d["consistency_refusals"]])

    def test_task_without_gap_is_a_mismatch(self):
        extra = dict(next(t for t in self.tasks if t["goal"] == KV), task_id="LC-KV-99",
                     failure_code="OPERATING_MODE_OWNER_MUST_ACT")
        self.tasks.append(extra)
        d = self.run_()
        self.assertTrue(any(f["failed_predicate"] == "SCOPED_TASK_COVERS_A_GAP" for f in d["consistency_refusals"]))

    def test_task_missing_a_six_field_is_a_mismatch(self):
        t = next(t for t in self.tasks if t["goal"] == KV)
        t["retry_point"] = ""
        self.assertEqual(self.run_()["consistency"], "FAIL_CLOSED")

    def test_verdict_precedence_deny_over_fail_closed(self):
        it = self.item("KV_PROJECTION_WRITE_READ_REVOKE_ROUNDTRIP_EXACT")
        it["owner_actions"] = ["x"]
        self.assertEqual(_verdict(self.run_(), it["id"]), "DENY")

    def test_bypass_path_is_deny(self):
        self.item(self.allowed)["bypass_paths"] = ["direct read"]
        d = self.run_()
        self.assertEqual(_verdict(d, self.allowed), "DENY")
        self.assertIn("LADDER_ACCESS_PATH_BYPASSES_LAYER", _codes(d, self.allowed))

    def test_collapsed_layers_are_deny(self):
        self.item(self.allowed)["collapsed_layers"] = ["one call mints both"]
        d = self.run_()
        self.assertEqual(_verdict(d, self.allowed), "DENY")
        self.assertIn("LADDER_ACCESS_LAYERS_COLLAPSED", _codes(d, self.allowed))

    def test_constraint_outside_sealed_scope_fails_closed(self):
        it = self.item(self.allowed)
        it["kind"] = "CONSTRAINT"
        self.assertIn("LADDER_CONSTRAINT_NOT_IN_SEALED_SCOPE", _codes(self.run_(), self.allowed))
        it["sealed_scope_includes"] = True
        self.assertNotIn("LADDER_CONSTRAINT_NOT_IN_SEALED_SCOPE", _codes(self.run_(), self.allowed))

    def test_required_outcome_mismatch_missing_and_exception(self):
        it = self.item(self.allowed)
        it["required_outcomes"] = {self.allowed: ["FAIL_CLOSED"]}
        self.assertIn("OPERATING_MODE_E0_WITNESS_FAILED", _codes(self.run_(), self.allowed))
        it["required_outcomes"] = {"NO_SUCH_PROBE": ["FAIL_CLOSED"]}
        self.assertIn("OPERATING_MODE_E0_WITNESS_UNBOUND", _codes(self.run_(), self.allowed))
        it["required_outcomes"] = {self.allowed: ["ALLOW"]}
        self.assertEqual(_verdict(self.run_(), self.allowed), "ALLOW")
        hn = self.item("H-KV-HEALTHY-NODE-DETERMINATION")
        self.assertNotIn("LADDER_E0_TERMINAL_NOT_SIX_FIELD", _codes(self.run_(), hn["id"]))  # #428 returns six fields
        for r in self.obs["runs"]:
            if r["run_id"] == "layer1-healthy-node-probe":
                for o in r["outcomes"]:
                    if o["subject"] == "STANDING_REFUSED":
                        o.clear()
                        o.update({"subject": "STANDING_REFUSED", "disposition": "EXCEPTION", "exception": "StandingRefused"})
        self.assertIn("LADDER_E0_TERMINAL_NOT_SIX_FIELD", _codes(self.run_(), hn["id"]))

    def test_failure_class_is_recorded_and_checked(self):
        d = self.run_()
        prov = next(r for r in d["items"] if r["id"] == "H-KV-DURABLE-CUSTODY-PROVIDER")
        self.assertEqual(prov["failure_class"]["class"], "B")
        self.assertEqual(next(t for t in self.tasks if t["task_id"] == "LC-KV-09")["failure_class"]["class"], "A")
        self.assertEqual(d["consistency"], "ALLOW")
        it = self.item(self.allowed)
        it["failure_class"] = {"class": "B", "reason": "recorded only"}
        self.assertEqual(_verdict(self.run_(), self.allowed), "ALLOW")  # a classification never changes a verdict
        for bad in ({"class": "D", "reason": "x"}, {"class": "B", "reason": " "}, {"class": "B"}, "B",
                    {"class": "B", "reason": "x", "extra": 1}):
            it["failure_class"] = bad
            self.assertIn("LADDER_FAILURE_CLASS_MALFORMED", _codes(self.run_(), self.allowed), bad)
        del it["failure_class"]
        t = next(t for t in self.tasks if t["task_id"] == "LC-KV-09")
        t["failure_class"] = {"class": "Z", "reason": "x"}
        d = self.run_()
        self.assertEqual(d["consistency"], "FAIL_CLOSED")
        self.assertIn("LADDER_SCOPED_TASK_MISMATCH", [f["failure_code"] for f in d["consistency_refusals"]])

    def test_missing_evidence_run_is_unbound(self):
        self.item(self.allowed)["evidence_runs"] = ["no-such-run"]
        self.assertIn("OPERATING_MODE_E0_WITNESS_UNBOUND", _codes(self.run_(), self.allowed))

    def test_tasks_sharing_a_code_must_cover_disjoint_items(self):
        t = copy.deepcopy(next(t for t in self.tasks if t["task_id"] == "LC-KV-27"))
        t["task_id"] = "LC-KV-99"
        self.tasks.append(t)
        self.assertEqual(self.run_()["consistency"], "FAIL_CLOSED")

    def test_allow_path_blockers_are_separate_gaps_with_their_own_tasks(self):
        it = self.item(self.allowed)
        it["allow_path"] = {"state": "UNBOUND", "evidence": "two things", "blockers": [
            {"id": "B1", "evidence": "first"}, {"id": "B2", "evidence": "second"}]}
        tmpl = next(t for t in self.tasks if t["task_id"] == "LC-KV-27")
        for b in ("B1", "B2"):
            self.tasks.append(dict(copy.deepcopy(tmpl), task_id="LC-KV-9" + b[-1], items=[self.allowed], blocker=b))
        d = self.run_()
        res = next(r for r in d["items"] if r["id"] == self.allowed)
        self.assertEqual(sorted(r.get("blocker") for r in res["refusals"]), ["B1", "B2"])
        self.assertEqual(d["consistency"], "ALLOW", d["consistency_refusals"])
        self.tasks = [t for t in self.tasks if t["task_id"] != "LC-KV-92"]  # one blocker uncovered
        self.assertEqual(self.run_()["consistency"], "FAIL_CLOSED")
        self.tasks.append(dict(copy.deepcopy(tmpl), task_id="LC-KV-93", items=[self.allowed], blocker="B1"))
        self.assertEqual(self.run_()["consistency"], "FAIL_CLOSED")  # two tasks on one (item, blocker)

    def test_malformed_blockers_fail_closed(self):
        for bad in ([], [{"id": "B1"}], [{"id": "B1", "evidence": "x"}, {"id": "B1", "evidence": "y"}]):
            self.item(self.allowed)["allow_path"] = {"state": "UNBOUND", "evidence": "x", "blockers": bad}
            self.assertIn("LADDER_ALLOW_PATH_BLOCKER_MALFORMED", _codes(self.run_(), self.allowed))

    def test_external_dependency_ref_is_pending_and_needs_no_scoped_task(self):
        self.item(self.allowed)["external_dependency_refs"] = [{"ref": "X-001", "owner": "Lane X", "evidence": "e"}]
        d = self.run_()
        self.assertEqual(_verdict(d, self.allowed), "FAIL_CLOSED")
        res = next(r for r in d["items"] if r["id"] == self.allowed)
        self.assertEqual([(r["failure_code"], r["external_ref"]) for r in res["refusals"]],
                         [("LADDER_EXTERNAL_DEPENDENCY_PENDING", "X-001")])
        self.assertEqual(d["consistency"], "ALLOW", d["consistency_refusals"])
        t = dict(copy.deepcopy(next(t for t in self.tasks if t["task_id"] == "LC-KV-27")), task_id="LC-KV-99",
                 failure_code="LADDER_EXTERNAL_DEPENDENCY_PENDING", items=[self.allowed])
        self.tasks.append(t)  # the referenced registered task covers it; a scoped task here is a mismatch
        self.assertEqual(self.run_()["consistency"], "FAIL_CLOSED")
        for bad in ([], [{"ref": "X-001", "owner": ""}], [{"ref": "X", "owner": "o", "evidence": "e"}] * 2):
            self.item(self.allowed)["external_dependency_refs"] = bad
            self.assertIn("LADDER_EXTERNAL_DEPENDENCY_REF_MALFORMED", _codes(self.run_(), self.allowed))

    def test_wrong_schema_fails_closed(self):
        self.decl["schema"] = "x"
        self.assertEqual(lc.evaluate(self.decl, self.obs, self.tasks)["failure_code"], "LADDER_DECLARATION_MALFORMED")
        self.decl["schema"] = lc.DECL_SCHEMA
        self.obs["task_id"] = GOV
        self.assertEqual(lc.evaluate(self.decl, self.obs, self.tasks)["failure_code"], "LADDER_OBSERVATIONS_UNBOUND")


class Parsers(unittest.TestCase):
    def test_rows_parser_keeps_each_probe(self):
        out = cli._parse("rows", {}, 0, json.dumps({"rows": [{"subject": "A", "disposition": "ALLOW"},
                                                            {"subject": "B", "disposition": "EXCEPTION"}]}), "")
        self.assertEqual([o["subject"] for o in out], ["A", "B"])

    def test_unittest_parser_records_ran_and_skipped(self):
        out = cli._parse("unittest", {"subject": "S", "on_fail": {}}, 0, "", "....\nRan 4 tests in 0.1s\n\nOK (skipped=1)\n")
        self.assertEqual(out[0]["tests_ran"], 4)
        self.assertEqual(out[0]["skipped"], 1)
        self.assertNotEqual(out[0]["disposition"], "ALLOW")

    def test_disposition_parser_reads_stderr_when_stdout_is_empty(self):
        out = cli._parse("disposition", {"subject": "S"}, 1, "", json.dumps({"disposition": "FAIL_CLOSED"}))
        self.assertEqual(out[0]["disposition"], "FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
