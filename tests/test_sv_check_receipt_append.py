"""sv_check_receipt: the org-ledger writer appends one NWI-S1 check receipt.

Temporary repositories only. Receipts here are exercise evidence on those
repositories, not records of the published organization ledger.

Oracle: P1's readers at the c9192134 re-pin (StegVerse-Labs/.github#3282), vendored under
tests/vendor/p1_c9192134/ in P1's own layout: the contract manifest data/sv-work-items/contract-pins.json (blob
56116e48, sha256 8f750202...) and only the files this operation uses, each verified
against its manifest sha256 (sv_work_items.py 94f56a0f, required-checks.json 482e3af9,
lifecycle-transitions.json c66de6e8, sv-check-receipt.v1.schema.json a4934cc1, stages
NWI-S0..S4). tests/sv_ledger_fixtures.py (30a9fe89) is test-only and not listed in the
manifest, so it is pinned by its blob. The operation runs P1's module itself
(svc.p1_readers()); this test uses that same module. This PR touches no P1 path.
Shared epoch rule: org-kernel/kernel.py::supplied_epoch_failure, SHARED_RULE_SHA256 c9192134... (its ast
segment; function text ad8ff529); storage location kernel.py hb_reference.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = "refs/stegverse/organization-ledger"
NAMESPACE = "repository-ledger/StegVerse-Labs/.github"
VENDOR = ROOT / "tests" / "vendor" / "p1_c9192134"
MANIFEST_SHA256 = "8f75020249d7a12f8ac754443aec1a01da4c2572e052172bff8f35970e35ab87"
FIXTURES_BLOB = "30a9fe8980671e63348810c837882f3dab525459"
GATE = "nwi-s0-exit-gate"
S1_RUN = "SV-LLM/.github#46@64b90721"
LEDGER_REPOSITORY = "StegVerse-Labs/.github"
# The push-on-committed-file writer (Labs#3312) and its read-only PR checks.
WRITER = ROOT / ".github" / "workflows" / "organization-ledger-transition.yml"
PR_FACING = ROOT / ".github" / "workflows" / "organization-ledger-transition-validation.yml"
HEAD = "a" * 40
CHANGE = "sha256:" + "b" * 64


def _module(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


svc = _module("sv_check_receipt_append_test", ROOT / "resident-runtime" / "sv_check_receipt_append.py")
ingress = svc.ingress
ledger_store = ingress.repository_ledger.ledger_store
readback = _module("organization_ledger_readback_sv_check", ROOT / "resident-runtime" / "organization_ledger_readback.py")
REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))

wi = svc.p1_readers()
_FX_ROOT = tempfile.TemporaryDirectory()


def _fixtures():
    """P1's tests/sv_ledger_fixtures.py (vendored byte-identical) resolves its modules from parents[1]; run the vendored
    bytes from a temp root's tests/ whose other top-level entries link to this checkout."""
    root = Path(_FX_ROOT.name)
    (root / "tests").mkdir(exist_ok=True)
    (root / "tests" / "sv_ledger_fixtures.py").write_bytes((VENDOR / "tests" / "sv_ledger_fixtures.py").read_bytes())
    for entry in ROOT.iterdir():
        if entry.name not in ("tests", ".git") and not (root / entry.name).exists():
            os.symlink(entry, root / entry.name)
    return _module("sv_ledger_fixtures_p1", root / "tests" / "sv_ledger_fixtures.py")


fx = _fixtures()


def check_receipt(**override):
    r = {"schema": "stegverse.sv_check_receipt.v1", "check_id": "workflow-surface-registered",
         "disposition": "FAIL_CLOSED", "change_digest": CHANGE, "head_sha": HEAD, "hb_epoch": "40",
         "verifier_ref": "SV-LLM/.github#46 fixture run",
         "failure_code": "WORKFLOW_SURFACE_UNREGISTERED", "failed_predicate": "EVERY_WORKFLOW_FILE_IS_REGISTERED",
         "required_evidence_or_repair": "register .github/workflows/x.yml in control/workflow-surface-registry.json",
         "retry_entrypoint": "scripts/validate_workflow_surface_hygiene.py", "owning_existing_goal": "HYGIENE-CAUSAL-ROOTS-001",
         "next_attempt": "after the registry entry lands"}
    r.update(override)
    return {k: v for k, v in r.items() if v is not None}


def _git(repo, *args, input_bytes=None):
    env = os.environ.copy()
    env.update({"GIT_AUTHOR_NAME": "ledger-seed", "GIT_AUTHOR_EMAIL": "seed@example.invalid",
                "GIT_COMMITTER_NAME": "ledger-seed", "GIT_COMMITTER_EMAIL": "seed@example.invalid"})
    done = subprocess.run(["git", "--git-dir", str(repo), *args], input=input_bytes, capture_output=True, env=env, check=True)
    return done.stdout


def _p1_refusal(call):
    try:
        call()
    except BaseException as exc:  # P1's Refusal
        record = getattr(exc, "record", None)
        if record is None:
            raise
        return record
    raise AssertionError("expected a refusal")


