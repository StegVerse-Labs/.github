"""Writer for refs/stegverse/organization-ledger: diagnostic self-closure.

Temporary repositories only. Receipts in this module are exercise evidence on
those repositories. They are not records of the published organization ledger.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = "refs/stegverse/organization-ledger"
NAMESPACE = "repository-ledger/StegVerse-Labs/.github"
WORKFLOW = ROOT / ".github" / "workflows" / "organization-ledger-transition.yml"


def _module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ingress = _module("intr_destination_ingress_writer", "resident-runtime/intr_destination_ingress.py")
ledger_store = _module("ledger_store_writer", "resident-runtime/ledger_store.py")
readback = _module("organization_ledger_readback_writer",
                   "resident-runtime/organization_ledger_readback.py")

REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))
CONTRACT = json.loads((ROOT / ".stegverse/transition-ledger/contract.json").read_text(encoding="utf-8"))


def diagnostic(communication_id="self-closure-communication-001"):
    return ingress.diagnostic_payload(communication_id)


def _git(repo, *args, input_bytes=None):
    environment = os.environ.copy()
    environment.update({
        "GIT_AUTHOR_NAME": "ledger-history-seed",
        "GIT_AUTHOR_EMAIL": "seed@example.invalid",
        "GIT_COMMITTER_NAME": "ledger-history-seed",
        "GIT_COMMITTER_EMAIL": "seed@example.invalid",
    })
    completed = subprocess.run(
        ["git", "--git-dir", str(repo), *args],
        input=input_bytes, capture_output=True, env=environment, check=True,
    )
    return completed.stdout.decode().strip()


class PosixSelfClosure(unittest.TestCase):
    def setUp(self):
        self._work = tempfile.TemporaryDirectory()
        self.addCleanup(self._work.cleanup)
        self._previous = {}
        for name, value in (
            ("STEGVERSE_REPO_LEDGER_ROOT", str(Path(self._work.name) / "repo")),
            ("STEGVERSE_ORG_LEDGER_ROOT", str(Path(self._work.name) / "org")),
        ):
            self._previous[name] = os.environ.get(name)
            os.environ[name] = value
        self.addCleanup(self._restore)

    def _restore(self):
        for name, value in self._previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def receipts(self, variable, schema, transition_class=None):
        found = []
        root = Path(os.environ[variable])
        if not root.exists():
            return found
        for path in root.rglob("*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("schema") != schema:
                continue
            if transition_class is not None and record.get("transition_class") != transition_class:
                continue
            found.append(record)
        return found

    def test_self_closure_records_communication_id_on_both_ledgers(self):
        result = ingress.self_close(
            diagnostic(), registry=REGISTRY, packet_id="self-closure-packet", hb_epoch=40)
        self.assertEqual(result["disposition"], "ALLOW", result.get("detail"))
        self.assertIs(result["closed"], True)
        self.assertEqual(result["communication_id"], "self-closure-communication-001")
        self.assertIs(result["federation_directory_consulted"], False)
        self.assertIs(result["peer_enumerated"], False)
        self.assertIs(result["repository_receipt_observed"], True)
        self.assertIs(result["organization_receipt_observed"], True)
        self.assertIs(result["organization_receipt_preserves_repository_receipt"], True)
        repository, = self.receipts(
            "STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1",
            ingress.CLOSURE_CLASS)
        organization, = self.receipts(
            "STEGVERSE_ORG_LEDGER_ROOT", "stegverse.organization-transition-receipt/v1")
        self.assertEqual(repository["evidence"]["communication_id"], result["communication_id"])
        self.assertEqual(organization["boundary_evidence"]["communication_id"], result["communication_id"])
        self.assertEqual(organization["repo_receipt_sha256"], repository["receipt_sha256"])
        self.assertFalse(any(key.endswith("_authority") for key in result))

    def test_a_replay_returns_the_same_pair(self):
        first = ingress.self_close(
            diagnostic("replay-communication"), registry=REGISTRY,
            packet_id="replay-packet", hb_epoch=41)
        second = ingress.self_close(
            diagnostic("replay-communication"), registry=REGISTRY,
            packet_id="replay-packet", hb_epoch=42)
        self.assertIs(second["transition_replayed"], True)
        self.assertEqual(first["repository_receipt_sha256"], second["repository_receipt_sha256"])
        self.assertEqual(first["organization_receipt_sha256"], second["organization_receipt_sha256"])
        self.assertEqual(len(self.receipts(
            "STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1",
            ingress.CLOSURE_CLASS)), 1)

    def test_a_communication_id_that_is_not_a_token_is_refused_and_recorded(self):
        result = ingress.self_close(
            {"message_class": "ecosystem.communication", "communication_id": "has space",
             "body": {"schema": ingress.PAYLOAD_SCHEMA}},
            registry=REGISTRY, packet_id="refused-self-closure", hb_epoch=43)
        self.assertEqual(result["disposition"], "DENY")
        self.assertIs(result["closed"], False)
        self.assertEqual(result["failed_predicate"],
                         "SUBMISSION_CARRIES_THE_COMMUNICATION_ID_CLOSURE_CORRELATES_ON")
        self.assertEqual(len(self.receipts(
            "STEGVERSE_REPO_LEDGER_ROOT", "stegverse.repo-transition-receipt/v1",
            ingress.CLOSURE_REFUSED_CLASS)), 1)

    def test_the_operation_does_not_name_the_federation_directory(self):
        source = (ROOT / "resident-runtime" / "intr_destination_ingress.py").read_text(encoding="utf-8")
        self.assertNotIn("federation.json", source)
        self.assertNotIn("resolve_destination", source)


class GitRefSelfClosure(unittest.TestCase):
    def test_append_keeps_existing_history_and_reads_back_from_another_repository(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        bare = Path(work.name) / "ledger.git"
        subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
        marker = _git(bare, "hash-object", "-w", "--stdin", input_bytes=b"prior-history\n")
        already = _git(bare, "hash-object", "-w", "--stdin", input_bytes=b'{"kept":true}\n')
        index = Path(work.name) / "seed.index"
        environment_index = os.environ.get("GIT_INDEX_FILE")
        os.environ["GIT_INDEX_FILE"] = str(index)
        try:
            _git(bare, "read-tree", "--empty")
            _git(bare, "update-index", "--add", "--cacheinfo", f"100644,{marker},MARKER")
            _git(bare, "update-index", "--add", "--cacheinfo", f"100644,{already},receipts/already.json")
            tree = _git(bare, "write-tree")
        finally:
            if environment_index is None:
                os.environ.pop("GIT_INDEX_FILE", None)
            else:
                os.environ["GIT_INDEX_FILE"] = environment_index
        seed = _git(bare, "commit-tree", tree, "-m", "prior history")
        _git(bare, "update-ref", REF, seed)

        contract = ingress.organization_ledger.C
        previous = contract.get("organization_ledger")
        contract["organization_ledger"] = {
            "store": "git", "ref": REF, "custody": "PRIVATE", "propagate_target": None,
        }
        saved = {name: os.environ.get(name) for name in (
            "STEGVERSE_ORG_LEDGER_GIT_DIR", "STEGVERSE_REPO_LEDGER_ROOT",
            "STEGVERSE_ORG_LEDGER_STORE", "STEGVERSE_ORG_LEDGER_GIT_REF",
            "STEGVERSE_ORG_LEDGER_GIT_REMOTE", "STEGVERSE_ORG_LEDGER_GIT_CUSTODY",
            "STEGVERSE_ORG_LEDGER_ROOT",
        )}
        os.environ["STEGVERSE_ORG_LEDGER_GIT_DIR"] = str(bare)
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = f"git+{bare}#{REF}:{NAMESPACE}"
        for name in saved:
            if name not in ("STEGVERSE_ORG_LEDGER_GIT_DIR", "STEGVERSE_REPO_LEDGER_ROOT"):
                os.environ.pop(name, None)
        try:
            result = ingress.self_close(
                diagnostic("git-ref-communication"), registry=REGISTRY,
                packet_id="git-ref-packet", hb_epoch=44)
            replay = ingress.self_close(
                diagnostic("git-ref-communication"), registry=REGISTRY,
                packet_id="git-ref-packet", hb_epoch=45)
        finally:
            contract["organization_ledger"] = previous
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

        self.assertEqual(result["disposition"], "ALLOW", result.get("detail"))
        self.assertEqual(result["communication_id"], "git-ref-communication")
        self.assertIs(result["peer_enumerated"], False)
        self.assertIs(replay["transition_replayed"], True)
        self.assertEqual(replay["organization_receipt_sha256"], result["organization_receipt_sha256"])
        self.assertEqual(_git(bare, "rev-list", "--count", REF), "3")
        self.assertEqual(_git(bare, "merge-base", "--is-ancestor", seed, REF) or "ok", "ok")
        self.assertEqual(_git(bare, "rev-parse", f"{seed}:MARKER"), marker)
        self.assertEqual(_git(bare, "rev-parse", f"{REF}:MARKER"), marker)
        self.assertEqual(_git(bare, "rev-parse", f"{REF}:receipts/already.json"), already)

        org_store = ledger_store.GitLedgerStore(bare, REF, custody="PRIVATE")
        repo_store = ledger_store.GitLedgerStore(bare, REF, namespace=NAMESPACE, custody="PRIVATE")
        org_key = ledger_store.receipt_key(result["organization_receipt_sha256"])
        repo_key = ledger_store.receipt_key(result["repository_receipt_sha256"])
        organization = org_store.get(org_key)
        repository = repo_store.get(repo_key)
        self.assertEqual(organization["boundary_evidence"]["communication_id"], "git-ref-communication")
        self.assertEqual(repository["evidence"]["communication_id"], "git-ref-communication")
        self.assertIsNone(repo_store.get(org_key))
        self.assertNotEqual(
            org_store.get(ledger_store.HEAD_KEY)["receipt_sha256"],
            repo_store.get(ledger_store.HEAD_KEY)["receipt_sha256"],
        )

        reader = Path(work.name) / "reader.git"
        subprocess.run(["git", "init", "--bare", "-q", str(reader)], check=True)
        subprocess.run(
            ["git", "--git-dir", str(reader), "fetch", "-q", str(bare), f"+{REF}:{REF}"],
            check=True,
        )
        verified = readback.bind_closure(
            f"git+{reader}#{REF}", NAMESPACE, result)
        self.assertEqual(verified["disposition"], "ALLOW")
        self.assertEqual(verified["closure"]["communication_id"], "git-ref-communication")
        self.assertIs(verified["closure"]["communication_id_on_repository_receipt"], True)
        self.assertIs(verified["closure"]["communication_id_on_organization_receipt"], True)
        self.assertIs(verified["readback_writes"], False)
        self.assertGreaterEqual(verified["chain_length"], 1)
        self.assertEqual(verified["repository_ledger"]["chain_length"], 1)


class WriterContract(unittest.TestCase):
    def test_current_push_writer_refusals_keep_six_fields_and_code_specific_owners(self):
        import re
        text = WORKFLOW.read_text(encoding="utf-8")
        fields = ("failure_code", "failed_predicate", "required_evidence_or_repair",
                  "retry_entrypoint", "owning_existing_goal", "next_attempt")
        intr_owner = "StegVerse-Labs/.github#2897 / StegVerse-org/.github#162 P0-runtime-and-custody"
        push_owner = "ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001"
        owners = {
            "ORGANIZATION_LEDGER_REF_ABSENT": intr_owner,
            "ORGANIZATION_LEDGER_HISTORY_REWRITTEN": intr_owner,
            "ORGANIZATION_LEDGER_PUBLISH_RACE": intr_owner,
            "LEDGER_READBACK_CREDENTIAL_UNAVAILABLE": intr_owner,
            "PUSHED_RANGE_UNRESOLVED": push_owner,
            "NO_COMMITTED_PACKET_CHANGED": push_owner,
        }
        literals = re.findall(r"""echo\s*'(\{"disposition":"(?:FAIL_CLOSED|DENY)".*?\})'""", text)
        codes = []
        for literal in literals:
            message = json.loads(literal)
            with self.subTest(code=message.get("failure_code")):
                for field in fields:
                    self.assertIsInstance(message.get(field), str, (field, message))
                    self.assertTrue(message[field].strip(), (field, message))
                self.assertEqual(message["owning_existing_goal"], owners[message["failure_code"]])
                self.assertEqual(message["retry_entrypoint"], ".github/workflows/organization-ledger-transition.yml")
            codes.append(message["failure_code"])
        self.assertEqual(set(codes), set(owners))
        # All three committed operation paths (sv_check, sv_push_receipt and the append) must report the credential refusal.
        self.assertEqual(codes.count("LEDGER_READBACK_CREDENTIAL_UNAVAILABLE"), 3)
        self.assertEqual(len(codes), 8)
        # The old draft's closure-summary test must not bring retired execution back.
        self.assertNotIn("workflow_dispatch", text)
        self.assertNotIn("--self-close", text)
        self.assertNotIn("SELF_CLOSURE_INPUT_INVALID", text)
        self.assertNotIn("DISPATCH_HB_EPOCH_INVALID", text)

    def test_the_repository_chain_is_a_subtree_of_the_existing_ref(self):
        location = CONTRACT["repository_ledger_location"]
        self.assertEqual(location["ref"], REF)
        self.assertEqual(location["namespace"], NAMESPACE)
        self.assertIs(location["new_ledger_root"], False)
        self.assertEqual(readback.repository_namespace(), NAMESPACE)

    def test_a_namespace_may_not_shadow_the_organization_chain(self):
        with self.assertRaises(ledger_store.LedgerLocatorInvalid):
            ledger_store.parse_locator(f"git+/tmp/ledger#{REF}:receipts/shadow")

    def test_the_workflow_appends_pushes_and_reads_back_without_rewriting(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("on:\n  push:\n    branches: [main]\n", text)
        self.assertNotIn("workflow_dispatch", text)
        # The self-closure is retired (Rigel's rule, 2026-10-25: no InTr hop inside one organization).
        self.assertNotIn("--self-close", text)
        self.assertNotIn("self-closure-packet.json'", text.split("\njobs:", 1)[0].split("\non:", 1)[1])
        self.assertIn("readback", text)
        self.assertIn('git push origin "$LEDGER_REF:$LEDGER_REF"', text)
        self.assertNotIn("--force", text)
        self.assertNotIn("federation.json", text)
        self.assertIn('group: organization-ledger', text)
        self.assertIn("merge-base --is-ancestor", text)

    def test_files_touched_for_the_writer_do_not_use_the_forbidden_word(self):
        token = "g" + "rant"
        paths = [
            ROOT / "resident-runtime" / "intr_destination_ingress.py",
            ROOT / "resident-runtime" / "organization_ledger_readback.py",
            ROOT / "resident-runtime" / "ledger_store.py",
            ROOT / ".stegverse" / "transition-ledger" / "emit.py",
            ROOT / ".stegverse" / "transition-ledger" / "contract.json",
            ROOT / ".github" / "workflows" / "organization-ledger-transition.yml",
            ROOT / "tests" / "test_intr_destination_capability.py",
            ROOT / "tests" / "test_organization_ledger_transition_writer.py",
        ]
        for path in paths:
            self.assertNotIn(token, path.read_text(encoding="utf-8").lower(), path.name)


if __name__ == "__main__":
    unittest.main()
