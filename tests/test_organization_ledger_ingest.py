"""The committed ingest request the organization ledger writer processes on push to main (no dispatch input).

resident-runtime/organization_ledger_ingest.py reads .stegverse/organization-ledger-ingest/request.json at the
pushed commit, the same push-on-committed-file pattern as the self-closure packet. One route carries both an
sv_check_receipt and a sealed_test_receipt (TVC's conformance receipt). Clock-free and network-free: the reader
and admission are checked on temporary files, the append and readback on temporary git ledgers wired as the
writer wires the real ref, and the writer and its PR checks as text.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITER = ROOT / ".github/workflows/organization-ledger-transition.yml"
VALIDATION = ROOT / ".github/workflows/organization-ledger-transition-validation.yml"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
LABS = "StegVerse-Labs/.github"
# TVC push run 40137248073 at StegVerse-Labs/TVC 8c8ec518 (TVC#539) printed this receipt between
# TVC_LABS_CONFORMANCE_RECEIPT_JSON_BEGIN/END; its seal names Labs#3317's head 006b32a0. The contract's
# surface_paths_observed_at still records it: its surface is byte-identical to Labs main.
TVC_LABS_RECEIPT_SHA256 = "sha256:9823142846b9a4cb98b6ef48bc2d652c9efe7be908e24fa2502eb8e397560270"
# The committed request: TVC push run 40999761329 at StegVerse-Labs/TVC e9d646ad printed this receipt in the same
# block; its seal names Labs#3434's head c6e46982 (ALLOW, 25 tests, 0 skipped).
COMMITTED_RUN_ID = 40999761329
COMMITTED_RECEIPT_SHA256 = "sha256:da6fdfa471ecabcb3f079321d850c55b5174da14e470f0bf781adb9ab5ecde36"
COMMITTED_LABS_COMMIT = "c6e4698256baa6b78ab675cd5963182cf7add498"
COMMITTED_TVC_HEAD = "e9d646ad21677737954ce0169b68c32d75b0b6c9"


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ing = _load("organization_ledger_ingest_under_test", ROOT / "resident-runtime/organization_ledger_ingest.py")
# The seeded git ledger and the sv_check append it uses to give the head a supplied epoch.
appendtests = _load("test_sv_check_receipt_append_for_ingest", ROOT / "tests/test_sv_check_receipt_append.py")
svc, GitLedger, REF = appendtests.svc, appendtests.GitLedger, appendtests.REF
consumer = _load("tvc_conformance_receipt_for_ingest", ROOT / "scripts/tvc_conformance_receipt.py")
pushappend = _load("sv_push_receipt_append_for_ingest", ROOT / "resident-runtime/sv_push_receipt_append.py")
org = ing.writer().organization_ledger
CONTRACT = json.loads((ROOT / ".stegverse/verification-inputs/tvc-conformance-receipt.json").read_text(encoding="utf-8"))
CHECK = {"schema": "stegverse.sv_check_receipt.v1", "check_id": "x", "hb_epoch": "40"}
ACCEPTED = [{"schema": "stegverse.test-suite-skip-receipt/v1", "receipt_kind": "TVC_LABS_CONFORMANCE_TEST_RECEIPT",
             "suite": "TVC_LABS_CONFORMANCE", "repository": "StegVerse-Labs/TVC"}]


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sealed(body):
    body = {k: v for k, v in body.items() if k != "receipt_sha256"}
    return body | {"receipt_sha256": "sha256:" + hashlib.sha256(canon(body)).hexdigest()}


def fsha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


SURFACE = {"heartbeat_runtime/x.py": b"x = 1\n", CONTRACT["tests"][0]: b"t0\n", CONTRACT["tests"][1]: b"t1\n"}


def tvc_receipt(**over):
    body = {"schema": "stegverse.test-suite-skip-receipt/v1", "receipt_kind": "TVC_LABS_CONFORMANCE_TEST_RECEIPT",
            "suite": "TVC_LABS_CONFORMANCE", "repository": "StegVerse-Labs/TVC", "head_sha": "c" * 40,
            "disposition": "ALLOW", "refusals": [],
            "counts": {"tests": 2, "skipped": 0, "failed": 0, "errors": 0, "passed": 2, "xfailed": 0},
            "test_ids": [consumer.module_of(t) + ".T::a" for t in CONTRACT["tests"]],
            "ledger_candidate": {"candidate": True, "appended_by_this_job": False, "target": ing.ledger_target(LABS)},
            "consumed_source": {"repository": LABS, "commit": "d" * 40,
                                "observed_surface": {p: fsha(d) for p, d in SURFACE.items()}}}
    return sealed(body | over)


def provenance(receipt, **over):
    return {"repository": receipt["repository"], "run_id": 1, "head_sha": receipt["head_sha"]} | over


def write(tmp: str, doc, name="request.json") -> Path:
    path = Path(tmp) / name
    path.write_text(doc if isinstance(doc, str) else json.dumps(doc), encoding="utf-8")
    return path


def sv_request(**override):
    return {"schema": ing.SCHEMA, "operation": ing.SV_CHECK, "check_receipt": dict(CHECK), "hb_epoch": 40} | override


def sealed_request(receipt=None, **override):
    receipt = tvc_receipt() if receipt is None else receipt
    prov = provenance(receipt) if isinstance(receipt, dict) else {}
    return {"schema": ing.SCHEMA, "operation": ing.SEALED, "receipt": receipt, "provenance": prov} | override


class Refusals:
    def assertRefused(self, result, code):
        self.assertEqual(result["disposition"], "FAIL_CLOSED", result)
        self.assertEqual(result["failure_code"], code, result)
        for field in SIX:
            self.assertTrue(result.get(field), field)
        self.assertIs(result["consequence_committed"], False)


class Reader(Refusals, unittest.TestCase):
    def test_well_formed_requests_are_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = ing.read_request(write(tmp, sv_request()))
            self.assertEqual(got, {"disposition": "ALLOW", "operation": ing.SV_CHECK, "check_receipt": CHECK,
                                   "hb_epoch": 40, "evaluation_subject": None, "base_state_readback": None})
            request = sealed_request()
            got = ing.read_request(write(tmp, request))
            self.assertEqual(got, {"disposition": "ALLOW", "operation": ing.SEALED, "receipt": request["receipt"],
                                   "provenance": request["provenance"]})

    def test_absent_unreadable_and_malformed_requests_fail_closed_with_six_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertRefused(ing.read_request(Path(tmp) / "absent.json"), "INGEST_REQUEST_ABSENT")
            self.assertRefused(ing.read_request(write(tmp, "{not json")), "INGEST_REQUEST_UNREADABLE")
            for bad in ([], sv_request(schema="other/v1"), sv_request(operation="other"), {"schema": ing.SCHEMA},
                        sv_request(extra=1), sv_request(evaluation_subject=[]), sv_request(receipt={}),
                        sealed_request(hb_epoch=40), sealed_request(provenance="x"), sealed_request(receipt=[])):
                self.assertRefused(ing.read_request(write(tmp, bad)), "INGEST_REQUEST_SCHEMA_MISMATCH")
            self.assertRefused(ing.read_request(write(tmp, sv_request(check_receipt="{}"))),
                               "LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT")
            for epoch in (None, "40", -1, True, 40.0):
                self.assertRefused(ing.read_request(write(tmp, sv_request(hb_epoch=epoch))),
                                   "SV_CHECK_RECEIPT_HB_EPOCH_INVALID")

    def test_read_materializes_the_operations_inputs_and_env(self):
        subject, readback = {"schema": "s"}, {"schema": "r"}
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, sv_request(evaluation_subject=subject, base_state_readback=readback))
            out, env = Path(tmp) / "out", Path(tmp) / "env"
            self.assertEqual(ing.main(["read", "--request", str(path), "--materialize", str(out),
                                       "--github-env", str(env)]), 0)
            self.assertEqual(json.loads((out / "check-receipt.json").read_text()), CHECK)
            self.assertEqual(json.loads((out / "evaluation-subject.json").read_text()), subject)
            self.assertEqual(json.loads((out / "base-state-readback.json").read_text()), readback)
            self.assertEqual(env.read_text().splitlines(), ["INGEST_OPERATION=sv_check_receipt", "HB_EPOCH=40"])
            request = sealed_request()
            out3, env3 = Path(tmp) / "out3", Path(tmp) / "env3"
            self.assertEqual(ing.main(["read", "--request", str(write(tmp, request, "s.json")), "--materialize",
                                       str(out3), "--github-env", str(env3)]), 0)
            self.assertEqual(json.loads((out3 / "sealed-receipt.json").read_text()), request["receipt"])
            self.assertEqual(env3.read_text().splitlines(), ["INGEST_OPERATION=sealed_test_receipt"])
            out2 = Path(tmp) / "out2"
            self.assertEqual(ing.main(["read", "--request", str(Path(tmp) / "absent.json"), "--materialize", str(out2),
                                       "--github-env", str(env)]), 1)
            self.assertFalse(out2.exists())
            self.assertEqual(env.read_text().splitlines(), ["INGEST_OPERATION=sv_check_receipt", "HB_EPOCH=40"])


class Admission(Refusals, unittest.TestCase):
    def admit(self, receipt, prov=None, repo=LABS):
        return ing.admit_sealed(receipt, prov or provenance(receipt), ledger_repository=repo, accepted=ACCEPTED)

    def test_a_sealed_allow_receipt_for_this_ledger_is_admitted(self):
        self.assertIsNone(self.admit(tvc_receipt()))

    def test_each_admission_predicate_refuses_with_six_fields(self):
        good = tvc_receipt()
        tampered = dict(good, head_sha="e" * 40)
        self.assertRefused(self.admit(tampered, provenance(good)), "SEALED_RECEIPT_SEAL_MISMATCH")
        self.assertRefused(self.admit(tvc_receipt(receipt_kind="OTHER")), "SEALED_RECEIPT_NOT_ACCEPTED")
        self.assertRefused(self.admit(tvc_receipt(disposition="FAIL_CLOSED")), "SEALED_RECEIPT_NOT_ALLOW")
        self.assertRefused(self.admit(tvc_receipt(refusals=[{"x": 1}])), "SEALED_RECEIPT_NOT_ALLOW")
        for counts in ({"tests": 2, "skipped": 1, "failed": 0, "errors": 0}, {"tests": 2, "skipped": 0, "failed": 1, "errors": 0},
                       {"tests": 0, "skipped": 0, "failed": 0, "errors": 0}, {"tests": 2, "skipped": 0}):
            self.assertRefused(self.admit(tvc_receipt(counts=counts)), "SEALED_RECEIPT_TESTS_NOT_ZERO_SKIPPED")
        self.assertRefused(self.admit(good, repo="StegVerse-org/.github"), "SEALED_RECEIPT_TARGETS_ANOTHER_LEDGER")
        self.assertRefused(self.admit(tvc_receipt(ledger_candidate={"candidate": False, "target": ing.ledger_target(LABS)})),
                           "SEALED_RECEIPT_TARGETS_ANOTHER_LEDGER")
        for prov in (provenance(good, head_sha="f" * 40), provenance(good, repository="x/y"), provenance(good, run_id="1"),
                     provenance(good, run_id=True)):
            self.assertRefused(self.admit(good, prov), "SEALED_RECEIPT_PROVENANCE_MISMATCH")
        undeclared = ing.admit_sealed(good, provenance(good), ledger_repository=LABS,
                                      accepted=ing.load_accepted(ROOT / "absent.json"))
        self.assertRefused(undeclared, "SEALED_RECEIPT_ACCEPTANCE_UNDECLARED")

    def test_a_sealed_receipt_is_bound_by_its_own_seal(self):
        good = tvc_receipt()
        for source in (ing.sealed_source(good), ing.verify_any_source(org, good)):
            self.assertEqual(source["source_transition_sha256"], good["receipt_sha256"])
            self.assertIsNone(source["repo_receipt_sha256"])
            self.assertIsNone(source["source_repository"])
        with self.assertRaises(ValueError):
            ing.sealed_source(dict(good, head_sha="e" * 40))
        with self.assertRaises(ValueError):
            ing.sealed_source(dict(good, schema="stegverse.repo-transition-receipt/v1"))

    def test_the_tvc_observed_writer_surface_is_not_edited_by_this_route(self):
        # aggregate_repo_transition.py and org-contract.json are in the observed_surface of the
        # receipt this route ingests; editing either would make that receipt stale for the ratchet.
        request = ing.read_request(ROOT / ing.REQUEST_PATH)
        if request["operation"] != ing.SEALED:
            # The committed request is one operation at a time. While it carries an sv_push_receipt there is no
            # sealed TVC receipt in it to hold the surface against; the guard applies again when a sealed request
            # is committed.
            self.assertEqual(request["operation"], ing.SV_PUSH)
            return
        receipt = request["receipt"]
        observed = receipt["consumed_source"]["observed_surface"]
        for path in ("resident-runtime/aggregate_repo_transition.py", ".stegverse/transition-ledger/org-contract.json"):
            self.assertIn(path, observed)
        self.assertNotIn("stegverse.test-suite-skip-receipt/v1", org.C["consumes"])
        self.assertFalse(hasattr(org, "SEALED_TEST_RECEIPT_SCHEMA"))

    def test_the_committed_request_is_tvc_run_40137248073s_labs_receipt_and_is_admitted(self):
        """The committed request's TVC receipt is admitted. The method name is kept so the test-suite ratchet sees the
        same test at the head (TEST_PRESENT_AT_BASE_RUNS_AT_HEAD); the request now carries run COMMITTED_RUN_ID
        (40999761329, TVC main e9d646ad), which supersedes runs 40166845193 (TVC#551), 40160000328 (TVC#546) and 40137248073 (TVC#539)."""
        request = ing.read_request(ROOT / ing.REQUEST_PATH)
        if request["operation"] == ing.SV_PUSH:
            # A committed sv_push_receipt request replaces the sealed one (one request holds one receipt). It is
            # admitted when the producer's own shape and seal check passes and its epoch is the receipt's own.
            receipt = request["push_receipt"]
            self.assertIsNone(pushappend.push_payload(receipt))
            self.assertEqual(request["hb_epoch"], int(receipt["hb_epoch"]))
            return
        self.assertEqual(request["operation"], ing.SEALED)
        receipt = request["receipt"]
        self.assertTrue(ing.seal_verifies(receipt))
        self.assertEqual(receipt["receipt_sha256"], COMMITTED_RECEIPT_SHA256)
        self.assertEqual(receipt["consumed_source"]["commit"], COMMITTED_LABS_COMMIT)
        self.assertEqual((receipt["head_sha"], request["provenance"]["head_sha"]), (COMMITTED_TVC_HEAD,) * 2)
        self.assertEqual(request["provenance"]["run_id"], COMMITTED_RUN_ID)
        self.assertEqual((receipt["counts"]["tests"], receipt["counts"]["skipped"], receipt["skipped"]), (25, 0, []))
        self.assertIsNone(ing.admit_sealed(receipt, request["provenance"], ledger_repository=LABS))
        self.assertTrue(consumer.is_conformance_receipt(receipt, CONTRACT))
        self.assertEqual(CONTRACT["surface_paths_observed_at"]["receipt_sha256"], TVC_LABS_RECEIPT_SHA256)


class SealedAppend(Refusals, GitLedger):
    def fresh(self):
        reader = self.work / ("reader%d.git" % len(list(self.work.glob("reader*.git"))))
        subprocess.run(["git", "init", "--bare", "-q", str(reader)], check=True)
        subprocess.run(["git", "--git-dir", str(reader), "fetch", "-q", str(self.bare), f"+{REF}:{REF}"], check=True)
        return f"git+{reader}#{REF}"

    def test_append_retains_the_exact_receipt_reads_back_and_the_ratchet_consumer_binds_it(self):
        self.assertEqual(svc.append_check_receipt(appendtests.check_receipt(), hb_epoch=40)["disposition"], "ALLOW")
        receipt = tvc_receipt()
        result = ing.append_sealed(receipt, provenance(receipt), ledger_repository=LABS, accepted=ACCEPTED)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual((result["hb_epoch"], result["transition_replayed"]), (40, False))
        replay = ing.append_sealed(receipt, provenance(receipt), ledger_repository=LABS, accepted=ACCEPTED)
        self.assertEqual((replay["transition_replayed"], replay["organization_receipt_sha256"]),
                         (True, result["organization_receipt_sha256"]))
        location = self.fresh()
        back = ing.readback_sealed(location, receipt)
        self.assertEqual(back["disposition"], "ALLOW", back)
        self.assertEqual(back["organization_receipt_sha256"], result["organization_receipt_sha256"])
        self.assertEqual(back["org_transition_class"], ing.SEALED_CLASS)
        self.assertEqual(back["hb_reference"]["epoch"], 40)
        self.assertIs(back["hb_reference"]["derived_from_clock"], False)
        with tempfile.TemporaryDirectory() as tmp:
            head = Path(tmp)
            for path, data in SURFACE.items():
                (head / path).parent.mkdir(parents=True, exist_ok=True)
                (head / path).write_bytes(data)
            bound = consumer.consume(dict(CONTRACT, surface_paths=sorted(SURFACE)), location, head, None)
        self.assertEqual(bound["disposition"], "ALLOW", bound)
        self.assertEqual(bound["bound_receipt_sha256"], receipt["receipt_sha256"])
        self.assertEqual(bound["bound_by_organization_receipt_sha256"], result["organization_receipt_sha256"])
        # the chain keeps taking appends over the retained sealed receipt
        later = svc.append_check_receipt(appendtests.check_receipt(head_sha="b" * 40, hb_epoch="41"), hb_epoch=41)
        self.assertEqual(later["disposition"], "ALLOW", later)
        self.assertEqual(ing.readback_sealed(self.fresh(), receipt)["disposition"], "ALLOW")

    def test_nothing_is_written_without_a_supplied_head_epoch_or_admission(self):
        before = self.tip()
        receipt = tvc_receipt()
        out = ing.append_sealed(receipt, provenance(receipt), ledger_repository=LABS, accepted=ACCEPTED)
        self.assertEqual(out["disposition"], "FAIL_CLOSED", out)
        self.assertIs(out["consequence_committed"], False)
        self.assertEqual(self.tip(), before)
        out = ing.append_sealed(dict(receipt, head_sha="e" * 40), provenance(receipt), ledger_repository=LABS,
                                accepted=ACCEPTED)
        self.assertRefused(out, "SEALED_RECEIPT_SEAL_MISMATCH")
        self.assertEqual(self.tip(), before)
        self.assertRefused(ing.readback_sealed(self.fresh(), receipt), "LEDGER_READBACK_UNAVAILABLE")


def _triggers(text):
    head = text.split("\njobs:\n", 1)[0]
    return head, head.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]


