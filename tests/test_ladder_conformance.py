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
        layers = {r["id"]: r for r in d["items"] if r["kind"] == "CONSTRAINT"}
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
        self.assertIn("0eaa1de05320bc72ebb7db16a46431b4133b1b3d", anc["e0_terminal"]["by"])
        # revision 7: the null genesis pin (Lane B) and the EPHEMERAL signer (TV/TVC) are separate blockers of one item;
        # the org-ledger head signer is an external registered task (ORG-LEDGER-HEAD-SIGNER-001), not a scoped task here
        self.assertEqual([b["id"] for b in anc["allow_path"]["blockers"]],
                         ["ORG_GENESIS_PIN_NULL", "GENESIS_OBSERVED_SIGNAL_NOT_CARRIED_BY_ORG_EMITTER",
                          "KV_LEDGER_ON_ORG_LEDGER_REF_MODEL_CONFLICT", "EPHEMERAL_NODE_LEDGER_OPENED_SIGNER_UNPUBLISHED"])
        self.assertEqual([r["ref"] for r in anc["external_dependency_refs"]], ["ORG-LEDGER-HEAD-SIGNER-001"])
        self.assertTrue(anc["external_dependency_refs"][0]["owner"].startswith("GitHub Product lane"))
        self.assertIn("LC-KV-13 finish point (a PERMANENT node) waits on it", anc["external_dependency_refs"][0]["evidence"])
        res = next(r for r in d["items"] if r["id"] == "H-KV-ENDPOINT-LEDGER-ANCHOR")
        self.assertEqual(sorted(r.get("blocker") for r in res["refusals"] if r["failure_code"] == "LADDER_ALLOW_PATH_UNBOUND"),
                         ["EPHEMERAL_NODE_LEDGER_OPENED_SIGNER_UNPUBLISHED", "GENESIS_OBSERVED_SIGNAL_NOT_CARRIED_BY_ORG_EMITTER",
                          "KV_LEDGER_ON_ORG_LEDGER_REF_MODEL_CONFLICT", "ORG_GENESIS_PIN_NULL"])
        self.assertEqual([r["external_ref"] for r in res["refusals"] if r["failure_code"] == "LADDER_EXTERNAL_DEPENDENCY_PENDING"],
                         ["ORG-LEDGER-HEAD-SIGNER-001"])
        for s_ in ("CONTRACT_WITHOUT_GENESIS_PIN", "CONTRACT_GENESIS_PIN_FIELD_ABSENT"):
            self.assertEqual(anc["required_outcomes"][s_], ["FAIL_CLOSED"], s_)
        # revision 8: #431's genesis pin planner and pre-pin receiver are witnessed on the anchor item
        self.assertIn("genesis-pin-probe", anc["observed_by"])
        for s_ in ("SAME_SIGNAL_REPLAYED_AFTER_THE_PIN", "NODE_SIGNAL_GENUINELY_CARRIED_WHILE_PIN_NULL",
                   "FORGED_CARRIER_BODY_IS_ANOTHER_SIGNAL", "PLANNER_DIRECT_AFTER_THE_PIN_OTHER_GENESIS"):
            self.assertEqual(anc["required_outcomes"][s_], ["FAIL_CLOSED"], s_)
        self.assertEqual(anc["required_outcomes"]["PLANNER_DIRECT_AFTER_THE_PIN_SAME_GENESIS"], ["ALLOW"])
        # revision 9: #431 @66a098fa refuses the caller-written genesis on a caller copy (ACCEPTED at 1541d465)
        self.assertEqual(anc["required_outcomes"]["CALLER_WRITTEN_GENESIS_AND_CARRIER_ON_A_CALLER_LEDGER_COPY"], ["FAIL_CLOSED"])
        self.assertNotIn("Observation, not a verdict", anc["observed_state"])
        self.assertIn("6371352606", anc["observed_state"])
        for s_ in ("PERMANENT_ROOT_ON_CALLER_CREATED_ORG_OBJECT_STORE", "CALLER_APPENDED_INGRESS_RECORD_CLAIMING_INSTALLED_INTR",
                   "PERMANENT_CALLER_STORE_AND_CALLER_APPENDED_INGRESS_NO_TRANSPORT_PATCH", "CALLER_STORE_WITH_ITS_OWN_GENESIS",
                   "CALLER_STORE_WITH_THE_ROUTES_ATTESTATION_OF_THE_REAL_STORE_REPLAYED", "PRODUCTION_HEAD_SIGNERS_E0_POSITIVE_CONTROL"):
            self.assertEqual(anc["required_outcomes"][s_], ["FAIL_CLOSED"], s_)
        # the bare evaluator's ALLOW is observational (not the wrapper; KV accepts only the pinned evaluate_anchored)
        self.assertNotIn("PRODUCTION_UNANCHORED_ROOT_VIA_BARE_EVALUATOR", anc["required_outcomes"])
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
        self.assertIn("63705c86a7c6228db5acdbb342d9991bf93b99d5", decl[l2]["bypass_paths"][0])
        # revision 9: TVC#541 @63705c86 takes no caller-minted layer receipts (mint-both tests witnessed as ALLOW = passed);
        # the systemd units naming the legacy root are an external machine on layer 2 (LC-KV-22)
        for s_ in ("TVC541_TEST_P1_MINT_BOTH_IS_FAIL_CLOSED_ON_GATE_READ_THROUGH_AND_PLACE",
                   "TVC541_TEST_P1_MINT_BOTH_BUILD_AND_VALIDATE_FAIL_CLOSED"):
            self.assertEqual(decl[l2]["required_outcomes"][s_], ["ALLOW"], s_)
        self.assertIn("tvc541-mint-both-tests", decl[l2]["observed_by"])
        self.assertIn("LADDER_EXTERNAL_MACHINE_REQUIRED", _codes(d, l2))
        self.assertIn("9 systemd .service units and 1 .path unit", decl[l2]["external_requirements"][0])
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
        m = tasks["LC-KV-21"]  # KV's ledger designated on the org ledger ref: model conflict with Rigel's ruling
        self.assertEqual(m["blocker"], "KV_LEDGER_ON_ORG_LEDGER_REF_MODEL_CONFLICT")
        self.assertEqual(m["items"], ["H-KV-ENDPOINT-LEDGER-ANCHOR"])
        self.assertEqual(m["failure_code"], "LADDER_ALLOW_PATH_UNBOUND")
        self.assertEqual(m["failure_class"]["class"], "B")
        self.assertTrue(m["owning_lane"].startswith("Lane D (KV and WorkSpace) for KV's ledger and endpoint"))
        self.assertIn("Lane B", m["owning_lane"])
        self.assertIn("MODEL CONFLICT", m["required_repair"])
        self.assertIn("f5f971a5", m["required_repair"])
        self.assertIn("accepted existing dependency", m["required_repair"])
        self.assertIn("accepted existing dependency", m["proposed_resolution"])
        self.assertNotIn("merge-ready", json.dumps(m))
        x = tasks["LC-KV-22"]  # systemd units on TVC#541: an external machine
        self.assertEqual((x["disposition"], x["failure_code"], x["failed_check"]),
                         ("DENY", "LADDER_EXTERNAL_MACHINE_REQUIRED", "NO_EXTERNAL_MACHINE"))
        self.assertEqual(x["items"], ["SKAP_VAULT_REACHABLE_ONLY_VIA_INTR_FROM_KV"])
        self.assertEqual(x["failure_class"]["class"], "A")
        self.assertTrue(x["owning_lane"].startswith("GitHub Product lane as TV/TVC owner"))
        for t in (m, x):
            for k in ("failure_code", "failed_check", "required_repair", "retry_point", "owning_goal", "next_attempt"):
                self.assertTrue(str(t.get(k) or "").strip(), k)
        f = next(t for t in _inputs()["tasks"] if t["task_id"] == "LC-KV-13")
        self.assertIn("finish_point_model_conflict_note", f)
        for t in tasks.values():  # every open task carries a class, for the cross-goal blocker list
            self.assertIn(t["failure_class"]["class"], ("A", "B", "C"), t["task_id"])

    def test_empty_tvc_signer_file_is_a_class_c_tvc_task(self):
        tasks = {t["task_id"]: t for t in _inputs()["tasks"]}
        t = tasks["LC-KV-18"]
        self.assertEqual(t["failure_class"]["class"], "C")
        self.assertTrue(t["owning_lane"].startswith("GitHub Product lane as TV/TVC owner"))
        self.assertEqual(t["items"], ["H-KV-ENDPOINT-LEDGER-ANCHOR"])
        self.assertEqual(t["failure_code"], "LADDER_ALLOW_PATH_UNBOUND")
        self.assertIn("ac9a1532102452ea75badc0ee2b902b92cecd1b7", t["required_repair"])
        self.assertIn("node-ledger-opened-signers.v1.json", t["required_repair"])
        self.assertEqual(t["blocker"], "EPHEMERAL_NODE_LEDGER_OPENED_SIGNER_UNPUBLISHED")
        self.assertIn("narrowed back", t["required_repair"])
        self.assertIn("ORG-LEDGER-HEAD-SIGNER-001", t["required_repair"])
        self.assertNotIn("org-ledger-head-signers", t["next_attempt"] + t["proposed_resolution"])
        g = tasks["LC-KV-19"]  # the null org genesis pin: Lane B, next attempt on the genesis-observed record
        self.assertEqual(g["blocker"], "ORG_GENESIS_PIN_NULL")
        self.assertEqual(g["items"], ["H-KV-ENDPOINT-LEDGER-ANCHOR"])
        self.assertTrue(g["owning_lane"].startswith("InTr and Mesh Destinations lane (Lane B"))
        # revision 8: narrowed, the ruling cited (no caveat), the clock question resolved, the copy binding remains
        self.assertEqual(g["failure_class"]["class"], "A")
        self.assertIn("genesis-observed record", g["next_attempt"])
        self.assertIn("REPOSITORY_LEDGER_GENESIS_PIN", g["next_attempt"])
        self.assertIn("66a098fac891a782ad8175d8df3ae07e113a1db7", g["required_repair"])
        self.assertIn("StegVerse-org/.github#162 comment 6371352606", g["required_repair"])
        self.assertNotIn("6371144164", g["required_repair"])
        self.assertNotIn("Observation, not a verdict", g["required_repair"])
        self.assertIn("no clock conflict with LC-GOV-04", g["required_repair"])
        # revision 9: the caller-copy hole is closed in #431 @66a098fa (head attestation by a published signer)
        self.assertIn("caller-written genesis and carrier on a caller copy", g["required_repair"])
        self.assertIn("a caller copy is refused", g["proposed_resolution"])
        e = tasks["LC-KV-20"]  # the org emitter cannot carry the genesis-observed signal
        self.assertEqual(e["blocker"], "GENESIS_OBSERVED_SIGNAL_NOT_CARRIED_BY_ORG_EMITTER")
        self.assertEqual(e["items"], ["H-KV-ENDPOINT-LEDGER-ANCHOR"])
        # revision 9: Coordination's ruling 6371704941: class B, owner Lane B, INTR-PATH-TRANSFER-TYPED-BODY-001
        self.assertTrue(e["owning_lane"].startswith("InTr and Mesh Destinations lane (Lane B"))
        self.assertIn("6371704941", e["owning_lane"])
        self.assertEqual(e["failure_class"]["class"], "B")
        self.assertIn("907f4305ddd4f39b16d96638744304de9ef0b67d", e["required_repair"])
        self.assertIn("69eae86e405fc06f0e1487c6a263765ee1e542a7", e["required_repair"])
        for x in (g, e):
            for k in ("failure_code", "failed_check", "required_repair", "retry_point", "owning_goal", "next_attempt"):
                self.assertTrue(str(x.get(k) or "").strip(), k)
        self.assertIn("ORG-LEDGER-HEAD-SIGNER-001", tasks["LC-KV-13"]["required_repair"])
        for k in ("failure_code", "failed_check", "required_repair", "retry_point", "owning_goal", "next_attempt"):
            self.assertTrue(str(t.get(k) or "").strip(), k)
        self.assertNotIn("LC-KV-17", tasks)  # closed in revision 6: cvk#258 @b93b06a4 refuses the unsigned anchor
        for tid in ("LC-KV-07", "LC-KV-08"):
            self.assertTrue(tasks[tid]["owning_lane"].startswith("GitHub Product lane as TV/TVC owner"), tid)
        self.assertIn("63705c86a7c6228db5acdbb342d9991bf93b99d5", tasks["LC-KV-07"]["required_repair"])

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
        self.assertEqual(next(t for t in self.tasks if t["task_id"] == "LC-KV-09")["failure_class"]["class"], "C")
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
        t = copy.deepcopy(next(t for t in self.tasks if t["task_id"] == "LC-KV-19"))
        t["task_id"] = "LC-KV-99"
        self.tasks.append(t)
        self.assertEqual(self.run_()["consistency"], "FAIL_CLOSED")

    def test_allow_path_blockers_are_separate_gaps_with_their_own_tasks(self):
        it = self.item(self.allowed)
        it["allow_path"] = {"state": "UNBOUND", "evidence": "two things", "blockers": [
            {"id": "B1", "evidence": "first"}, {"id": "B2", "evidence": "second"}]}
        tmpl = next(t for t in self.tasks if t["task_id"] == "LC-KV-19")
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
        t = dict(copy.deepcopy(next(t for t in self.tasks if t["task_id"] == "LC-KV-19")), task_id="LC-KV-99",
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