class GitLedger(unittest.TestCase):
    """A seeded bare ledger repository, wired exactly as the writer workflow wires the real ref."""

    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.bare = self.work / "ledger.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.bare)], check=True)
        marker = _git(self.bare, "hash-object", "-w", "--stdin", input_bytes=b"prior-history\n").decode().strip()
        index = self.work / "seed.index"
        prior_index = os.environ.get("GIT_INDEX_FILE")
        os.environ["GIT_INDEX_FILE"] = str(index)
        try:
            _git(self.bare, "read-tree", "--empty")
            _git(self.bare, "update-index", "--add", "--cacheinfo", f"100644,{marker},MARKER")
            tree = _git(self.bare, "write-tree").decode().strip()
        finally:
            if prior_index is None:
                os.environ.pop("GIT_INDEX_FILE", None)
            else:
                os.environ["GIT_INDEX_FILE"] = prior_index
        self.seed = _git(self.bare, "commit-tree", tree, "-m", "prior history").decode().strip()
        _git(self.bare, "update-ref", REF, self.seed)
        contract = ingress.organization_ledger.C
        previous = contract.get("organization_ledger")
        contract["organization_ledger"] = {"store": "git", "ref": REF, "custody": "PRIVATE", "propagate_target": None}
        names = ("STEGVERSE_ORG_LEDGER_GIT_DIR", "STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_STORE",
                 "STEGVERSE_ORG_LEDGER_GIT_REF", "STEGVERSE_ORG_LEDGER_GIT_REMOTE", "STEGVERSE_ORG_LEDGER_GIT_CUSTODY",
                 "STEGVERSE_ORG_LEDGER_ROOT")
        saved = {n: os.environ.get(n) for n in names}
        for n in names:
            os.environ.pop(n, None)
        os.environ["STEGVERSE_ORG_LEDGER_GIT_DIR"] = str(self.bare)
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = f"git+{self.bare}#{REF}:{NAMESPACE}"

        def restore():
            contract["organization_ledger"] = previous
            for n, v in saved.items():
                if v is None:
                    os.environ.pop(n, None)
                else:
                    os.environ[n] = v
        self.addCleanup(restore)

    def tip(self):
        return _git(self.bare, "rev-parse", REF).decode().strip()

    def objects(self, commit, *paths):
        out = {}
        for path in paths:
            try:
                out[commit + ":" + path] = _git(self.bare, "cat-file", "blob", f"{commit}:{path}")
            except subprocess.CalledProcessError:
                pass
        return out

    def ledger_objects(self, result):
        commit = self.tip()
        return commit, self.objects(commit, ledger_store.HEAD_KEY, result["organization_receipt_key"],
                                    result["repository_receipt_source_key"])


class AppendRoundTrip(GitLedger):
    def test_append_round_trips_and_keeps_history(self):
        result = svc.append_check_receipt(check_receipt(), hb_epoch=40)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertIs(result["organization_receipt_preserves_repository_receipt"], True)
        self.assertEqual(result["hb_epoch"], 40)
        replay = svc.append_check_receipt(check_receipt(), hb_epoch=40)
        self.assertIs(replay["transition_replayed"], True)
        self.assertEqual(replay["organization_receipt_sha256"], result["organization_receipt_sha256"])
        self.assertEqual(replay["repository_receipt_sha256"], result["repository_receipt_sha256"])
        self.assertEqual(_git(self.bare, "merge-base", "--is-ancestor", self.seed, REF), b"")
        self.assertEqual(_git(self.bare, "rev-parse", f"{REF}:MARKER"), _git(self.bare, "rev-parse", f"{self.seed}:MARKER"))

        org_store = ledger_store.GitLedgerStore(self.bare, REF, custody="PRIVATE")
        org = org_store.get(result["organization_receipt_key"])
        repo = org_store.get(result["repository_receipt_source_key"])
        self.assertTrue(result["organization_receipt_key"].startswith("receipts/"))
        self.assertTrue(result["repository_receipt_source_key"].startswith("source-receipts/"))
        self.assertEqual(org["schema"], "stegverse.organization-transition-receipt/v1")
        self.assertEqual(org["boundary_evidence"]["operation"], "sv_check_receipt")
        self.assertEqual(org["repo_receipt_sha256"], repo["receipt_sha256"])
        self.assertEqual(repo["schema"], "stegverse.repo-transition-receipt/v1")
        self.assertEqual(repo["evidence"], check_receipt())  # complete receipt, $.evidence.schema only, no added marker
        self.assertNotIn("kind", repo["evidence"])
        for row in (org, repo):
            self.assertIs(row["hb_reference"]["derived_from_clock"], False)
            self.assertEqual(row["hb_reference"]["epoch"], 40)
        # the same field layout as P1's fixtures (emit.py:116-117, aggregate_repo_transition.py:1073-1089)
        fixture_repo = fx.repo_receipt(check_receipt(), 40)
        fixture_org = fx.org_receipt(fixture_repo, 40, boundary_evidence=fx.boundary())
        self.assertEqual(set(repo), set(fixture_repo))
        self.assertEqual(set(org) - {"custody_authority_basis", "custody_exclusivity_attestation_sha256"},
                         set(fixture_org) - {"custody_authority_basis", "custody_exclusivity_attestation_sha256"})

        reader = self.work / "reader.git"
        subprocess.run(["git", "init", "--bare", "-q", str(reader)], check=True)
        subprocess.run(["git", "--git-dir", str(reader), "fetch", "-q", str(self.bare), f"+{REF}:{REF}"], check=True)
        bound = svc.bind_check_receipt(f"git+{reader}#{REF}", result)
        self.assertEqual(bound["disposition"], "ALLOW", bound)
        chain = readback.readback(f"git+{reader}#{REF}")
        self.assertEqual(chain["disposition"], "ALLOW")
        self.assertIn(result["organization_receipt_sha256"], [r["receipt_sha256"] for r in chain["chain"]])

    def test_seal_verifies_and_a_broken_seal_is_not_ledgered(self):
        result = svc.append_check_receipt(check_receipt(), hb_epoch=40)
        commit, objs = self.ledger_objects(result)
        for path in (result["organization_receipt_key"], result["repository_receipt_source_key"]):
            doc = json.loads(objs[commit + ":" + path])
            self.assertTrue(wi._self_verifies(doc), path)
            self.assertTrue(readback.self_verifies(doc), path)
        tampered = dict(objs)
        key = commit + ":" + result["repository_receipt_source_key"]
        doc = json.loads(tampered[key])
        doc["evidence"]["verifier_ref"] = "edited after sealing"
        tampered[key] = json.dumps(doc).encode()
        ref = "%s@%s:%s" % (REF, commit, result["organization_receipt_key"])
        rec = _p1_refusal(lambda: wi.derive_issue_from_check_receipt(
            tampered, ref, observed_base={"registry_generation": 319, "ledger_head": commit}))
        self.assertEqual(rec["failure_code"], "SOURCE_RECEIPT_NOT_LEDGERED")
        missing = {k: v for k, v in objs.items() if k != key}
        rec = _p1_refusal(lambda: wi.derive_issue_from_check_receipt(
            missing, ref, observed_base={"registry_generation": 319, "ledger_head": commit}))
        self.assertEqual(rec["failure_code"], "SOURCE_RECEIPT_NOT_LEDGERED")