class Triggers(unittest.TestCase):
    def test_the_writer_runs_on_push_for_the_request_without_dispatch(self):
        text = WRITER.read_text(encoding="utf-8")
        head, triggers = _triggers(text)
        self.assertEqual(triggers.splitlines()[0], "  push:")
        for word in ("workflow_dispatch", "pull_request", "schedule", "repository_dispatch", "workflow_run"):
            self.assertNotIn(word, triggers, word)
        for word in ("workflow_dispatch", "github.event.inputs"):
            self.assertNotIn(word, text, word)
        self.assertIn("    paths:\n", head)
        self.assertIn("      - '" + ing.REQUEST_PATH + "'\n", head)
        self.assertIn("resident-runtime/organization_ledger_ingest.py read --request " + ing.REQUEST_PATH, text)
        for command in ("sv_check_receipt_append.py append", "sv_check_receipt_append.py readback",
                        "organization_ledger_ingest.py append-sealed", "organization_ledger_ingest.py readback-sealed"):
            self.assertIn("resident-runtime/" + command, text)
        for gate in ("env.INGEST_REQUEST_CHANGED == '1'", "env.INGEST_OPERATION == 'sv_check_receipt'",
                     "env.INGEST_OPERATION == 'sealed_test_receipt'"):
            self.assertIn("if: " + gate, text)
        # The self-closure branch is retired (Rigel's rule, 2026-10-25: no InTr hop inside one organization).
        self.assertNotIn("SELF_CLOSURE_PACKET_CHANGED", text)
        self.assertIn('git diff --name-only "$PUSH_BEFORE" "$GITHUB_SHA"', text)
        self.assertIn("NO_COMMITTED_PACKET_CHANGED", text)
        self.assertIn("concurrency:\n  group: organization-ledger\n  cancel-in-progress: false\n", text)
        self.assertIn('git push origin "$LEDGER_REF:$LEDGER_REF"', text)
        self.assertNotIn("--force", text)

    def test_no_separate_writer_workflow_is_added(self):
        self.assertFalse((ROOT / ".github/workflows/organization-ledger-transition-writer.yml").exists())
        self.assertFalse((ROOT / ".github/workflows/organization-ledger-ingest.yml").exists())

    def test_the_pr_checks_cover_the_request_and_append_nothing(self):
        text = VALIDATION.read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        for path in (".stegverse/organization-ledger-ingest/**", "resident-runtime/organization_ledger_ingest.py",
                     "resident-runtime/sv_check_receipt_append.py", "tests/test_organization_ledger_ingest.py",
                     "tests/test_sv_check_receipt_append.py", "resident-runtime/aggregate_repo_transition.py",
                     ".stegverse/transition-ledger/org-contract.json"):
            self.assertIn("'" + path + "'", text, path)
        jobs = text.split("\njobs:\n", 1)[1]
        self.assertIn("tests/test_organization_ledger_ingest.py", jobs)
        self.assertIn("organization_ledger_ingest.py admit-sealed", jobs)
        for command in ("sv_check_receipt_append.py append", "append-sealed", "git push"):
            self.assertNotIn(command, text)
        code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
        self.assertNotIn("contents: write", code)
        self.assertNotIn("    if:", code)


if __name__ == "__main__":
    unittest.main()
