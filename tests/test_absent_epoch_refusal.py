"""An absent epoch is refused; nothing is written and no clock stands in for it.

WU-B13 slice g. The repository ledger (emit.append), the organization ledger
(aggregate_transition, release_custody, assume_custody) and the batch
submission step (submit_pending_released_batch) refuse an absent epoch with the
shared rule's six-field FAIL_CLOSED (HB_EPOCH_NOT_SUPPLIED) before any store is
resolved or opened, and their command lines refuse an omitted --hb-epoch the
same way. A production caller with no supplied epoch in scope refuses
NO_EPOCH_CALLER_FAILS_CLOSED: no file is written and no clock is read.

Clock reads are counted, not raised, so a caller that swallows an exception
cannot hide one: time.time, time.time_ns, the kernels' datetime and the
canonical custody's own clock helpers all count. Supplied epochs are 4096.

Source validation only. No authority effect is claimed.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "resident-runtime", ROOT / "workers"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


emit = _load("transition_ledger_emit_absent_epoch", ".stegverse/transition-ledger/emit.py")
import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as batches  # noqa: E402
import heartbeat_runtime.worker_runtime_legacy  # noqa: E402,F401  (import order)
from workers import canonical_state_transition_custody as custody  # noqa: E402

PREDICATE = "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH"
GOAL = "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
SHA_A, SHA_B = "sha256:" + "a" * 64, "sha256:" + "b" * 64


class ClockCounter:
    """Counts every clock read on the paths under test; returns a value so nothing is masked."""

    def __init__(self):
        self.calls = 0
        counter = self

        class _DateTime:
            @staticmethod
            def now(*args, **kwargs):
                counter.calls += 1
                raise AssertionError("a clock was read")

        self.datetime = _DateTime

    def _tick(self, value):
        def read(*args, **kwargs):
            self.calls += 1
            return value
        return read

    def patches(self, *kernels):
        stack = ExitStack()
        for kernel in kernels:
            stack.enter_context(mock.patch.object(kernel, "datetime", self.datetime))
        stack.enter_context(mock.patch.object(custody, "datetime", self.datetime))
        stack.enter_context(mock.patch.object(time, "time", self._tick(0.0)))
        stack.enter_context(mock.patch.object(time, "time_ns", self._tick(0)))
        stack.enter_context(mock.patch.object(custody, "now", self._tick("1970-01-01T00:00:00Z")))
        stack.enter_context(mock.patch.object(custody, "current_hb_creation_reference", self._tick({})))
        return stack


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class AbsentEpochTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.repo_root = self.work / "repo-ledger"
        self.org_root = self.work / "org-ledger"
        self.env = {"STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root),
                    "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root)}
        patched = mock.patch.dict(os.environ, self.env)
        patched.start()
        self.addCleanup(patched.stop)
        self.clock = ClockCounter()

    def assertSharedRule(self, refusal, retry_entrypoint):
        """The shared rule's own dict: writer_epoch_refusal(None, ...) exactly."""
        self.assertEqual(refusal, org.kernel.writer_epoch_refusal(None, retry_entrypoint=retry_entrypoint))
        self.assertEqual(refusal["failure_code"], "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(refusal["failed_predicate"], PREDICATE)
        self.assertEqual(refusal["owning_existing_goal"], GOAL)

    def assertNoEpochCaller(self, record):
        self.assertEqual(record["failure_code"], "NO_EPOCH_CALLER_FAILS_CLOSED")
        self.assertEqual(record["failed_predicate"], PREDICATE)
        self.assertEqual(record["owning_existing_goal"], GOAL)
        for field in SIX_FIELDS:
            self.assertTrue(str(record.get(field) or "").strip(), field)

    def assertNothingWrittenNoClock(self, before):
        self.assertEqual(snapshot(self.work), before)
        self.assertFalse(self.repo_root.exists())
        self.assertFalse(self.org_root.exists())
        self.assertEqual(self.clock.calls, 0)

    # --- writers: refused before any store is resolved or opened ---------------

    def test_the_repository_ledger_refuses_an_absent_epoch_before_its_store(self):
        before = snapshot(self.work)
        with self.clock.patches(emit.kernel, org.kernel), \
             mock.patch.object(emit, "repository_store", side_effect=AssertionError("store resolved")):
            with self.assertRaises(emit.RepoLedgerEpochRefused) as raised:
                emit.append("t-absent", "TEST", SHA_A, SHA_B)
        self.assertSharedRule(raised.exception.refusal, emit.EPOCH_RETRY_ENTRYPOINT)
        self.assertNothingWrittenNoClock(before)

    def test_the_organization_ledger_refuses_an_absent_epoch_before_its_store(self):
        calls = {
            "aggregate_transition": lambda: org.aggregate_transition({}),
            "release_custody": lambda: org.release_custody({}),
            "assume_custody": lambda: org.assume_custody({}, materialization_id="m"),
            "_aggregate_transition_locked": lambda: org._aggregate_transition_locked({}),
        }
        for name, call in calls.items():
            with self.subTest(writer=name):
                before = snapshot(self.work)
                with self.clock.patches(emit.kernel, org.kernel), \
                     mock.patch.object(org, "organization_store", side_effect=AssertionError("store resolved")):
                    with self.assertRaises(org.OrgLedgerEpochRefused) as raised:
                        call()
                self.assertSharedRule(raised.exception.refusal, org.EPOCH_RETRY_ENTRYPOINT)
                self.assertNothingWrittenNoClock(before)

    def test_the_batch_submission_refuses_an_absent_epoch_before_its_outbox(self):
        before = snapshot(self.work)
        with self.clock.patches(emit.kernel, org.kernel), \
             mock.patch.object(batches, "pending_released_batches", side_effect=AssertionError("outbox read")):
            result = batches.submit_pending_released_batch(self.org_root)
        shared = {key: result[key] for key in result
                  if key not in ("submission_receipts", "submission_receipt", "authority_effect")}
        self.assertSharedRule(shared, batches.SUBMISSION_RETRY_ENTRYPOINT + " (hb_epoch=, or --hb-epoch)")
        self.assertEqual(result["submission_receipts"], [])
        self.assertNothingWrittenNoClock(before)

    # --- command lines: an omitted --hb-epoch is refused the same way ----------

    def run_cli(self, relative, *arguments):
        before = snapshot(self.work)
        completed = subprocess.run([sys.executable, "-B", str(ROOT / relative), *arguments],
                                   capture_output=True, text=True, cwd=self.work, timeout=120,
                                   env={**os.environ, **self.env})
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(snapshot(self.work), before)
        self.assertFalse(self.repo_root.exists())
        self.assertFalse(self.org_root.exists())
        return json.loads(completed.stdout.strip().splitlines()[-1])

    def test_each_writer_command_line_refuses_an_omitted_hb_epoch(self):
        receipt = self.work / "inputs" / "receipt.json"
        receipt.parent.mkdir()
        receipt.write_text(json.dumps({"schema": "stegverse.repo-transition-receipt/v1"}))
        cases = {
            ".stegverse/transition-ledger/emit.py": (
                ("--transition-id", "t", "--transition-class", "TEST",
                 "--predecessor-state-sha256", SHA_A, "--successor-state-sha256", SHA_B),
                ".stegverse/transition-ledger/emit.py (--hb-epoch)"),
            "resident-runtime/aggregate_repo_transition.py": (
                ("--repo-receipt", str(receipt)), org.EPOCH_RETRY_ENTRYPOINT),
            "resident-runtime/organization_batch_custody.py": (
                ("--submit-pending-released-batch", "--root", str(self.org_root)),
                batches.SUBMISSION_RETRY_ENTRYPOINT + " (hb_epoch=, or --hb-epoch)"),
            "resident-runtime/governance_endpoint.py": (
                ("--packet", str(receipt), "--out", str(self.work / "out.json")),
                "resident-runtime/governance_endpoint.py (--hb-epoch)"),
            "resident-runtime/remediation_endpoint.py": (
                ("--packet", str(receipt), "--out", str(self.work / "out.json")),
                "resident-runtime/remediation_endpoint.py (--hb-epoch)"),
        }
        for relative, (arguments, entrypoint) in cases.items():
            with self.subTest(cli=relative):
                self.assertSharedRule(self.run_cli(relative, *arguments), entrypoint)

    # --- production callers with no epoch in scope -------------------------------

    def test_canonical_custody_without_an_epoch_writes_nothing_and_reads_no_clock(self):
        receipt = {"schema": custody.RECEIPT_SCHEMA}
        before = snapshot(self.work)
        with self.clock.patches(emit.kernel, org.kernel):
            submitted = custody.submit_state_receipt(receipt)
            reality = custody.record_organization_runtime_reality(receipt)
            refusal = custody.record_organization_receipt_refusal(
                {"disposition": "FAIL_CLOSED", "failed_predicate": "P"}, gated_transition_id="T")
            helper = custody.CanonicalTransitionCustody("subject-no-epoch")
            row = helper.record("T", outcome="OBSERVED", evidence={}, require_return=False)
        for record in (submitted, reality, row["organization_recording"]):
            self.assertEqual(record["state"], "BOUNDARY")
            self.assertNoEpochCaller(record)
        self.assertIsNone(row["receipt"])
        self.assertIs(refusal["refusal_recorded"], False)
        self.assertNoEpochCaller(refusal["refusal_recording_refusal"])
        self.assertNothingWrittenNoClock(before)

    def test_heartbeat_runtime_and_conversation_evidence_paths_fail_closed(self):
        from heartbeat_runtime.worker_assignment_functional_memory import record_non_allow_functional_memory
        from workers.conversation_evidence_ingestion import custody_ingestion
        before = snapshot(self.work)
        with self.clock.patches(emit.kernel, org.kernel):
            memory = record_non_allow_functional_memory(
                task={"task_id": "TASK-1"}, trigger={"packet_id": "P1"},
                packet={"assignment_transition": {"admissibility_resolution": "DENY"}})
            ingested = custody_ingestion({"record_id": "CASE-NO-EPOCH"})
        for record in (memory, ingested):
            self.assertEqual(record["state"], "BOUNDARY")
            self.assertNoEpochCaller(record)
        self.assertNothingWrittenNoClock(before)

    def test_manifest_ingress_and_crossing_ingest_without_an_epoch_write_nothing(self):
        # The ingress module as its own tests load it, with the SDK stubbed.
        ingress = _load("manifest_ingress_rule_ref_fixture_absent_epoch",
                        "tests/test_organization_manifest_ingress_rule_ref.py").ingress
        frame = org.kernel.carrier_frame(
            {"packet_id": "p-absent", "origin": {"org": "StegVerse-org"},
             "destination": {"org": "StegVerse-Labs", "service": "s"},
             "intr_profile": "x", "payload": {}}, epoch=4096)
        before = snapshot(self.work)
        with self.clock.patches(emit.kernel, org.kernel, ingress.organization_ledger.kernel), \
             mock.patch.object(ingress, "recomputation_rule_ref", side_effect=AssertionError("resolved")):
            received = ingress.receive({"processing": {"capability": "x"}}, registry={})
            refused, recorded = org.kernel.ingest_recorded(
                self.work / "absent-root", {"frame": frame, "path": "f.json"}, {}, {"services": []},
                node_state=None, epoch=None)
        self.assertEqual(received["disposition"], "FAIL_CLOSED")
        self.assertIs(received["refusal_recorded"], False)
        self.assertNoEpochCaller(received)
        self.assertEqual(refused["status"], "REFUSED")
        self.assertNoEpochCaller(refused)
        self.assertIsNone(recorded)
        self.assertNothingWrittenNoClock(before)

    def test_endpoint_record_without_an_epoch_refuses_before_either_ledger(self):
        for relative in ("resident-runtime/governance_endpoint.py", "resident-runtime/remediation_endpoint.py"):
            with self.subTest(endpoint=relative):
                endpoint = _load("absent_epoch_" + Path(relative).stem, relative)
                before = snapshot(self.work)
                with mock.patch.object(subprocess, "run", side_effect=AssertionError("emit.py invoked")):
                    # The endpoint loads its own kernel, so its refusal class is that kernel's.
                    with self.assertRaises(ValueError) as raised:
                        endpoint.record({"packet_id": "p"}, {})
                self.assertEqual(type(raised.exception).__name__, "SuppliedEpochRefused")
                self.assertEqual(raised.exception.refusal["failure_code"], "HB_EPOCH_NOT_SUPPLIED")
                for field in SIX_FIELDS:
                    self.assertTrue(raised.exception.refusal[field], field)
                self.assertEqual(snapshot(self.work), before)

    def test_a_supplied_4096_still_records_as_given(self):
        with self.clock.patches(emit.kernel, org.kernel):
            repository = emit.append("t-4096", "TEST", SHA_A, SHA_B, hb_epoch=4096)
            organization = org.aggregate_transition(
                repository, predecessor_org_state_sha256=SHA_A, successor_org_state_sha256=SHA_B,
                hb_epoch=4096, ledger=self.org_root)
        for receipt in (repository, organization):
            self.assertEqual(receipt["hb_reference"]["epoch"], 4096)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)
        self.assertEqual(self.clock.calls, 0)


if __name__ == "__main__":
    unittest.main()