class P1ReadersDerive(GitLedger):
    def test_p1_readers_derive_an_issue_and_the_base_epoch(self):
        result = svc.append_check_receipt(check_receipt(), hb_epoch=40)
        commit, objs = self.ledger_objects(result)
        ref = "%s@%s:%s" % (REF, commit, result["organization_receipt_key"])
        issue = wi.derive_issue_from_check_receipt(objs, ref, observed_base={"registry_generation": 319, "ledger_head": commit})
        self.assertEqual(issue["record_mode"], "NATIVE")
        self.assertEqual(issue["source_receipt"]["receipt_sha256"], result["organization_receipt_sha256"])
        self.assertEqual(issue["disposition"]["failure_code"], "WORKFLOW_SURFACE_UNREGISTERED")
        self.assertEqual(issue["violated_invariant"]["rule_id"].split("#checks.")[1], "workflow-surface-registered")
        self.assertTrue(issue["issue_id"].startswith("svi:"))
        self.assertEqual(wi.base_ledger_head_epoch(commit, objs), 40)
        self.assertEqual(wi.verify_native_hb_epoch(issue, objs)["disposition"], "ALLOW")
        again = wi.derive_issue_from_check_receipt(objs, ref, observed_base={"registry_generation": 319, "ledger_head": commit})
        self.assertEqual(again["issue_id"], issue["issue_id"])

    def test_a_self_closure_on_the_same_ledger_is_not_a_check_receipt(self):
        closure = ingress.self_close(ingress.diagnostic_payload("not-a-check"), registry=REGISTRY,
                                     packet_id="not-a-check-packet", hb_epoch=40)
        self.assertEqual(closure["disposition"], "ALLOW", closure)
        commit = self.tip()
        org_key = ledger_store.receipt_key(closure["organization_receipt_sha256"])
        objs = self.objects(commit, ledger_store.HEAD_KEY, org_key, ledger_store.source_key(closure["repository_receipt_sha256"]))
        rec = _p1_refusal(lambda: wi.derive_issue_from_check_receipt(
            objs, "%s@%s:%s" % (REF, commit, org_key), observed_base={"registry_generation": 319, "ledger_head": commit}))
        self.assertEqual(rec["failure_code"], "LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT")


