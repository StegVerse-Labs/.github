"""sv_check_receipt: the org-ledger writer appends one NWI-S1 check receipt.

Temporary repositories only. Receipts here are exercise evidence on those
repositories, not records of the published organization ledger.

Oracle: P1's readers at StegVerse-Labs/.github#3264 head
fc19b5321bb37c5203fe9244441a268e72eaa67b, vendored test-only under
tests/vendor/p1_fc19b532/ (sv_work_items.py blob 689d3a76, required-checks.json
409264f1, lifecycle-transitions.json c66de6e8), with P1's tests/sv_ledger_fixtures.py
(blob 30a9fe89) byte-identical. org-kernel/kernel.py (ffec5d64) and
scripts/project_worker_claim_into_canonical_task.py (9573c5bb) are the same blobs
here as at that pin, so the vendored module runs over them through symlinks.
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
VENDOR = ROOT / "tests" / "vendor" / "p1_fc19b532"
P1_PIN = "fc19b5321bb37c5203fe9244441a268e72eaa67b"
WRITER = ROOT / ".github" / "workflows" / "organization-ledger-transition-writer.yml"
PR_FACING = ROOT / ".github" / "workflows" / "organization-ledger-transition.yml"
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

_P1_ROOT = tempfile.TemporaryDirectory()


def _p1():
    """P1's sv_work_items at the pin, over a temp root that holds the vendored files and links the identical blobs."""
    root = Path(_P1_ROOT.name)
    (root / "resident-runtime").mkdir(exist_ok=True)
    (root / "data" / "sv-work-items").mkdir(parents=True, exist_ok=True)
    (root / "resident-runtime" / "sv_work_items.py").write_bytes((VENDOR / "sv_work_items.py").read_bytes())
    for name in ("lifecycle-transitions.json", "required-checks.json"):
        (root / "data" / "sv-work-items" / name).write_bytes((VENDOR / name).read_bytes())
    for link in ("org-kernel", "scripts"):
        if not (root / link).exists():
            os.symlink(ROOT / link, root / link)
    return _module("sv_work_items_p1_fc19b532", root / "resident-runtime" / "sv_work_items.py")


wi = _p1()
fx = _module("sv_ledger_fixtures_p1", ROOT / "tests" / "sv_ledger_fixtures.py")


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
        replay = svc.append_check_receipt(check_receipt(), hb_epoch=41)
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
    def _assert_nothing_written(self, result, code):
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
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
                    check_receipt(hb_epoch="31"), dict(check_receipt(), kind="sv_check_receipt"),
                    check_receipt(change_digest="sha256:short")):
            result = svc.append_check_receipt(bad, hb_epoch=40)
            self._assert_nothing_written(result, "LEDGER_EVIDENCE_NOT_A_CHECK_RECEIPT")
            self.assertTrue(result["schema_errors"])

    def test_an_absent_or_invalid_epoch_fails_closed_and_no_clock_is_read(self):
        for bad in (None, True, 31, "40", 40.0):
            self._assert_nothing_written(svc.append_check_receipt(check_receipt(), hb_epoch=bad),
                                         "HB_EPOCH_UNSUPPLIED_OR_INVALID")

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


class Declarations(unittest.TestCase):
    def test_the_operation_is_declared_and_the_schema_is_pinned(self):
        boundary = json.loads((ROOT / "org-runtime" / "interlock-intr.json").read_text(encoding="utf-8"))
        declared = boundary["organization_ledger_writer_operations"]
        entry, = [e for e in declared if e["operation"] == svc.OPERATION_ID]
        self.assertEqual(entry["operation_module"], "resident-runtime/sv_check_receipt_append.py")
        self.assertEqual(entry["evidence_schema"], svc.CHECK_RECEIPT_SCHEMA_ID)
        self.assertIs(entry["ingress_capability"], False)
        self.assertEqual(svc.CHECK_RECEIPT_SCHEMA["$id"], wi.CHECK_RECEIPT_SCHEMA)
        self.assertEqual(svc.OPERATION_ID, wi.SV_CHECK_RECEIPT_OPERATION)
        raw = (ROOT / "schemas" / "sv-check-receipt.v1.schema.json").read_bytes()
        blob = subprocess.run(["git", "hash-object", "--stdin"], input=raw, capture_output=True, check=True).stdout.decode().strip()
        self.assertEqual(blob, "070f13f468558ca08aa5162a8f34431608fc1404")

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
