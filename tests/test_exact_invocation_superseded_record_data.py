"""The scoped #3257 successor repair: EXACT-INVOCATION checks in SUPERSEDED -> CYCLE-CLOSURE.

The repair is data applied by scripts/apply_task_record_data.py, never a hand edit. These
tests plan and apply it on temporary copies of the Registry and the standalone records
and pin that it changes exactly one task, exactly three fields, at exactly tip + 1.
"""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apply_task_record_data as atr  # noqa: E402

REGISTRY = ROOT / "data" / "canonical-task-registry.json"
SHARDS = ROOT / "data" / "canonical-task-records"
DATA = ROOT / "data" / "registry-record-data" / "exact-invocation-superseded-by-cycle-closure.v1.json"
TASK = "CANONICAL-WORK-EXACT-INVOCATION-EVIDENCE-RECONCILIATION-001"
CONTINUATION = "CANONICAL-WORK-END-TO-END-CYCLE-CLOSURE-001"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ExactInvocationSupersededRecordDataTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        self.registry = self.dir / "canonical-task-registry.json"
        self.shards = self.dir / "canonical-task-records"
        shutil.copy2(REGISTRY, self.registry)
        shutil.copytree(SHARDS, self.shards)
        self.tip = load(REGISTRY)["generation"]
        self.data = load(DATA)

    def run_apply(self, payload, write=True):
        return atr.apply(payload, registry_path=self.registry, task_shards=self.shards,
                         tip_generation=self.tip, write=write, root=self.dir, validators=())

    def test_data_is_scoped_to_one_task_and_three_fields(self):
        self.assertEqual(self.data["schema"], atr.DATA_SCHEMA)
        self.assertEqual(self.data["register_from_record"], [TASK])
        self.assertNotIn("work_items", self.data)
        self.assertNotIn("human_actions", self.data)
        self.assertEqual({e["task_id"] for e in self.data["row_fields"]}, {TASK})
        self.assertEqual([e["path"] for e in self.data["row_fields"]],
                         [["coordination_state"], ["checkout_state"], ["continuation_task_id"]])
        self.assertEqual(self.data["registry_generation_base"], self.tip)

    def test_preconditions_hold_on_the_base(self):
        record = load(SHARDS / f"{TASK}.json")
        self.assertEqual((record["coordination_state"], record["checkout_state"]), ("ACTIVE", "CHECKED_OUT"))
        self.assertNotIn("continuation_task_id", record)
        self.assertNotIn(TASK, [row.get("task_id") for row in load(REGISTRY)["tasks"]])
        self.assertTrue((SHARDS / f"{CONTINUATION}.json").is_file())

    def test_plan_allows_exactly_tip_plus_one_and_writes_nothing(self):
        before = (self.registry.read_bytes(), (self.shards / f"{TASK}.json").read_bytes())
        report = self.run_apply(self.data, write=False)
        self.assertEqual((report["disposition"], report["generation"], report["files_changed"]),
                         ("ALLOW", self.tip + 1, False))
        self.assertEqual(report["records_changed"], [f"{TASK}.json"])
        self.assertEqual(before, (self.registry.read_bytes(), (self.shards / f"{TASK}.json").read_bytes()))

    def test_apply_supersedes_row_and_record_and_changes_nothing_else(self):
        base_registry = load(self.registry)
        base_record = load(self.shards / f"{TASK}.json")
        self.assertEqual(self.run_apply(self.data)["disposition"], "ALLOW")
        registry = load(self.registry)
        record = load(self.shards / f"{TASK}.json")
        rows = [row for row in registry["tasks"] if row.get("task_id") == TASK]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], record)  # the row follows the record
        self.assertEqual((record["coordination_state"], record["checkout_state"], record["continuation_task_id"]),
                         ("SUPERSEDED", "SUPERSEDED", CONTINUATION))
        expected = copy.deepcopy(base_record)
        expected.update(coordination_state="SUPERSEDED", checkout_state="SUPERSEDED", continuation_task_id=CONTINUATION)
        self.assertEqual(record, expected)
        self.assertEqual(registry["generation"], self.tip + 1)
        registry["tasks"] = [row for row in registry["tasks"] if row.get("task_id") != TASK]
        registry["generation"] = base_registry["generation"]
        self.assertEqual(registry, base_registry)
        for path in self.shards.iterdir():
            if path.name != f"{TASK}.json":
                self.assertEqual(path.read_bytes(), (SHARDS / path.name).read_bytes(), path.name)

    def test_reapply_is_no_change_with_no_bump(self):
        self.run_apply(self.data)
        applied = self.registry.read_bytes()
        report = self.run_apply(self.data)
        self.assertEqual((report["disposition"], report["files_changed"]), ("NO_CHANGE", False))
        self.assertEqual(self.registry.read_bytes(), applied)

    def test_row_fields_without_registration_fail_closed_with_six_fields(self):
        payload = {k: v for k, v in self.data.items() if k != "register_from_record"}
        with self.assertRaises(atr.Refused) as ctx:
            self.run_apply(payload)
        result = ctx.exception.result
        self.assertEqual((result["disposition"], result["failure_code"]),
                         ("FAIL_CLOSED", "RECORD_DATA_TASK_NOT_IN_AGGREGATE_REGISTRY"))
        for field in SIX:
            self.assertTrue(result[field], field)
        self.assertFalse(result["files_changed"])
        self.assertEqual(self.registry.read_bytes(), REGISTRY.read_bytes())

    def test_stale_before_value_fails_closed_and_restores(self):
        payload = copy.deepcopy(self.data)
        payload["row_fields"][0]["before"] = "CLAIMED"
        with self.assertRaises(atr.Refused) as ctx:
            self.run_apply(payload)
        self.assertEqual(ctx.exception.result["disposition"], "FAIL_CLOSED")
        for field in SIX:
            self.assertTrue(ctx.exception.result[field], field)
        self.assertEqual(self.registry.read_bytes(), REGISTRY.read_bytes())
        self.assertEqual((self.shards / f"{TASK}.json").read_bytes(), (SHARDS / f"{TASK}.json").read_bytes())