class Refusals(GitLedger):
    def _assert_nothing_written(self, result, code, disposition="FAIL_CLOSED"):
        self.assertEqual(result["disposition"], disposition, result)
        self.assertEqual(result["failure_code"], code)
        for field in svc.SIX_FIELDS:
            self.assertTrue(isinstance(result[field], str) and result[field], field)
        self.assertIs(result["consequence_committed"], False)
        self.assertEqual(self.tip(), self.seed)

    def test_non_check_evidence_is_refused_before_any_write(self):
        for bad in ({"communication_id": "x", "disposition": "ALLOW"}, ["not", "an", "object"], None,
                    check_receipt(schema="stegverse.sv_check_receipt.v0"),
                    dict(check_receipt(), kind="sv_check_receipt", schema=None)):
            self._assert_nothing_written(svc.append_check_receipt(bad, hb_epoch=40), "LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT")

    def test_invalid_check_receipt_is_refused_before_any_write(self):
        for bad in (check_receipt(head_sha=None), check_receipt(failure_code=None), check_receipt(check_id="not-declared"),
                    dict(check_receipt(), kind="sv_check_receipt"),
                    check_receipt(change_digest="sha256:short")):
            result = svc.append_check_receipt(bad, hb_epoch=40)
            self._assert_nothing_written(result, "LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT")
            self.assertTrue(result["schema_errors"])

    def test_an_absent_null_or_sentinel_epoch_is_unobserved_on_either_side(self):
        for bad in (None, "", "null", "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"):
            result = svc.append_check_receipt(check_receipt(), hb_epoch=bad)
            self._assert_nothing_written(result, "HB_EPOCH_SOURCE_UNOBSERVED")
            self.assertEqual(result["shared_rule_sha256"], svc.SHARED_RULE_SHA256)
        for bad in ("ABSENT", None, "", "null", "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"):
            receipt = check_receipt()
            if bad == "ABSENT":
                del receipt["hb_epoch"]
            else:
                receipt["hb_epoch"] = bad
            self._assert_nothing_written(svc.append_check_receipt(receipt, hb_epoch=40), "HB_EPOCH_SOURCE_UNOBSERVED")

    def test_a_malformed_append_epoch_is_a_mismatch_and_no_clock_is_read(self):
        for bad in (True, False, 31, 0, -40, "40", 40.0, "unknown", "NULL", " null", "None"):
            result = svc.append_check_receipt(check_receipt(), hb_epoch=bad)
            self._assert_nothing_written(result, "HB_EPOCH_MISMATCH", disposition="DENY")
            self.assertEqual(result["failed_predicate"], "CHECK_RECEIPT_HB_EPOCH_EQUALS_APPEND_HB_EPOCH")

    def test_a_malformed_receipt_epoch_is_a_mismatch(self):
        for bad in ("31", "+40", " 40", "4_0", "40.0", "\uff14\uff10", True, False, 40, 40.0, "unknown", "NULL", "None"):
            result = svc.append_check_receipt(check_receipt(hb_epoch=bad), hb_epoch=40)
            self._assert_nothing_written(result, "HB_EPOCH_MISMATCH", disposition="DENY")

    def test_a_receipt_epoch_other_than_the_append_epoch_is_denied(self):
        for receipt_epoch, append_epoch in (("41", 40), ("40", 41), ("1024", 40)):
            result = svc.append_check_receipt(check_receipt(hb_epoch=receipt_epoch), hb_epoch=append_epoch)
            self._assert_nothing_written(result, "HB_EPOCH_MISMATCH", disposition="DENY")
            self.assertEqual(result["failed_predicate"], "CHECK_RECEIPT_HB_EPOCH_EQUALS_APPEND_HB_EPOCH")

    def test_parity_with_p1_verify_admission_hb_epoch(self):
        """The receipt's hb_epoch against the append epoch, versus P1's supplied hb_epoch (an SV_CHANGE record's hb_epoch,
        an epoch-source field) against a sealed readback slot (P1 #3264 head f28c3a76): identical disposition and code
        in every case. HB_EPOCH_NOT_CROSS_CHECKED (an optional cross-check) has no counterpart here: both of this
        operation's fields are epoch sources."""
        head = "a" * 40

        def p1(supplied, sealed=40):
            rb = {"schema": wi.BASE_STATE_READBACK_SCHEMA, "disposition": "ALLOW", "base_ref": {"ledger_head": head},
                  "hb_epoch_source": {"ledger_head": head, "field": wi.HB_EPOCH_SOURCE_FIELD, "derived_from_clock": False,
                                      "receipt": "receipts/" + "b" * 64 + ".json"},
                  "hb_epoch": str(sealed),
                  "cross_checked": False, "detail": wi.NOT_CROSS_CHECKED_DETAIL}  # the pinned producer's omitted-flag ALLOW shape
            rb["result_sha256"] = wi.sha(rb)
            try:
                return wi.verify_admission_hb_epoch(supplied, rb, head)["disposition"], None
            except wi.Refusal as refusal:
                return refusal.record["disposition"], refusal.record["failure_code"]

        def mine(supplied, append=40):
            receipt = check_receipt(hb_epoch=supplied)
            result = svc._epoch_refusal(receipt, append)
            return ("ALLOW", None) if result is None else (result["disposition"], result["failure_code"])

        cases = (None, "", "null", "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED",
                 "40", "41", "1024", "31", "0", "+40", " 40", "40 ", "4_0", "40.0", "\uff14\uff10", "NULL", "None", " null",
                 True, False, 40, 41, 31, 40.0, "unknown", [], {})
        seen = set()
        for value in cases:
            self.assertEqual(mine(value), p1(value), repr(value))
            seen.add(mine(value))
        self.assertEqual(seen, {("ALLOW", None), ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"), ("DENY", "HB_EPOCH_MISMATCH")})
        self.assertEqual(tuple(svc.UNOBSERVED_EPOCH_VALUES), tuple(wi.SUPPLIED_EPOCH_UNOBSERVED_VALUES))
        # P1's optional cross-check left out is ALLOW, not comparable here
        self.assertEqual(p1(wi.HB_EPOCH_NOT_CROSS_CHECKED), ("ALLOW", None))

    def test_a_clock_derived_source_is_unobserved_in_both(self):
        head = "a" * 40
        rb = {"schema": wi.BASE_STATE_READBACK_SCHEMA, "disposition": "ALLOW", "base_ref": {"ledger_head": head},
              "hb_epoch_source": {"ledger_head": head, "field": wi.HB_EPOCH_SOURCE_FIELD, "derived_from_clock": True,
                                  "receipt": "receipts/" + "b" * 64 + ".json"},
              "hb_epoch": "40",
              "cross_checked": False, "detail": wi.NOT_CROSS_CHECKED_DETAIL}  # the pinned producer's omitted-flag ALLOW shape
        rb["result_sha256"] = wi.sha(rb)
        with self.assertRaises(wi.Refusal) as caught:
            wi.verify_admission_hb_epoch("40", rb, head)
        self.assertEqual((caught.exception.record["disposition"], caught.exception.record["failure_code"]),
                         ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"))
        clock = {"schema": "x", "hb_reference": kernel_ref(40, derived=True)}
        clock["receipt_sha256"] = svc.sha(dict(clock))
        self.assertEqual((svc._stored_epoch_refusal(clock, 40)["disposition"], svc._stored_epoch_refusal(clock, 40)["failure_code"]),
                         ("FAIL_CLOSED", "HB_EPOCH_SOURCE_UNOBSERVED"))

    def test_an_unpinned_kernel_rule_is_unobserved(self):
        from unittest import mock
        with mock.patch.object(svc, "KERNEL_RULE_SHA256", "0" * 64):
            self._assert_nothing_written(svc.append_check_receipt(check_receipt(), hb_epoch=40), "HB_EPOCH_SOURCE_UNOBSERVED")

    def test_a_clock_derived_or_unsealed_stored_epoch_is_unobserved(self):
        clock = {"schema": "x", "hb_reference": kernel_ref(40, derived=True)}
        clock["receipt_sha256"] = svc.sha({k: v for k, v in clock.items()})
        self.assertEqual(svc._stored_epoch_refusal(clock, 40)["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")
        unsealed = {"schema": "x", "hb_reference": kernel_ref(40), "receipt_sha256": "sha256:" + "0" * 64}
        self.assertEqual(svc._stored_epoch_refusal(unsealed, 40)["failure_code"], "HB_EPOCH_SOURCE_UNOBSERVED")
        good = {"schema": "x", "hb_reference": kernel_ref(40)}
        good["receipt_sha256"] = svc.sha(dict(good))
        self.assertIsNone(svc._stored_epoch_refusal(good, 40))
        self.assertEqual(svc._stored_epoch_refusal(good, 41)["failure_code"], "HB_EPOCH_MISMATCH")

    def test_an_undeclared_check_command_is_refused_before_any_write(self):
        from unittest import mock
        undeclared = {"offline_command": "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED", "command_paths": []}
        with mock.patch.dict(wi.REQUIRED_CHECKS["checks"], {"workflow-surface-registered": undeclared}):
            self.assertFalse(svc.command_declared("workflow-surface-registered"))
            self.assertFalse(wi.command_declared("workflow-surface-registered"))
            for receipt in (check_receipt(), check_receipt(disposition="ALLOW", failure_code=None, failed_predicate=None,
                                                           required_evidence_or_repair=None, retry_entrypoint=None,
                                                           owning_existing_goal=None, next_attempt=None)):
                result = svc.append_check_receipt(receipt, hb_epoch=40)
                self._assert_nothing_written(result, "CHECK_COMMAND_UNDECLARED")
                self.assertEqual(result["failed_predicate"], "CHECK_HAS_OFFLINE_COMMAND")
            # the verifier's own FAIL_CLOSED CHECK_COMMAND_UNDECLARED receipt is the one receipt it may append (P1's rule)
            own = check_receipt(failure_code="CHECK_COMMAND_UNDECLARED", failed_predicate="CHECK_HAS_OFFLINE_COMMAND")
            self.assertEqual(svc.append_check_receipt(own, hb_epoch=40)["disposition"], "ALLOW")

    def test_the_command_rule_is_p1s_for_every_declared_check_including_the_gate(self):
        ids = set(wi.REQUIRED_CHECKS["checks"]) | set(wi.GATE_CHECKS)
        self.assertIn(GATE, ids)
        self.assertNotIn(GATE, wi.REQUIRED_CHECKS["checks"])  # declared by the NWI-S0 manifest, not the row
        self.assertEqual(set(svc.CHECK_RECEIPT_SCHEMA["properties"]["check_id"]["enum"]), ids)
        for check_id in ids:
            self.assertTrue(svc.command_declared(check_id), check_id)
            self.assertEqual(svc.command_declared(check_id), wi.command_declared(check_id), check_id)

    def test_p1_oracle_wrong_operation_or_evidence_and_missing_receipt(self):
        commit = "c" * 40
        good = fx.repo_receipt(check_receipt(), 40)
        cases = [
            (fx.org_receipt(good, 40, boundary_evidence=fx.boundary("intr-destination")), good, "LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT"),
            (fx.org_receipt(fx.repo_receipt({"communication_id": "x"}, 40), 40, boundary_evidence=fx.boundary()),
             fx.repo_receipt({"communication_id": "x"}, 40), "LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT"),
            (fx.org_receipt(good, 40, boundary_evidence=fx.boundary()), None, "SOURCE_RECEIPT_NOT_LEDGERED"),
        ]
        for org, repo, code in cases:
            rec = _p1_refusal(lambda: wi.derive_issue_from_check_receipt(
                fx.ledger_objects(commit, org, repo), fx.org_ref(commit, org),
                observed_base={"registry_generation": 319, "ledger_head": commit}))
            self.assertEqual(rec["failure_code"], code)


def _blob(data):
    return subprocess.run(["git", "hash-object", "--stdin"], input=data, capture_output=True, check=True).stdout.decode().strip()


def subject(ledger_head, **override):
    s = {"repository": LEDGER_REPOSITORY, "stage_id": "NWI-S0",
         "manifest_blob": _blob((VENDOR / "data/sv-work-items/stages/NWI-S0.json").read_bytes()),
         "evaluated_commit": "c" * 40, "base_ref": {"registry_generation": 319, "ledger_head": ledger_head}}
    s.update(override)
    return s


def base_state_readback(ledger_head, epoch="40", repository=LEDGER_REPOSITORY, **override):
    """A sealed ALLOW Labs#3266 base-state readback of `repository`'s own ledger at `ledger_head` (not fixture_only)."""
    rb = {"schema": wi.BASE_STATE_READBACK_SCHEMA, "disposition": "ALLOW", "repository": repository,
          "base_ref": {"registry_generation": 319, "ledger_head": ledger_head},
          "hb_epoch_source": {"ledger_head": ledger_head, "field": wi.HB_EPOCH_SOURCE_FIELD, "derived_from_clock": False,
                              "receipt": "receipts/" + "d" * 64 + ".json"},
          "hb_epoch": epoch,
          "cross_checked": False, "detail": wi.NOT_CROSS_CHECKED_DETAIL}  # the pinned producer's omitted-flag ALLOW shape
    rb.update(override)
    rb["result_sha256"] = wi.sha(rb)
    return rb


def gate_receipt(subj, disposition="FAIL_CLOSED", **override):
    r = {"schema": "stegverse.sv_check_receipt.v1", "check_id": GATE, "disposition": disposition,
         "change_digest": wi.stage_evaluation_digest(subj), "head_sha": subj["evaluated_commit"], "hb_epoch": "40",
         "verifier_ref": S1_RUN}
    if disposition != "ALLOW":
        r.update({"failure_code": "STAGE_EVIDENCE_UNOBSERVED", "failed_predicate": "UNKNOWN_NEVER_YIELDS_PASS",
                  "required_evidence_or_repair": "a receipted outcome for every exit predicate",
                  "retry_entrypoint": "resident-runtime/stage_gate.py::evaluate_gate",
                  "owning_existing_goal": "StegVerse-org/.github#163", "next_attempt": "re-evaluate with the receipts; nothing moved"})
    r.update(override)
    return {k: v for k, v in r.items() if v is not None}


class StageGateReceipts(GitLedger):
    def _append(self, receipt, subj, rb, repository=LEDGER_REPOSITORY, epoch=40):
        return svc.append_check_receipt(receipt, hb_epoch=epoch, subject=subj, readback=rb, ledger_repository=repository)

    def _refused(self, result, code, disposition="FAIL_CLOSED"):
        self.assertEqual((result["disposition"], result["failure_code"]), (disposition, code), result)
        for field in svc.SIX_FIELDS:
            self.assertTrue(isinstance(result[field], str) and result[field], field)
        self.assertIs(result["consequence_committed"], False)
        self.assertEqual(self.tip(), self.seed)

    def test_a_gate_receipt_appends_round_trips_and_p1_derives_an_issue(self):
        subj = subject(self.seed)
        receipt = gate_receipt(subj)
        self.assertEqual(wi.validate_gate_receipt(receipt, subj, base_state_readback(self.seed))["disposition"], "ALLOW")
        result = self._append(receipt, subj, base_state_readback(self.seed))
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertTrue(result["organization_receipt_key"].startswith("receipts/"))
        self.assertTrue(result["repository_receipt_source_key"].startswith("source-receipts/"))
        replay = self._append(receipt, subj, base_state_readback(self.seed))
        self.assertIs(replay["transition_replayed"], True)
        commit, objs = self.ledger_objects(result)
        repo = json.loads(objs[commit + ":" + result["repository_receipt_source_key"]])
        self.assertEqual(repo["evidence"], receipt)
        self.assertEqual(repo["evidence"]["change_digest"], wi.stage_evaluation_digest(subj))
        self.assertEqual(repo["evidence"]["head_sha"], subj["evaluated_commit"])
        reader = self.work / "reader.git"
        subprocess.run(["git", "init", "--bare", "-q", str(reader)], check=True)
        subprocess.run(["git", "--git-dir", str(reader), "fetch", "-q", str(self.bare), f"+{REF}:{REF}"], check=True)
        self.assertEqual(svc.bind_check_receipt(f"git+{reader}#{REF}", result)["disposition"], "ALLOW")
        ref = "%s@%s:%s" % (REF, commit, result["organization_receipt_key"])
        issue = wi.derive_issue_from_check_receipt(objs, ref, observed_base={"registry_generation": 319, "ledger_head": commit})
        manifest = "data/sv-work-items/stages/NWI-S0.json"
        self.assertEqual(issue["record_mode"], "NATIVE")
        self.assertEqual(issue["surface"]["path"], manifest)
        self.assertEqual(issue["violated_invariant"]["rule_id"], "NWI-S0#exit_gate_check." + GATE)
        self.assertEqual(issue["disposition"]["failure_code"], "STAGE_EVIDENCE_UNOBSERVED")
        self.assertEqual(issue["source_receipt"]["receipt_sha256"], result["organization_receipt_sha256"])
        self.assertEqual(wi.verify_native_hb_epoch(issue, objs)["disposition"], "ALLOW")
        again = wi.derive_issue_from_check_receipt(objs, ref, observed_base={"registry_generation": 319, "ledger_head": commit})
        self.assertEqual(again["issue_id"], issue["issue_id"])

    def test_a_passing_gate_receipt_appends_and_derives_no_issue(self):
        subj = subject(self.seed)
        result = self._append(gate_receipt(subj, "ALLOW"), subj, base_state_readback(self.seed))
        self.assertEqual(result["disposition"], "ALLOW", result)
        commit, objs = self.ledger_objects(result)
        rec = _p1_refusal(lambda: wi.derive_issue_from_check_receipt(
            objs, "%s@%s:%s" % (REF, commit, result["organization_receipt_key"]),
            observed_base={"registry_generation": 319, "ledger_head": commit}))
        self.assertEqual((rec["disposition"], rec["failure_code"]), ("DENY", "CHECK_RECEIPT_NOT_FAILING"))

    def test_an_invalid_subject_is_refused_before_any_write(self):
        good = subject(self.seed)
        receipt = gate_receipt(good)
        for bad in (None, {}, dict(good, stage_id="S0"), dict(good, evaluated_commit="short"),
                    dict(good, manifest_blob="x"), dict(good, base_ref={"ledger_head": self.seed}),
                    dict(good, repository="not a repo"), dict(good, extra="field")):
            self._refused(self._append(receipt, bad, base_state_readback(self.seed)), "STAGE_EVALUATION_SUBJECT_UNOBSERVED")
        self._refused(self._append(receipt, dict(good, stage_id="NWI-S1"), base_state_readback(self.seed)),
                      "CHECK_NOT_PART_OF_STAGE_EVALUATION")

    def test_a_gate_receipt_without_a_subject_is_refused(self):
        receipt = gate_receipt(subject(self.seed))
        self._refused(svc.append_check_receipt(receipt, hb_epoch=40), "STAGE_EVALUATION_SUBJECT_UNOBSERVED")

    def test_a_digest_or_commit_not_bound_to_the_subject_is_refused(self):
        subj = subject(self.seed)
        rb = base_state_readback(self.seed)
        other = subject(self.seed, evaluated_commit="e" * 40)
        for receipt in (gate_receipt(subj, change_digest="sha256:" + "f" * 64), gate_receipt(subj, change_digest=wi.stage_evaluation_digest(other)),
                        gate_receipt(subj, head_sha="e" * 40)):
            out = self._append(receipt, subj, rb)
            self._refused(out, "CHECK_SKIPPED_OR_UNOBSERVED")

    def test_the_gate_epoch_binds_the_subject_repositorys_readback(self):
        subj = subject(self.seed)
        receipt = gate_receipt(subj)
        self._refused(self._append(receipt, subj, None), "HB_EPOCH_SOURCE_UNOBSERVED")
        self._refused(self._append(receipt, subj, base_state_readback(self.seed, repository="StegVerse-org/.github")),
                      "HB_EPOCH_SOURCE_UNOBSERVED")
        self._refused(self._append(receipt, subj, base_state_readback(self.seed, fixture_only=True)), "HB_EPOCH_SOURCE_UNOBSERVED")
        self._refused(self._append(receipt, subj, base_state_readback("f" * 40)), "HB_EPOCH_SOURCE_UNOBSERVED")
        self._refused(self._append(receipt, subj, base_state_readback(self.seed, epoch="41")), "HB_EPOCH_MISMATCH", "DENY")

    def test_a_gate_receipt_goes_only_to_the_subject_repositorys_own_ledger(self):
        subj = subject(self.seed)
        for repository in ("StegVerse-org/.github", None):
            self._refused(self._append(gate_receipt(subj), subj, base_state_readback(self.seed), repository=repository),
                          "STAGE_EVALUATION_LEDGER_NOT_SUBJECT_REPOSITORY")


def kernel_ref(epoch, derived=False):
    ref = svc.kernel.hb_reference(epoch=epoch)
    return dict(ref, derived_from_clock=True) if derived else ref


class Declarations(unittest.TestCase):
    def test_shared_rule_hash_and_pins(self):
        import hashlib
        import inspect
        # line-independent: the function's own text (ad8ff529) and its ast segment (c9192134), wherever it sits
        source = inspect.getsource(svc.kernel.supplied_epoch_failure)
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),
                         "ad8ff52936d5bcd9a2ad6caceb2d9a637a099518989b34bbb3370301c7a4cce2")
        self.assertEqual(svc.supplied_epoch_rule_sha256((ROOT / "org-kernel" / "kernel.py").read_text(encoding="utf-8")),
                         svc.SHARED_RULE_SHA256)
        self.assertEqual(svc.KERNEL_RULE_SHA256, svc.SHARED_RULE_SHA256)
        self.assertEqual(wi.SUPPLIED_EPOCH_RULE_SHA256, svc.SHARED_RULE_SHA256)
        self.assertEqual(wi.KERNEL_RULE_SHA256, svc.SHARED_RULE_SHA256)
        self.assertEqual(svc.P1_VENDOR, VENDOR)

    def test_vendored_p1_files_match_the_contract_manifest(self):
        """The manifest has its pinned sha256 (and blob); each vendored file the operation uses has its manifest sha256
        and blob; nothing else from the manifest is vendored. If P1's file is in this checkout, a used file must be
        byte-identical to the vendored one (drift is flagged only for used files); if absent, UNKNOWN. No network."""
        import hashlib
        raw = (VENDOR / svc.P1_MANIFEST).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), MANIFEST_SHA256)
        self.assertEqual(svc.P1_MANIFEST_SHA256, MANIFEST_SHA256)
        self.assertEqual(_blob(raw), "56116e48b7b2d4e66f73ba5859e6c1230a89a5d3")
        manifest = json.loads(raw)
        self.assertEqual(manifest["schema"], "stegverse.sv-contract-pins/v1")
        self.assertEqual(len(manifest["files"]), 43)
        self.assertNotIn(svc.P1_MANIFEST, manifest["files"])
        self.assertIsNone(svc.P1_PIN_FAILURE)
        vendored = sorted(p.relative_to(VENDOR).as_posix() for p in VENDOR.rglob("*") if p.is_file())
        self.assertEqual(vendored, sorted(set(svc.P1_USED_FILES) | {svc.P1_MANIFEST, "tests/sv_ledger_fixtures.py"}))
        for rel in svc.P1_USED_FILES:
            data = (VENDOR / rel).read_bytes()
            pin = manifest["files"][rel]
            self.assertEqual("sha256:" + hashlib.sha256(data).hexdigest(), pin["sha256"], rel)
            self.assertEqual(_blob(data), pin["blob"], rel)
            p1 = ROOT / rel
            comparison = ("IDENTICAL" if p1.read_bytes() == data else "DRIFT") if p1.is_file() else "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"
            print("drift comparison", rel, comparison)
            self.assertNotEqual(comparison, "DRIFT", "P1's " + rel + " drifted from the vendored manifest pin; re-vendor")
        # not in the manifest (test-only): pinned by its blob
        self.assertEqual(_blob((VENDOR / "tests" / "sv_ledger_fixtures.py").read_bytes()), FIXTURES_BLOB)
        for pin, sha in (("schemas/sv-check-receipt.v1.schema.json", "a4934cc1"), ("resident-runtime/sv_work_items.py", "94f56a0f")):
            self.assertTrue(manifest["files"][pin]["blob"].startswith(sha))

    def test_a_vendored_file_off_its_manifest_digest_refuses_every_append(self):
        from unittest import mock
        with mock.patch.object(svc, "P1_PIN_FAILURE", "resident-runtime/sv_work_items.py does not match its manifest digest"):
            out = svc.append_check_receipt(check_receipt(), hb_epoch=40)
        self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "P1_CONTRACT_PINS_UNVERIFIED"))
        self.assertIs(out["consequence_committed"], False)

    def test_the_operation_is_declared_and_the_schema_is_pinned(self):
        boundary = json.loads((ROOT / ".stegverse" / "organization-ledger-ingest" / "operations.json").read_text(encoding="utf-8"))
        declared = boundary["organization_ledger_writer_operations"]
        entry, = [e for e in declared if e["operation"] == svc.OPERATION_ID]
        self.assertEqual(entry["operation_module"], "resident-runtime/sv_check_receipt_append.py")
        self.assertEqual(entry["evidence_schema"], svc.CHECK_RECEIPT_SCHEMA_ID)
        self.assertIs(entry["ingress_capability"], False)
        self.assertEqual(svc.CHECK_RECEIPT_SCHEMA["$id"], wi.CHECK_RECEIPT_SCHEMA)
        self.assertEqual(svc.OPERATION_ID, wi.SV_CHECK_RECEIPT_OPERATION)
        self.assertEqual(svc.CHECK_RECEIPT_SCHEMA_PATH, VENDOR / "schemas" / "sv-check-receipt.v1.schema.json")
        self.assertEqual(_blob(svc.CHECK_RECEIPT_SCHEMA_PATH.read_bytes()), svc.CHECK_RECEIPT_SCHEMA_BLOB)
        self.assertEqual(svc.CHECK_RECEIPT_SCHEMA_BLOB, "a4934cc1afb5f9c65d12f4ab5ae29f462b76b3f3")
        self.assertIn(GATE, svc.CHECK_RECEIPT_SCHEMA["properties"]["check_id"]["enum"])

    def test_writer_invokes_the_operation_under_the_shared_lock_and_pr_verify_appends_nothing(self):
        text = WRITER.read_text(encoding="utf-8")
        self.assertIn("resident-runtime/sv_check_receipt_append.py append", text)
        self.assertIn("resident-runtime/sv_check_receipt_append.py readback", text)
        self.assertIn("concurrency:\n  group: organization-ledger\n  cancel-in-progress: false\n", text)
        self.assertNotIn("--force", text)
        self.assertNotIn("pull_request", text.split("\njobs:\n", 1)[1])
        pr = PR_FACING.read_text(encoding="utf-8")
        self.assertIn("tests/test_sv_check_receipt_append.py", pr)
        self.assertNotIn("sv_check_receipt_append.py append", pr)

    def test_files_touched_do_not_use_the_forbidden_word(self):
        token = "g" + "rant"
        for path in (ROOT / "resident-runtime" / "sv_check_receipt_append.py", Path(__file__)):
            self.assertNotIn(token, path.read_text(encoding="utf-8").lower(), path.name)


if __name__ == "__main__":
    unittest.main()
