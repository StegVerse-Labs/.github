"""Source-only tests for the Exp3 task-vector durable queue entry (B-P4).

The readback used here is a synthetic fixture marked _fixture_not_evidence. It
is never evidence: no organization receipt exists until StegVerse-org/.github#198
is merged and the ledger append is read back.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import materialize_mir_exp3_task_vector_from_org_receipt as mod
from scripts.validate_transition_disposition import non_allow_missing

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/mir-exp3/org-ledger-readback.fixture.json"
COMMIT = "2" * 40


def vector():
    return json.loads((ROOT / mod.VECTOR_REL).read_text(encoding="utf-8"))


def readback(**changes):
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    value.update(changes)
    return value


class QueueEntryTests(unittest.TestCase):
    def setUp(self):
        self.entry = json.loads((ROOT / mod.QUEUE_REL).read_text(encoding="utf-8"))

    def test_entry_uses_existing_durable_request_mechanism(self):
        self.assertEqual(self.entry["schema"], "stegverse.resident-execution-request/v1")
        self.assertEqual(self.entry["state"], "REQUESTED")
        self.assertEqual(self.entry["receiver_unavailable_disposition"],
                         "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION")
        self.assertTrue(self.entry["event_triggered"])
        for key in ("always_on_receiver_required", "external_machine_awaited",
                    "second_machine_required", "master_records_awaited",
                    "request_grants_execution_authority", "claim_or_fence_minted_by_request",
                    "receipt_claimed"):
            self.assertIs(self.entry[key], False, key)
        self.assertEqual(self.entry["evidence_class"], "SOURCE_IMPLEMENTED")

    def test_entry_binds_the_script_trigger_and_transition(self):
        self.assertEqual(self.entry["entrypoint"], mod.ENTRYPOINT)
        self.assertEqual(self.entry["task_id"], mod.GOAL)
        self.assertEqual(self.entry["cosv_task_vector"], mod.COSV)
        transition, trigger = self.entry["transition"], self.entry["trigger"]
        self.assertEqual(transition["target_ref"], str(mod.VECTOR_REL))
        self.assertEqual((transition["from_state"], transition["to_state"]),
                         (mod.FROM_STATE, mod.TO_STATE))
        self.assertEqual(trigger["canonical_manifest_sha256"], mod.CANONICAL_MANIFEST_SHA256)
        self.assertEqual(trigger["organization_transition_id"], mod.ORGANIZATION_TRANSITION_ID)
        self.assertEqual(trigger["organization_ledger_ref"], mod.LEDGER_REF)
        bound = self.entry["binds_receipt_fields"]
        for key, expected in mod.BOUND_RECEIPT_FIELDS.items():
            self.assertIn(key, bound)
            if expected is not None:
                self.assertEqual(bound[key], expected, key)

    def test_vector_is_still_source_only_active(self):
        self.assertEqual(vector()["vector_state"], mod.FROM_STATE)

    def test_current_disposition_is_six_field_fail_closed(self):
        current = self.entry["current_disposition"]
        self.assertEqual(current["disposition"], "FAIL_CLOSED")
        self.assertEqual(current["failure_code"], "ORGANIZATION_RECEIPT_NOT_APPENDED")
        self.assertEqual(current["next_attempt"],
                         "on org#198 merge; materialized from the receipt readback")
        self.assertIs(current["consequence_committed"], False)
        self.assertEqual(non_allow_missing(current), [])
        expected = mod.pending()
        for key in ("failure_code", "failed_predicate", "retry_entrypoint",
                    "owning_existing_goal", "next_attempt", "required_evidence_or_repair"):
            self.assertEqual(current[key], expected[key], key)


class MaterializationTests(unittest.TestCase):
    def test_pending_without_readback(self):
        got = mod.pending()
        self.assertEqual(got["disposition"], "FAIL_CLOSED")
        self.assertEqual(non_allow_missing(got), [])

    def test_fixture_is_refused_without_explicit_test_flag(self):
        got = mod.materialize(vector(), readback(), COMMIT)
        self.assertEqual(got["failure_code"], "ORGANIZATION_RECEIPT_IS_FIXTURE")
        self.assertEqual(non_allow_missing(got), [])

    def test_fixture_materializes_as_synthetic_only(self):
        source = vector()
        got = mod.materialize(source, readback(), COMMIT, allow_fixture=True)
        self.assertEqual(got["disposition"], "ALLOW")
        self.assertEqual(got["evidence_class"], "SYNTHETIC_TEST")
        self.assertTrue(got["fixture_only"])
        updated = got["vector"]
        self.assertEqual(updated["vector_state"], mod.TO_STATE)
        self.assertEqual(updated["authority_effect"], "NONE")
        transition = updated["state_transition"]
        self.assertEqual(transition["from_state"], mod.FROM_STATE)
        self.assertEqual(transition["organization_transition_id"], mod.ORGANIZATION_TRANSITION_ID)
        self.assertEqual(transition["canonical_manifest_sha256"], mod.CANONICAL_MANIFEST_SHA256)
        self.assertEqual(transition["organization_ledger_commit"], COMMIT)
        self.assertIn("StegVerse-org/.github@refs/stegverse/organization-ledger:" + COMMIT
                      + ":receipts/" + "1" * 64 + ".json", updated["evidence_refs"])
        self.assertEqual(source["vector_state"], mod.FROM_STATE)  # input not mutated

    def test_replay_of_same_receipt_is_idempotent(self):
        first = mod.materialize(vector(), readback(), COMMIT, allow_fixture=True)["vector"]
        again = mod.materialize(first, readback(), COMMIT, allow_fixture=True)
        self.assertEqual(again["state"], "ALREADY_MATERIALIZED")
        other = mod.materialize(first, readback(ingress_organization_receipt_sha256="3" * 64),
                                COMMIT, allow_fixture=True)
        self.assertEqual(other["failure_code"],
                         "TASK_VECTOR_ALREADY_MATERIALIZED_FROM_ANOTHER_RECEIPT")

    def test_canonical_mismatch_is_refused_with_six_fields(self):
        got = mod.materialize(vector(), readback(canonical_manifest_sha256="0" * 64),
                              COMMIT, allow_fixture=True)
        self.assertEqual(got["disposition"], "FAIL_CLOSED")
        self.assertEqual(got["failure_code"], "ORGANIZATION_RECEIPT_CANONICAL_MISMATCH")
        self.assertIs(got["consequence_committed"], False)
        self.assertEqual(non_allow_missing(got), [])
        self.assertNotIn("vector", got)

    def test_transition_id_mismatch_is_refused_with_six_fields(self):
        got = mod.materialize(
            vector(), readback(organization_transition_id="ORGANIZATION-SDK-MANIFEST-INGRESS-0000000000000000"),
            COMMIT, allow_fixture=True)
        self.assertEqual(got["failure_code"], "ORGANIZATION_RECEIPT_TRANSITION_ID_MISMATCH")
        self.assertEqual(non_allow_missing(got), [])
        self.assertNotIn("vector", got)

    def test_refused_or_unbound_readbacks_are_refused(self):
        for changes in ({"disposition": "FAIL_CLOSED"}, {"ingress_refused": True},
                        {"ingress_receipt_bound_to_manifest": False},
                        {"master_records_awaited": True},
                        {"ingress_organization_receipt_sha256": "not-hex"},
                        {"schema": "other"}):
            got = mod.materialize(vector(), readback(**changes), COMMIT, allow_fixture=True)
            self.assertEqual(got["disposition"], "FAIL_CLOSED", changes)
            self.assertEqual(non_allow_missing(got), [], changes)

    def test_bad_ledger_commit_and_wrong_source_state_are_refused(self):
        got = mod.materialize(vector(), readback(), "abc", allow_fixture=True)
        self.assertEqual(got["failure_code"], "ORGANIZATION_LEDGER_COMMIT_INVALID")
        wrong = dict(vector(), vector_state="UNKNOWN")
        got = mod.materialize(wrong, readback(), COMMIT, allow_fixture=True)
        self.assertEqual(got["failure_code"], "TASK_VECTOR_NOT_IN_SOURCE_STATE")

    def test_cli_never_writes_from_a_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / mod.VECTOR_REL
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(vector()), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(ROOT / mod.ENTRYPOINT), "--root", str(root),
                 "--readback", str(FIXTURE), "--ledger-commit", COMMIT, "--write"],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(json.loads(target.read_text())["vector_state"], mod.FROM_STATE)
            pending = subprocess.run([sys.executable, str(ROOT / mod.ENTRYPOINT)],
                                     capture_output=True, text=True)
            self.assertEqual(pending.returncode, 2)
            self.assertEqual(json.loads(pending.stdout)["failure_code"],
                             "ORGANIZATION_RECEIPT_NOT_APPENDED")


if __name__ == "__main__":
    unittest.main()
