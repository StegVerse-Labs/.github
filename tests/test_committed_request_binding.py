"""A request run binds every receipt to its committed request; a caller cannot forge one (VALIDATOR rows 1, 5, 6, 7).

Row 1 (route A): resident_cycle_request.py exports the committed request's
path and the sha256 of its bytes (STEGVERSE_COMMITTED_REQUEST_PATH /
_SHA256). Every receipt the run writes (repository, organization, cycle)
carries a top-level committed_request {path, sha256}, which the kernel
re-verifies against the file. A half-set, malformed or mismatched pair is
refused six-field before anything is written.
Row 5: a committed_request key at any depth in caller evidence (emit
evidence, aggregate boundary_evidence; in-process or CLI) is refused before
any write.
Row 6: egress emit validates the pair and refuses a committed_request in the
payload before anything is built or published: 0 frames.
Row 7: a source receipt carrying committed_request is aggregated only in the
run of that same committed request.

Source validation only. No authority effect is claimed.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tests.test_reverse_intr_inter_org_route as route

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as org  # noqa: E402

emit = org._repository_ledger()
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
SHA_A, SHA_B = "sha256:" + "a" * 64, "sha256:" + "b" * 64
PATH_ENV, SHA_ENV = org.kernel.COMMITTED_REQUEST_PATH_ENV, org.kernel.COMMITTED_REQUEST_SHA256_ENV


def request_file(directory, epoch="4096"):
    path = Path(directory) / "request.json"
    path.write_bytes(json.dumps({"schema": "stegverse.resident-cycle-request/v1", "hb_epoch": epoch}).encode())
    return path, "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class Refusals:
    def assertCommittedRequestRefused(self, raised, code):
        self.assertEqual(type(raised).__name__, "CommittedRequestRefused")
        record = raised.record
        self.assertEqual((record["disposition"], record["failure_code"]), ("FAIL_CLOSED", code))
        for field in SIX:
            self.assertTrue(str(record.get(field) or "").strip(), field)
        self.assertIs(record["consequence_committed"], False)


class LedgerBindingTests(Refusals, unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.work, True)
        self.repo = org.ledger_store.PosixLedgerStore(self.work / "repo")
        self.org_root = self.work / "org"
        self.request, self.digest = request_file(self.work)
        env = mock.patch.dict(os.environ, {"STEGVERSE_REPO_LEDGER_ROOT": str(self.work / "repo")})
        env.start(); self.addCleanup(env.stop)
        for name in (PATH_ENV, SHA_ENV):
            os.environ.pop(name, None)

    def in_run(self, path=None, digest=None):
        return mock.patch.dict(os.environ, {PATH_ENV: str(path or self.request), SHA_ENV: digest or self.digest})

    def append(self, tid="t", evidence=None):
        return emit.append(tid, "TEST", SHA_A, SHA_B, evidence or {}, "NONE", hb_epoch=4096, store=self.repo)

    def aggregate(self, receipt, **kwargs):
        return org.aggregate_transition(receipt, predecessor_org_state_sha256=SHA_A, successor_org_state_sha256=SHA_B,
                                        hb_epoch=4096, ledger=self.org_root, repository_ledger=self.repo, **kwargs)

    def written(self):
        return sorted(str(p.relative_to(self.work)) for p in self.work.rglob("*")
                      if p.is_file() and p.name != "request.json")

    # Row 1 -----------------------------------------------------------------
    def test_every_ledger_receipt_of_a_request_run_binds_the_committed_request(self):
        with self.in_run():
            repository = self.append()
            organization = self.aggregate(repository)
        binding = {"path": str(self.request.resolve()), "sha256": self.digest, "hb_epoch_source": "COMMITTED_REQUEST"}
        self.assertEqual(repository["committed_request"], binding)
        self.assertEqual(organization["committed_request"], binding)
        # The binding is inside the hashed body of both receipts.
        for receipt in (repository, organization):
            self.assertEqual(receipt["receipt_sha256"], org.sha({k: v for k, v in receipt.items() if k != "receipt_sha256"}))

    def test_outside_a_request_run_no_binding_is_written(self):
        repository = self.append()
        self.assertNotIn("committed_request", repository)
        self.assertNotIn("committed_request", self.aggregate(repository))

    def test_a_half_set_malformed_or_mismatched_pair_is_refused_before_any_write(self):
        cases = [
            ("half-set", "COMMITTED_REQUEST_INVALID", {PATH_ENV: str(self.request)}),
            ("malformed", "COMMITTED_REQUEST_INVALID", {PATH_ENV: str(self.request), SHA_ENV: "md5:00"}),
            ("mismatched", "COMMITTED_REQUEST_DIGEST_MISMATCH",
             {PATH_ENV: str(self.request), SHA_ENV: "sha256:" + "0" * 64}),
        ]
        for label, code, pair in cases:
            with self.subTest(label), mock.patch.dict(os.environ, pair):
                with self.assertRaises(Exception) as raised:
                    self.append("t-" + label)
                self.assertCommittedRequestRefused(raised.exception, code)
                self.assertEqual(self.written(), [])

    # Row 5 -----------------------------------------------------------------
    def test_a_committed_request_in_caller_evidence_at_any_depth_is_refused_before_any_write(self):
        forged = {"committed_request": {"path": "x", "sha256": self.digest}}
        for evidence in (forged, {"a": forged}, {"a": [1, {"b": forged}]}):
            with self.subTest(evidence=evidence), self.in_run():
                with self.assertRaises(Exception) as raised:
                    self.append("t-forged", evidence)
                self.assertCommittedRequestRefused(raised.exception, "FORGED_COMMITTED_REQUEST_FROM_EVIDENCE")
                self.assertEqual(self.written(), [])
        repository = self.append("t-clean")
        for evidence in (forged, {"nested": [forged]}):
            with self.subTest(boundary_evidence=evidence):
                with self.assertRaises(Exception) as raised:
                    self.aggregate(repository, boundary_evidence=evidence)
                self.assertCommittedRequestRefused(raised.exception, "FORGED_COMMITTED_REQUEST_FROM_EVIDENCE")
                self.assertFalse(self.org_root.exists())

    def test_the_cli_refuses_a_forged_committed_request_in_evidence_json(self):
        env = {**os.environ, "STEGVERSE_REPO_LEDGER_ROOT": str(self.work / "repo")}
        completed = subprocess.run(
            [sys.executable, "-B", str(ROOT / ".stegverse/transition-ledger/emit.py"), "--transition-id", "cli",
             "--transition-class", "TEST", "--predecessor-state-sha256", SHA_A, "--successor-state-sha256", SHA_B,
             "--evidence-json", json.dumps({"deep": {"committed_request": {"path": "x", "sha256": self.digest}}}),
             "--hb-epoch", "4096"], capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["failure_code"], "FORGED_COMMITTED_REQUEST_FROM_EVIDENCE")
        self.assertEqual(self.written(), [])

    # Row 7 -----------------------------------------------------------------
    def test_a_bound_source_receipt_is_aggregated_only_in_its_own_request_run(self):
        with self.in_run():
            repository = self.append()
        (self.work / "other").mkdir()
        other, other_digest = request_file(self.work / "other", epoch="5000")
        for label, context in (("no run", mock.patch.dict(os.environ, {})),
                               ("another run", self.in_run(other, other_digest))):
            with self.subTest(label), context:
                with self.assertRaises(Exception) as raised:
                    self.aggregate(repository)
                self.assertCommittedRequestRefused(raised.exception, "COMMITTED_REQUEST_DIGEST_UNVERIFIED")
                self.assertFalse(self.org_root.exists())
        with self.in_run():
            self.assertEqual(self.aggregate(repository)["repo_receipt_sha256"], repository["receipt_sha256"])


class CycleBindingTests(unittest.TestCase):
    def test_the_dispatched_cycle_receipt_binds_the_committed_request(self):
        rc_spec = __import__("importlib.util").util.spec_from_file_location(
            "rc_binding", ROOT / "resident-runtime/resident_cycle_request.py")
        rc = __import__("importlib.util").util.module_from_spec(rc_spec); rc_spec.loader.exec_module(rc)
        with tempfile.TemporaryDirectory() as work, mock.patch.dict(os.environ):
            request, digest = request_file(work)
            seen = {}

            class Cycle:
                @staticmethod
                def main(argv):
                    seen["bound"] = rc.K.committed_request()
                    return 0

            with mock.patch.object(rc, "_cycle", lambda: Cycle):
                self.assertEqual(rc.main(["--request", str(request)]), 0)
        self.assertEqual(seen["bound"], {"path": str(request.resolve()), "sha256": digest,
                                         "hb_epoch_source": "COMMITTED_REQUEST"})


class EgressBindingTests(Refusals, route.ReverseIntrRouteCase):
    payload = route.GovernanceReverseLegTests.payload

    def emit(self, payload):
        return route.egress.emit(route.PEER, payload, standing=route.GENESIS, capability="governance",
                                 transition_reference="ecosystem.transition.reverse-intr.v1",
                                 mesh_root=self.mesh, hb_epoch=4096)

    def frames(self):
        return sorted((self.mesh / "frames.d").glob("*.json")) if (self.mesh / "frames.d").is_dir() else []

    def test_a_half_set_pair_or_a_payload_committed_request_publishes_nothing(self):
        with tempfile.TemporaryDirectory() as work:
            request, digest = request_file(work)
            cases = {
                "COMMITTED_REQUEST_INVALID": ({PATH_ENV: str(request)}, self.payload()),
                "COMMITTED_REQUEST_DIGEST_MISMATCH": ({PATH_ENV: str(request), SHA_ENV: "sha256:" + "0" * 64},
                                                      self.payload()),
                "FORGED_COMMITTED_REQUEST_FROM_EVIDENCE": ({}, {**self.payload(), "body": {
                    "committed_request": {"path": "x", "sha256": digest}}}),
            }
            for code, (pair, payload) in cases.items():
                with self.subTest(code=code), mock.patch.dict(os.environ, pair):
                    with self.assertRaises(Exception) as raised:
                        self.emit(payload)
                    self.assertCommittedRequestRefused(raised.exception, code)
                    self.assertEqual(self.frames(), [])


if __name__ == "__main__":
    unittest.main()
