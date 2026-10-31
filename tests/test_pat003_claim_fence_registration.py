"""Lane D for Lane A (PAT-003): registration requests, claim drafts and the WRITE_ADMISSION fence, all draft inputs.

Nothing here registers, claims or fences. The plan pins COSV_NOT_DERIVABLE (Lane A owes task.v1 metrics), the allocator
plans each claim draft in a temp tree, and WRITE_ADMISSION decides each fenced surface against the PROPOSED records."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "tests" / "fixtures" / "canonical_task_registration" / "pat-003-lane-a"
MANIFEST = json.loads((FX / "MANIFEST.json").read_text(encoding="utf-8"))
TASKS = ("PAT-003-EVIDENCE", "PAT-003-CHRONOLOGY", "PAT-003-PRIOR-ART")
REPOS = {"StegVerse-Labs/Patents", "StegVerse-Labs/patent-registry"}
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def request(task: str) -> dict:
    return json.loads((FX / f"{task}.request.json").read_text(encoding="utf-8"))


class Registration(unittest.TestCase):
    def test_identities_are_lane_a_proposals_absent_from_the_registry(self):
        registry = json.loads((ROOT / "data" / "canonical-task-registry.json").read_text(encoding="utf-8"))
        ids = {row.get("task_id") for row in registry["tasks"]}
        self.assertEqual([g["task_id"] for g in MANIFEST["goals"]], list(TASKS))
        for goal in MANIFEST["goals"]:
            self.assertNotIn(goal["task_id"], ids)
            self.assertFalse((ROOT / "data" / "canonical-task-records" / f"{goal['task_id']}.json").exists())
            self.assertEqual(goal["identity_provenance"], "PROPOSED_BY_LANE_A")
        self.assertFalse(MANIFEST["registry_edit"] or MANIFEST["registry_generation_bump"] or MANIFEST["ledger_append"])

    def test_targets_name_both_repositories_and_exclude_the_filing_packet(self):
        for task in TASKS:
            req = request(task)
            rec = req["record"]
            self.assertEqual(set(rec["targets"]["repositories"]), REPOS)
            self.assertEqual(rec["coordination_state"], "PROPOSED")
            self.assertEqual(rec["worker_claim"], {"authority": "WORKERCOORDINATOR", "claim_ref": None,
                                                   "fence_ref": None, "projection_only": True})
            named = json.dumps([rec["targets"], rec["source_refs"], rec["existing_evidence_refs"], rec["adjacent_task_refs"]])
            self.assertNotIn("FILING-PACKET", named)  # mentioned in the goal text only as excluded
            self.assertNotIn("human-action-packet", named)
            self.assertEqual(req["authority_effect"], "NONE_REGISTRATION_ONLY")
            proposal = json.loads((ROOT / req["allocation_request_ref"]).read_text(encoding="utf-8"))
            self.assertEqual(proposal["proposed_task_id"], task)
            self.assertIsNone(proposal["cosv_task_vector"])
            self.assertEqual(proposal["proposed_task_id_authority"], "NONE_PROPOSAL_ONLY")
        components = [set(request(t)["record"]["targets"]["components"]) for t in TASKS]
        self.assertFalse(components[0] & components[1] or components[0] & components[2] or components[1] & components[2])

    def test_plan_derives_cosv_as_recorded_and_applies_nothing(self):
        for goal in MANIFEST["goals"]:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "receipt.json"
                subprocess.run([sys.executable, str(ROOT / "scripts" / "canonical_task_registration_transition.py"), "plan",
                                "--request", str(ROOT / goal["request"]), "--base", str(ROOT), "--receipt-out", str(out)],
                               cwd=ROOT, capture_output=True, text=True, check=False)
                receipt = json.loads(out.read_text(encoding="utf-8"))
            expected = goal["expected_plan"]
            self.assertEqual(receipt["disposition"], "ALLOW", (goal["task_id"], receipt))
            evidence = receipt["evidence"]
            for field in ("cosv_task_vector", "scope_digest", "successor_registry_generation", "collision_checkin"):
                self.assertEqual(evidence[field], expected[field], (goal["task_id"], field))
            self.assertEqual(receipt["derived_files"], expected["derived_files"], goal["task_id"])
            self.assertEqual(receipt["request_sha256"], expected["request_sha256"], goal["task_id"])
            self.assertFalse(evidence["allocation"]["proposal_adopted"])
            self.assertIsNone(evidence["allocation"]["proposed_cosv_task_vector"])
            claim = evidence["workercoordinator_claim_request"]
            self.assertIsNone(claim["claim_ref"])
            self.assertIsNone(claim["fence_ref"])
            for flag in ("consequence_committed", "organization_ledger_appended", "execution_authority_minted",
                         "workercoordinator_claim_or_fence_minted", "intr_admission_minted"):
                self.assertFalse(receipt.get(flag, False), (goal["task_id"], flag))
        registry = json.loads((ROOT / "data" / "canonical-task-registry.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["generation"], MANIFEST["observed_registry_generation"])  # nothing applied

    def test_metrics_carry_evidence_and_derive_only_in_the_planner(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        cosv = load_module("cosv_pat003", "scripts/cosv.py")
        for goal in MANIFEST["goals"]:
            vector = request(goal["task_id"])["vector"]
            self.assertNotIn("vector", vector)
            self.assertEqual(set(vector["exact_metrics"]) - {"symbol_order"}, set(cosv.TASK_FIELDS))
            self.assertEqual(set(vector["metric_evidence"]), set(cosv.TASK_FIELDS))
            for field, text in vector["metric_evidence"].items():
                self.assertIn("Lane D", text, (goal["task_id"], field))
            self.assertIn(goal["metrics_source"]["ref"], vector["evidence_refs"])

    def test_finish_points_are_lane_a_replacements_with_handoffs_outside(self):
        for goal in MANIFEST["goals"]:
            rec = request(goal["task_id"])
            fp = rec["sealed_scope"]["scope"]["finish_point"]
            self.assertNotIn("unresolved_items no longer lists", fp["predicate"])
            self.assertIn("never READY_TO_FILE", fp["predicate"])
            verifier = goal["verifier"]
            self.assertIn(f"StegVerse-Labs/Patents/{verifier['entrypoint']}@{verifier['commit']}", fp["verifier_entrypoint"])
            self.assertIn(verifier["entrypoint_sha256"], fp["verifier_entrypoint"])
            self.assertIn("UNADMITTED", fp["verifier_entrypoint"])
            self.assertNotIn("NOT_IMPLEMENTED", fp["verifier_entrypoint"])
            kinds = {(d["dependency_id"], d["kind"], d["state"]) for d in rec["record"]["dependencies"]}
            self.assertIn(("PAT_003_OWNER_OR_PRACTITIONER_CHECK_OFF", "HUMAN_ACTION", "UNRESOLVED"), kinds)
            self.assertIn(("PAT_003_STRUCTURAL_VERIFIER_ADMISSION", "CAPABILITY", "UNRESOLVED"), kinds)
            dep = next(d for d in rec["record"]["dependencies"] if d["dependency_id"] == "PAT_003_STRUCTURAL_VERIFIER_ADMISSION")
            self.assertIn("pending admission of StegVerse-Labs/Patents#23", dep["ref"])
            self.assertIn(verifier["commit"], dep["ref"])
            self.assertEqual(verifier["admission_state"], "UNADMITTED_DRAFT_PR_DEPENDENCY_NOT_ALLOW")
            self.assertEqual(goal["pinned_heads"]["Patents#23"], verifier["commit"])

    def test_fe2_primary_clip_is_six_field_fail_closed_class_c(self):
        evidence = next(g for g in MANIFEST["goals"] if g["task_id"] == "PAT-003-EVIDENCE")
        self.assertEqual(evidence["pinned_heads"]["Patents#21"], "e31f7263bb72645f2d684a95517547c930139d6a")
        self.assertEqual(evidence["pinned_heads"]["Patents#22"], "ffaec698ba49fc2d11cabfd6cfdf73f13534f7ae")
        [item] = evidence["fail_closed"]
        self.assertEqual((item["class"], item["failure_code"]), ("C", "FE2_PRIMARY_CLIP_POINTER_NOT_HASHED"))
        for field in SIX:
            self.assertTrue(item.get(field), field)
        self.assertIn("KV-8", item["failed_predicate"])
        rec = request("PAT-003-EVIDENCE")["record"]
        dep = next(d for d in rec["dependencies"] if d["dependency_id"] == "PAT_003_PRIMARY_DEMONSTRATION_INPUT_EXPORT")
        self.assertEqual((dep["kind"], dep["state"]), ("HUMAN_ACTION", "UNRESOLVED"))
        for pin in ("e31f7263bb72645f2d684a95517547c930139d6a", "ffaec698ba49fc2d11cabfd6cfdf73f13534f7ae"):
            self.assertIn(pin, dep["ref"])
        for other in ("PAT-003-CHRONOLOGY", "PAT-003-PRIOR-ART"):
            goal = next(g for g in MANIFEST["goals"] if g["task_id"] == other)
            self.assertEqual(goal["fail_closed"], [])
            ids = {d["dependency_id"] for d in request(other)["record"]["dependencies"]}
            self.assertNotIn("PAT_003_PRIMARY_DEMONSTRATION_INPUT_EXPORT", ids)

    def test_scope_seal_holds_for_the_record(self):
        gss = load_module("goal_scope_seal_pat003", "scripts/goal_scope_seal.py")
        for goal in MANIFEST["goals"]:
            req = request(goal["task_id"])
            scope = gss.scope_of(req["record"], req["sealed_scope"]["scope"]["finish_point"])
            self.assertEqual(gss.digest(scope), goal["scope_digest"])
            self.assertEqual(req["sealed_scope"]["scope_digest"], goal["scope_digest"])


class ClaimFence(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        for rel in ("scripts", "tasks", "control"):
            shutil.copytree(ROOT / rel, self.tmp / rel)
        (self.tmp / "events").mkdir(exist_ok=True)
        for task in TASKS:
            draft = json.loads((FX / f"{task}.claim-draft.json").read_text(encoding="utf-8"))
            self.assertEqual(draft["task_id"], "ALLOCATOR_TASK_ID_NOT_ASSIGNED")
            self.assertEqual({r["repository"]["full_name"] for r in draft["requirements"]["mandatory"]}, REPOS)
            draft["task_id"] = f"TASK-SCRATCH-{task}"
            (self.tmp / "tasks" / f"TASK-SCRATCH-{task}.json").write_text(json.dumps(draft), encoding="utf-8")

    def allocate(self, *args: str) -> dict:
        proc = subprocess.run([sys.executable, str(self.tmp / "scripts" / "allocate_claims.py"), *args],
                              cwd=self.tmp, capture_output=True, text=True, check=False)
        return json.loads(proc.stdout or proc.stderr)

    def test_each_claim_draft_plans_and_the_three_co_hold(self):
        generation = json.loads((ROOT / "control" / "claims-active.json").read_text(encoding="utf-8"))["generation"]
        for task in TASKS:
            plan = self.allocate("--plan", "--task", f"TASK-SCRATCH-{task}")
            self.assertEqual((plan["state"], plan["refusal_predicate"]), ("ALLOCATION_PLANNED", None), plan)
            self.assertEqual(plan["authority_effect"], "NONE_PLAN_ONLY")
        for offset, task in enumerate(TASKS, start=1):
            done = self.allocate("--task", f"TASK-SCRATCH-{task}", "--fencing-token", str(generation + offset))
            self.assertEqual((done["state"], done["refusal_predicate"]), ("ALLOCATION_COMPLETE", None), done)
        held = json.loads((self.tmp / "control" / "claims-active.json").read_text(encoding="utf-8"))
        tokens = {c["task_id"]: c["lease"]["fencing_token"] for c in held["claims"]
                  if c["repository"]["full_name"] == "StegVerse-Labs/Patents"}
        self.assertEqual(sorted(tokens.values()), [generation + 1, generation + 2, generation + 3])
        # the real claims registry is untouched
        self.assertEqual(json.loads((ROOT / "control" / "claims-active.json").read_text(encoding="utf-8"))["generation"], generation)

    def test_fenced_paths_are_disjoint_and_exist_in_the_handoff_inventory(self):
        paths = [set(json.loads((FX / f"{t}.claim-draft.json").read_text(encoding="utf-8"))["requirements"]["mandatory"][0]
                     ["scope"]["paths"]) for t in TASKS]
        self.assertFalse(paths[0] & paths[1] or paths[0] & paths[2] or paths[1] & paths[2])
        joined = set().union(*paths)
        self.assertNotIn("reviews/PAT-003-human-action-packet.md", joined)
        self.assertNotIn("data/active-family-prior-art-identifiers.json", joined)


class WriteAdmission(unittest.TestCase):
    def test_cases_decide_as_recorded(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        wa = load_module("write_admission_pat003", "scripts/write_admission.py")
        graph = wa.seal_graph([request(t)["record"] for t in TASKS])
        doc = json.loads((FX / "write-admission-cases.json").read_text(encoding="utf-8"))
        self.assertTrue(doc["cases"])
        for case in doc["cases"]:
            body = wa.evaluate(case["surface"], case["work_item"], graph, doc["active_work"])
            self.assertEqual(body["disposition"], case["expected_disposition"], (case["case"], body))
            self.assertEqual(body["ledger_status"], "SCRATCH_NOT_A_LEDGER_RECEIPT")
            if case["expected_failure_code"]:
                self.assertEqual(body["failure_code"], case["expected_failure_code"], case["case"])
                for field in SIX:
                    self.assertTrue(body.get(field), (case["case"], field))


if __name__ == "__main__":
    unittest.main()
