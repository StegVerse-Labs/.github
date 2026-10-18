"""RTC-REPOSITORY-LEDGER-GENESIS-READBACK-013 against temporary git refs.

The fixture ledger is written by the real writer (intr_destination_ingress.self_close)
into a temporary bare repository, so the readback verifies genuine receipts.
Receipts here are exercise evidence on temporary repositories, not records of
any published organization ledger. No network is used: the fetch source is a
local path.
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
PRESENT_NAMESPACE = "repository-ledger/StegVerse-Labs/.github"


def _module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


component = _module("rtc013_component_under_test", "resident-runtime/repository_ledger_genesis_readback.py")
consumer = _module("rtc013_consumer_under_test", "scripts/consume_repository_ledger_genesis_readback_request.py")
ingress = _module("rtc013_fixture_ingress", "resident-runtime/intr_destination_ingress.py")
REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))
CONTRACT = ROOT / "data/reusable-evidence-validation-component-contract.json"
MODEL = ROOT / "data/reusable-task-component-model.json"


def _git(repo, *args, input_bytes=None, index=None):
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environment.update({
        "GIT_AUTHOR_NAME": "rtc013-fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "rtc013-fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    })
    if index is not None:
        environment["GIT_INDEX_FILE"] = str(index)
    completed = subprocess.run(["git", "--git-dir", str(repo), *args], input=input_bytes,
                               capture_output=True, env=environment, check=True)
    return completed.stdout.decode().strip()


def build_ledger(work: Path) -> tuple[Path, str, str]:
    """A bare repo whose ref holds a seed commit, then one real self-closure append.

    Returns (bare, seed_commit, head_commit). The repository chain lives in
    repository-ledger/StegVerse-Labs/.github; no other repository has a chain.
    """
    bare = work / "ledger.git"
    subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
    marker = _git(bare, "hash-object", "-w", "--stdin", input_bytes=b"prior-history\n")
    index = work / "seed.index"
    _git(bare, "read-tree", "--empty", index=index)
    _git(bare, "update-index", "--add", "--cacheinfo", f"100644,{marker},MARKER", index=index)
    seed = _git(bare, "commit-tree", _git(bare, "write-tree", index=index), "-m", "prior history")
    _git(bare, "update-ref", REF, seed)

    contract = ingress.organization_ledger.C
    previous = contract.get("organization_ledger")
    contract["organization_ledger"] = {"store": "git", "ref": REF, "custody": "PRIVATE", "propagate_target": None}
    names = ("STEGVERSE_ORG_LEDGER_GIT_DIR", "STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_STORE",
             "STEGVERSE_ORG_LEDGER_GIT_REF", "STEGVERSE_ORG_LEDGER_GIT_REMOTE",
             "STEGVERSE_ORG_LEDGER_GIT_CUSTODY", "STEGVERSE_ORG_LEDGER_ROOT")
    saved = {name: os.environ.get(name) for name in names}
    for name in names:
        os.environ.pop(name, None)
    os.environ["STEGVERSE_ORG_LEDGER_GIT_DIR"] = str(bare)
    os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = f"git+{bare}#{REF}:{PRESENT_NAMESPACE}"
    try:
        result = ingress.self_close(ingress.diagnostic_payload("rtc013-fixture"), registry=REGISTRY,
                                    packet_id="rtc013-fixture-packet", hb_epoch=44)
    finally:
        contract["organization_ledger"] = previous
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    assert result["disposition"] == "ALLOW", result
    return bare, seed, _git(bare, "rev-parse", REF)


def request(repository, expected, organization="StegVerse-Labs", **overrides):
    value = {
        "schema": component.REQUEST_SCHEMA, "component_id": component.COMPONENT_ID,
        "organization": organization, "repository": repository,
        "expected_organization_ledger_head": expected,
        "owning_existing_goal": "ORGANIZATION-BATCH-CUSTODY-REPLAY-001",
        "authority_effect": "NONE_READBACK_ONLY",
    }
    value.update(overrides)
    return value


SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


class LedgerFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._work = tempfile.TemporaryDirectory()
        cls.work = Path(cls._work.name)
        cls.bare, cls.seed, cls.head = build_ledger(cls.work)
        cls.before = _git(cls.bare, "for-each-ref")

    @classmethod
    def tearDownClass(cls):
        cls._work.cleanup()

    def tearDown(self):
        # A readback never writes to the source it fetched.
        self.assertEqual(_git(self.bare, "for-each-ref"), self.before)

    def run_readback(self, value, source=None):
        return component.evaluate(value, ledger_source=str(source or self.bare))

    def assert_fail_closed(self, result, code, predicate):
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], code)
        self.assertEqual(result["failed_predicate"], predicate)
        for field in SIX:
            self.assertTrue(isinstance(result.get(field), str) and result[field], field)
        self.assertEqual(result["authority_effect"], "NONE_READBACK_ONLY")
        self.assertIs(result["consequence_committed"], False)


class Positive(LedgerFixture):
    def test_genesis_present_at_the_bound_head_is_allowed(self):
        result = self.run_readback(request(".github", self.head))
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["observed_organization_ledger_head"], self.head)
        self.assertEqual(result["expected_head_relation"], "EQUAL")
        self.assertEqual(result["repository_namespace"], PRESENT_NAMESPACE)
        self.assertEqual(result["repository_chain_length"], 1)
        self.assertEqual(result["genesis_receipt_sha256"], result["repository_head_receipt_sha256"])
        self.assertIs(result["every_receipt_retained_in_organization_ledger"], True)
        self.assertEqual(result["authority_effect"], "NONE_READBACK_ONLY")
        self.assertNotIn("failure_code", result)

    def test_genesis_applied_after_the_bound_head_is_allowed_as_ancestor(self):
        # Applying a genesis appends to the ref, so a moved head must not mask it.
        result = self.run_readback(request(".github", self.seed))
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["expected_head_relation"], "ANCESTOR")
        self.assertIs(result["observed_head_equals_expected"], False)

    def test_identical_input_gives_an_identical_sealed_answer(self):
        first = self.run_readback(request(".github", self.head))
        second = self.run_readback(request(".github", self.head))
        self.assertEqual(first, second)
        self.assertTrue(first["decision_sha256"].startswith("sha256:"))


class Negative(LedgerFixture):
    def test_absent_genesis_at_the_bound_head_fails_closed_head_present(self):
        result = self.run_readback(request("StegVerse-SDK", self.head))
        self.assert_fail_closed(result, "REPOSITORY_LEDGER_GENESIS_NOT_RETAINED", "REPOSITORY_LEDGER_HEAD_PRESENT")
        self.assertEqual(result["repository_namespace"], "repository-ledger/StegVerse-Labs/StegVerse-SDK")
        self.assertEqual(result["observed_organization_ledger_head"], self.head)

    def test_absent_genesis_after_the_head_moved_names_the_new_head(self):
        result = self.run_readback(request("StegVerse-SDK", self.seed))
        self.assert_fail_closed(result, "EXPECTED_ORG_LEDGER_HEAD_MOVED", "EXPECTED_ORG_LEDGER_HEAD_MOVED")
        self.assertEqual(result["observed_organization_ledger_head"], self.head)
        self.assertEqual(result["expected_organization_ledger_head"], self.seed)
        self.assertIn(self.head, result["required_evidence_or_repair"])

    def test_bound_head_outside_the_ledger_history_fails_closed(self):
        result = self.run_readback(request(".github", "0" * 40))
        self.assert_fail_closed(result, "EXPECTED_ORG_LEDGER_HEAD_NOT_AN_ANCESTOR",
                                "EXPECTED_ORG_LEDGER_HEAD_IS_ANCESTOR_OF_OBSERVED")

    def test_unpublished_ref_fails_closed(self):
        empty = self.work / "empty.git"
        if not empty.exists():
            subprocess.run(["git", "init", "--bare", "-q", str(empty)], check=True)
        result = self.run_readback(request(".github", self.head), source=empty)
        self.assert_fail_closed(result, "ORGANIZATION_LEDGER_REF_NOT_FETCHED", "ORGANIZATION_LEDGER_REF_FRESH_FETCHED")
        self.assertNotIn("observed_organization_ledger_head", result)

    def test_tampered_repository_receipt_fails_closed(self):
        tampered = self.work / "tampered.git"
        subprocess.run(["git", "clone", "-q", "--bare", "--no-local", str(self.bare), str(tampered)], check=True)
        subprocess.run(["git", "--git-dir", str(tampered), "fetch", "-q", str(self.bare), f"+{REF}:{REF}"], check=True)
        listing = _git(tampered, "ls-tree", "-r", "--name-only", REF)
        path = next(p for p in listing.splitlines()
                    if p.startswith(PRESENT_NAMESPACE + "/receipts/") and p.endswith(".json"))
        body = json.loads(_git(tampered, "cat-file", "-p", f"{REF}:{path}"))
        body["transition_id"] = "altered-after-minting"
        blob = _git(tampered, "hash-object", "-w", "--stdin", input_bytes=(json.dumps(body) + "\n").encode())
        index = self.work / "tamper.index"
        _git(tampered, "read-tree", REF, index=index)
        _git(tampered, "update-index", "--cacheinfo", f"100644,{blob},{path}", index=index)
        commit = _git(tampered, "commit-tree", _git(tampered, "write-tree", index=index), "-p", REF, "-m", "tamper")
        _git(tampered, "update-ref", REF, commit)
        result = self.run_readback(request(".github", self.head), source=tampered)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], "ORGANIZATION_LEDGER_READBACK_REFUSED")
        for field in SIX:
            self.assertTrue(result.get(field), field)

    def test_malformed_requests_fail_closed_before_any_fetch(self):
        cases = {
            "wrong schema": request(".github", self.head, schema="x/v1"),
            "wrong component": request(".github", self.head, component_id="RTC-OTHER-001"),
            "short head": request(".github", "abc123"),
            "path traversal": request("..", self.head),
            "slash in repository": request("a/b", self.head),
            "dot organization": request(".github", self.head, organization=".x"),
            "authority claimed": request(".github", self.head, authority_effect="AUTHORIZES_APPEND"),
            "missing goal": request(".github", self.head, owning_existing_goal=""),
        }
        for label, value in cases.items():
            with self.subTest(label):
                result = component.evaluate(value, ledger_source="/nonexistent/never-fetched")
                self.assertEqual(result["failure_code"], "READBACK_REQUEST_INVALID")
                self.assertNotIn("observed_organization_ledger_head", result)
                for field in SIX:
                    self.assertTrue(result.get(field), field)
        self.assertEqual(component.evaluate([], ledger_source="/x")["failed_predicate"], "REQUEST_IS_OBJECT")

    def test_request_cannot_choose_the_fetch_source(self):
        value = request(".github", self.head, ledger_source=str(self.bare))
        self.assertEqual(component.validate_request(value)["organization"], "StegVerse-Labs")
        self.assertNotIn("ledger_source", component.validate_request(value))
        self.assertEqual(component.canonical_ledger_source("StegVerse-org"),
                         "https://github.com/StegVerse-org/.github.git")


class ManifestInvocation(LedgerFixture):
    def runtime_with(self, requests):
        runtime = Path(tempfile.mkdtemp(dir=self.work))
        target = runtime / consumer.REQUEST_DIR_REL
        target.mkdir(parents=True)
        for name, value in requests.items():
            (target / name).write_text(json.dumps(value), encoding="utf-8")
        return runtime

    def test_no_manifest_is_no_request(self):
        runtime = self.runtime_with({})
        self.assertEqual(consumer.consume(ROOT, runtime)["state"], "NO_REQUEST")
        self.assertFalse((runtime / consumer.OUTPUT_REL).exists())

    def test_each_manifest_answer_is_retained_once(self):
        runtime = self.runtime_with({
            "repository-ledger-genesis-readback-present.json": request(".github", self.head),
            "repository-ledger-genesis-readback-absent.json": request("StegVerse-SDK", self.head),
            "unrelated-request.json": {"schema": "other/v1"},
        })
        first = consumer.consume(ROOT, runtime, _ledger_source=str(self.bare))
        self.assertEqual(first["state"], "RECORDED_LOCAL_READBACK", first)
        self.assertEqual(first["request_count"], 2)
        by_ref = {row["request_ref"].rsplit("/", 1)[1]: row for row in first["readbacks"]}
        self.assertEqual(by_ref["repository-ledger-genesis-readback-present.json"]["disposition"], "ALLOW")
        self.assertEqual(by_ref["repository-ledger-genesis-readback-absent.json"]["failure_code"],
                         "REPOSITORY_LEDGER_GENESIS_NOT_RETAINED")
        retained = sorted((runtime / consumer.OUTPUT_REL).glob("*.json"))
        self.assertEqual(len(retained), 2)
        for path in retained:
            self.assertTrue(path.name.endswith("-" + self.head + ".json"))
        second = consumer.consume(ROOT, runtime, _ledger_source=str(self.bare))
        self.assertEqual(second["state"], "ALREADY_RECORDED")
        self.assertEqual([row["decision_sha256"] for row in second["readbacks"]],
                         [row["decision_sha256"] for row in first["readbacks"]])
        self.assertEqual(sorted((runtime / consumer.OUTPUT_REL).glob("*.json")), retained)

    def test_malformed_manifest_is_a_boundary_and_is_not_retained(self):
        runtime = self.runtime_with({"repository-ledger-genesis-readback-bad.json": {"schema": "x"}})
        result = consumer.consume(ROOT, runtime, _ledger_source=str(self.bare))
        self.assertEqual(result["state"], "BOUNDARY")
        self.assertFalse((runtime / consumer.OUTPUT_REL).exists())


class Declaration(unittest.TestCase):
    def component_declaration(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        return next(c for c in contract["components"] if c["component_id"] == component.COMPONENT_ID)

    def test_declared_in_the_evidence_validation_family_with_the_interface_minimum(self):
        model = json.loads(MODEL.read_text(encoding="utf-8"))
        self.assertEqual(model["component_families"]["evidence_validation"],
                         "data/reusable-evidence-validation-component-contract.json")
        declared = self.component_declaration()
        for field in model["component_interface_minimum"]:
            self.assertIn(field, declared)
        self.assertEqual(declared["authority_effect"], "NONE_READBACK_ONLY")
        self.assertTrue(all(value is False for value in declared["invariants"].values()))
        for code in ("REPOSITORY_LEDGER_GENESIS_NOT_RETAINED", "EXPECTED_ORG_LEDGER_HEAD_MOVED"):
            self.assertIn(code, declared["failure_classes"])

    def test_invoked_by_manifest_through_the_existing_dispatcher_and_refresh(self):
        declared = self.component_declaration()["implementation"]["manifest_invocation"]
        dispatcher = _module("rtc013_dispatcher", "scripts/dispatch_resident_execution_requests.py")
        self.assertIn(("repository_ledger_genesis_readback", declared["consumer"]), dispatcher.CONSUMERS)
        refresh_text = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
        self.assertIn(f'Path("{declared["consumer"]}")', refresh_text)
        manifest = ROOT / "control/resident-execution-request.d/repository-ledger-genesis-readback-stegverse-org-stegverse-sdk-001.json"
        value = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(component.validate_request(value)["repository"], "StegVerse-SDK")
        self.assertEqual(value["expected_organization_ledger_head"], "2acec0e1cfd158a6a3313ad422737caf41badda3")

    def test_no_clock_sleep_loop_or_new_dependency_in_component_or_consumer(self):
        for relative in ("resident-runtime/repository_ledger_genesis_readback.py",
                         "scripts/consume_repository_ledger_genesis_readback_request.py"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            for forbidden in ("import time", "from time", "datetime", "sleep(", "while ", "import requests", "urllib",
                              "GITHUB_TOKEN", "GH_TOKEN"):
                self.assertNotIn(forbidden, text, (relative, forbidden))


if __name__ == "__main__":
    unittest.main()