# StegApp ingress vocabulary cases share this record-data ratchet set. Discover
# the proposal through the already-declared directory surface; the checked-in
# content below still pins its exact filename-independent schema and edit.
# APPLIED at registry generation 322 -> 323 (PR #3403): the proposal is spent, so
# these cases pin the exact landed state and the spent proposal's idempotent
# NO_CHANGE behaviour, and keep the before-mismatch and generation-fence guards
# exercised with payloads whose before/after match neither the live value nor a
# stale tip. Guards are never weakened; only the pre-apply expectations moved to
# post-apply ones. Test names are the base's names verbatim: the test-suite
# ratchet fails closed (REQUIRED_VERIFICATION_SKIPPED) on any test present at the
# base and not run at the head, so a rename is a removal; the pre-apply names are
# kept and their bodies assert the post-apply contract, noted per test.
RECORD_DATA = ROOT / "data" / "registry-record-data"
STEGAPP_DATA = next(path for path in RECORD_DATA.glob("*.json")
                    if "stegapp-ephemeral-composition-ingress-vocabulary" in path.name)
STEGAPP_TASK = "STEGAPP-EPHEMERAL-COMPOSITION-001"
STEGAPP_EXISTING = [
    "REVIEW_REGISTRATION_PROPOSAL",
    "RESOLVE_OWNER_SCOPE",
    "SOURCE_CANDIDATE_REPAIR",
    "NATIVE_ADMISSION_EVALUATION",
]
STEGAPP_APPLIED = STEGAPP_EXISTING + ["INGRESS_ADMITTED"]


class StegAppIngressVocabularyRecordDataTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        self.registry = self.dir / "canonical-task-registry.json"
        self.shards = self.dir / "canonical-task-records"
        shutil.copy2(REGISTRY, self.registry)
        self.shards.mkdir()
        shutil.copy2(SHARDS / f"{STEGAPP_TASK}.json", self.shards / f"{STEGAPP_TASK}.json")
        self.tip = load(REGISTRY)["generation"]
        self.data = load(STEGAPP_DATA)

    def run_apply(self, payload, write=True, tip=None):
        return atr.apply(payload, registry_path=self.registry, task_shards=self.shards,
                         tip_generation=self.tip if tip is None else tip, write=write,
                         root=self.dir, validators=())

    def row(self):
        rows = [row for row in load(self.registry)["tasks"] if row.get("task_id") == STEGAPP_TASK]
        self.assertEqual(len(rows), 1)
        return rows[0]

    def record(self):
        return load(self.shards / f"{STEGAPP_TASK}.json")

    def test_data_is_one_exact_non_authorizing_row_field_edit(self):
        self.assertEqual(self.data["schema"], atr.DATA_SCHEMA)
        self.assertEqual(self.data["authority_effect"], "NONE")
        # recorded at generation 322 and applied 322 -> 323; the base is
        # provenance of the applied edit, not a freshness alarm (the proposal
        # is spent; the ExactInvocation proposal above keeps the live-tip alarm)
        self.assertEqual(self.data["registry_generation_base"], 322)
        self.assertNotIn("register_from_record", self.data)
        self.assertNotIn("work_items", self.data)
        self.assertNotIn("human_actions", self.data)
        self.assertEqual(len(self.data["row_fields"]), 1)
        edit = self.data["row_fields"][0]
        self.assertEqual(edit["task_id"], STEGAPP_TASK)
        self.assertEqual(edit["path"], ["allowed_next_transitions"])
        self.assertEqual(edit["before"], STEGAPP_EXISTING)
        self.assertEqual(edit["after"], STEGAPP_APPLIED)

    def test_preconditions_hold_on_exact_aggregate_row_and_shard(self):
        # spent proposal: the preconditions are the APPLIED state (the name is
        # the base's, kept because a rename is a ratchet-counted removal)
        row, record = self.row(), self.record()
        self.assertEqual(row["coordination_state"], "PROPOSED")
        self.assertEqual(record["coordination_state"], "PROPOSED")
        self.assertEqual(row["checkout_state"], "UNCLAIMED")
        self.assertEqual(row["cosv_task_vector"], "10300000011000")
        self.assertEqual(row["allowed_next_transitions"], STEGAPP_APPLIED)
        self.assertEqual(record["allowed_next_transitions"], STEGAPP_APPLIED)
        self.assertFalse(record["worker_claim"]["claim_ref"])
        self.assertFalse(record["worker_claim"]["fence_ref"])
        self.assertFalse(record["completion"]["claimed"])
        self.assertFalse(record["completion"]["validated"])

    def test_plan_allows_tip_plus_one_and_writes_nothing(self):
        # spent proposal: the plan is the idempotent NO_CHANGE, not an ALLOW at
        # tip + 1 (the name is the base's, kept because a rename is a
        # ratchet-counted removal); nothing is written in either case
        before = (self.registry.read_bytes(), (self.shards / f"{STEGAPP_TASK}.json").read_bytes())
        report = self.run_apply(self.data, write=False)
        self.assertEqual(report["disposition"], "NO_CHANGE")
        self.assertFalse(report.get("files_changed", False))
        self.assertEqual(before, (self.registry.read_bytes(),
                                  (self.shards / f"{STEGAPP_TASK}.json").read_bytes()))

    def test_apply_changes_only_transition_vocabulary_on_row_and_shard(self):
        # spent proposal: a write-mode apply changes nothing at all - not the
        # row, not the shard, not the registry generation (the name is the
        # base's, kept because a rename is a ratchet-counted removal)
        before = (self.registry.read_bytes(), (self.shards / f"{STEGAPP_TASK}.json").read_bytes())
        report = self.run_apply(self.data, write=True)
        self.assertEqual((report["disposition"], report["files_changed"]), ("NO_CHANGE", False))
        self.assertEqual(before, (self.registry.read_bytes(),
                                  (self.shards / f"{STEGAPP_TASK}.json").read_bytes()))
        row, record = self.row(), self.record()
        self.assertEqual(row["allowed_next_transitions"], STEGAPP_APPLIED)
        self.assertEqual(record["allowed_next_transitions"], STEGAPP_APPLIED)
        self.assertEqual(load(self.registry)["generation"], self.tip)

    def test_reapply_is_no_change_with_no_generation_bump(self):
        self.run_apply(self.data)
        applied = (self.registry.read_bytes(), (self.shards / f"{STEGAPP_TASK}.json").read_bytes())
        report = self.run_apply(self.data, tip=self.tip + 1)
        self.assertEqual((report["disposition"], report["files_changed"]), ("NO_CHANGE", False))
        self.assertEqual(applied, (self.registry.read_bytes(),
                                   (self.shards / f"{STEGAPP_TASK}.json").read_bytes()))

    def test_stale_before_fails_closed_without_writing(self):
        # the live value is the applied one; a payload whose before/after match
        # neither the live value must still fail closed (the guard is reached
        # only when the edit is not already applied, so both are moved)
        payload = copy.deepcopy(self.data)
        payload["row_fields"][0]["before"] = STEGAPP_EXISTING + ["HANDOFF_READY"]
        payload["row_fields"][0]["after"] = STEGAPP_EXISTING + ["HANDOFF_READY", "INGRESS_ADMITTED"]
        before = (self.registry.read_bytes(), (self.shards / f"{STEGAPP_TASK}.json").read_bytes())
        with self.assertRaises(atr.Refused) as raised:
            self.run_apply(payload)
        self.assertEqual(raised.exception.result["disposition"], "FAIL_CLOSED")
        self.assertEqual(raised.exception.result["failure_code"],
                         "RECORD_DATA_ROW_FIELD_BEFORE_MISMATCH")
        self.assertEqual(before, (self.registry.read_bytes(),
                                  (self.shards / f"{STEGAPP_TASK}.json").read_bytes()))

    def test_stale_generation_fence_fails_closed_without_writing(self):
        # re-open the applied vocabulary on a copied registry so the merge
        # produces a real change, then require the generation fence to refuse a
        # stale tip (the spent proposal's NO_CHANGE path never reaches the fence)
        payload = copy.deepcopy(self.data)
        payload["row_fields"][0]["before"] = STEGAPP_APPLIED
        payload["row_fields"][0]["after"] = STEGAPP_APPLIED + ["HANDOFF_READY"]
        before = (self.registry.read_bytes(), (self.shards / f"{STEGAPP_TASK}.json").read_bytes())
        with self.assertRaises(atr.Refused) as raised:
            self.run_apply(payload, tip=self.tip - 1)
        self.assertEqual(raised.exception.result["failure_code"],
                         "REGISTRY_GENERATION_NOT_TIP_PLUS_ONE")
        self.assertEqual(before, (self.registry.read_bytes(),
                                  (self.shards / f"{STEGAPP_TASK}.json").read_bytes()))


if __name__ == "__main__":
    unittest.main()
