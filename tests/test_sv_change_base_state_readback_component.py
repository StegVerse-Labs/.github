"""RTC-SV-CHANGE-BASE-STATE-READBACK-014 against temporary git repositories.

The fixture ledger is written by the real writer (intr_destination_ingress.self_close) into a temporary
bare repository, as in RTC-REPOSITORY-LEDGER-GENESIS-READBACK-013's tests, and a main commit carrying a
fixture data/canonical-task-registry.json is added to the same repository. Exercise evidence on temporary
repositories only; no network; the real registry is never read or written.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = "refs/stegverse/organization-ledger"
NAMESPACE = "repository-ledger/StegVerse-Labs/.github"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint", "owning_existing_goal", "next_attempt")


def _module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


component = _module("rtc014_component_under_test", "resident-runtime/sv_change_base_state_readback.py")
ingress = _module("rtc014_fixture_ingress", "resident-runtime/intr_destination_ingress.py")
REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))
CONTRACT = ROOT / "data/reusable-evidence-validation-component-contract.json"
MODEL = ROOT / "data/reusable-task-component-model.json"


def _git(repo, *args, input_bytes=None, index=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_AUTHOR_NAME": "rtc014-fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                "GIT_COMMITTER_NAME": "rtc014-fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"})
    if index is not None:
        env["GIT_INDEX_FILE"] = str(index)
    return subprocess.run(["git", "--git-dir", str(repo), *args], input=input_bytes, capture_output=True,
                          env=env, check=True).stdout.decode().strip()


def _commit(bare, work, files, parent=None, message="fixture"):
    index = work / ("i" + str(len(list(work.iterdir()))))
    _git(bare, "read-tree", "--empty", index=index)
    for path, data in files.items():
        blob = _git(bare, "hash-object", "-w", "--stdin", input_bytes=data)
        _git(bare, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", index=index)
    tree = _git(bare, "write-tree", index=index)
    return _git(bare, "commit-tree", tree, "-m", message, *(["-p", parent] if parent else []))


LABS, ORG = "StegVerse-Labs/.github", "StegVerse-org/.github"
ORG_REGISTRY = "orchestration/task-registry.json"


def ev(*args, **kw):
    kw.setdefault("repository_name", LABS)
    return component.evaluate(*args, **kw)


def org_registry_bytes(**extra):
    """The StegVerse-org/.github shape (orchestration/task-registry.json @40a5d235): no generation field."""
    return (json.dumps({"$schema": "https://stegverse-labs.github.io/repo-standards/schemas/task-registry.schema.json",
                        "org": "StegVerse-org", "repo": ".github", "registry_type": "orchestration_task_registry",
                        "active_goal": "SVORG-STEGOS-PORTABILITY-001", "archive_status": "ACTIVE", "tasks": [], **extra}, indent=2) + "\n").encode()


def registry_bytes(generation):
    return (json.dumps({"schema": "fixture-registry", "generation": generation, "tasks": []}, indent=2) + "\n").encode()


def build(work: Path):
    bare = work / "repo.git"
    subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
    seed = _commit(bare, work, {"MARKER": b"prior-history\n"}, message="prior history")
    _git(bare, "update-ref", REF, seed)
    contract = ingress.organization_ledger.C
    previous = contract.get("organization_ledger")
    contract["organization_ledger"] = {"store": "git", "ref": REF, "custody": "PRIVATE", "propagate_target": None}
    names = ("STEGVERSE_ORG_LEDGER_GIT_DIR", "STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_STORE", "STEGVERSE_ORG_LEDGER_GIT_REF",
             "STEGVERSE_ORG_LEDGER_GIT_REMOTE", "STEGVERSE_ORG_LEDGER_GIT_CUSTODY", "STEGVERSE_ORG_LEDGER_ROOT")
    saved = {n: os.environ.get(n) for n in names}
    for n in names:
        os.environ.pop(n, None)
    os.environ["STEGVERSE_ORG_LEDGER_GIT_DIR"] = str(bare)
    os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = f"git+{bare}#{REF}:{NAMESPACE}"
    try:
        result = ingress.self_close(ingress.diagnostic_payload("rtc014-fixture"), registry=REGISTRY,
                                    packet_id="rtc014-fixture-packet", hb_epoch=44)
    finally:
        contract["organization_ledger"] = previous
        for n, v in saved.items():
            os.environ.pop(n, None) if v is None else os.environ.__setitem__(n, v)
    assert result["disposition"] == "ALLOW", result
    first = _commit(bare, work, {"data/canonical-task-registry.json": registry_bytes(318)})
    second = _commit(bare, work, {"data/canonical-task-registry.json": registry_bytes(319)}, parent=first)
    broken = _commit(bare, work, {"data/canonical-task-registry.json": b"{not json"}, parent=second)
    no_gen = _commit(bare, work, {"data/canonical-task-registry.json": b'{"generation": "319"}'}, parent=broken)
    absent = _commit(bare, work, {"README.md": b"x\n"}, parent=no_gen)
    org_shape = _commit(bare, work, {ORG_REGISTRY: org_registry_bytes()}, parent=absent)
    org_gen = _commit(bare, work, {ORG_REGISTRY: org_registry_bytes(generation=7)}, parent=org_shape)
    _git(bare, "update-ref", "refs/heads/main", org_gen)
    side = _commit(bare, work, {"data/canonical-task-registry.json": registry_bytes(400)})
    _git(bare, "update-ref", "refs/heads/side", side)
    return bare, {"first": first, "second": second, "broken": broken, "no_gen": no_gen, "absent": absent, "side": side,
                  "org_shape": org_shape, "org_gen": org_gen}


class BaseStateReadbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._work = tempfile.TemporaryDirectory()
        cls.work = Path(cls._work.name)
        cls.bare, cls.c = build(cls.work)
        cls.ledger_head = _git(cls.bare, "rev-parse", REF)
        cls.refs_before = _git(cls.bare, "for-each-ref")

    @classmethod
    def tearDownClass(cls):
        cls._work.cleanup()

    def tearDown(self):
        self.assertEqual(_git(self.bare, "for-each-ref"), self.refs_before, "the readback wrote nothing")

    def assert_six(self, r, code):
        self.assertEqual(r["disposition"], "FAIL_CLOSED")
        self.assertEqual(r["failure_code"], code)
        for f in SIX:
            self.assertTrue(isinstance(r[f], str) and r[f].strip(), f)
        self.assertEqual(r["owning_existing_goal"], "StegVerse-org/.github#164")
        self.assertTrue(component.seal_verifies(r))

    def test_allow_receipt_shape_and_seal(self):
        r = ev(self.bare, self.c["second"], hb_epoch="1024")
        self.assertEqual(r["disposition"], "ALLOW", r)
        self.assertEqual(r["schema"], "stegverse.sv-change-base-state-readback/v1")
        self.assertEqual(r["base_ref"], {"registry_generation": 319, "ledger_head": self.ledger_head})
        self.assertEqual(r["bound_main_commit"], self.c["second"])
        self.assertEqual(r["hb_epoch"], "1024")
        self.assertNotIn("open_questions", r)
        reg_blob = _git(self.bare, "rev-parse", self.c["second"] + ":data/canonical-task-registry.json")
        head_blob = _git(self.bare, "rev-parse", self.ledger_head + ":HEAD.json")
        self.assertEqual(r["sources"], [{"file": "data/canonical-task-registry.json", "blob_sha": reg_blob},
                                        {"file": REF + ":HEAD.json", "blob_sha": head_blob}])
        self.assertTrue(r["ledger_chain_verifies"])
        self.assertEqual(r["authority_effect"], "NONE_READBACK_ONLY")
        self.assertTrue(component.seal_verifies(r))
        for k in ("schema", "base_ref", "bound_main_commit", "sources", "disposition", "result_sha256", "hb_epoch"):
            self.assertIn(k, r)
        tampered = copy.deepcopy(r); tampered["base_ref"]["registry_generation"] = 320
        self.assertFalse(component.seal_verifies(tampered))

    def test_generation_is_read_at_the_bound_commit_exactly(self):
        self.assertEqual(ev(self.bare, self.c["first"], hb_epoch="1024")["base_ref"]["registry_generation"], 318)
        self.assertEqual(ev(self.bare, self.c["second"], hb_epoch="1024")["base_ref"]["registry_generation"], 319)

    def test_hb_epoch_slot_open_when_not_supplied(self):
        r = ev(self.bare, self.c["second"])
        self.assertEqual((r["disposition"], r["hb_epoch"]), ("ALLOW", None))
        self.assertEqual([q["id"] for q in r["open_questions"]], ["JD-P4-3"])
        for bad in ("31", "abc", "", True, 12.5):
            with self.subTest(bad=bad):
                self.assert_six(ev(self.bare, self.c["second"], hb_epoch=bad), "BASE_STATE_NOT_OBSERVED")

    def test_registry_generation_unreadable(self):
        for key in ("broken", "no_gen", "absent"):
            with self.subTest(key):
                r = ev(self.bare, self.c[key], hb_epoch="1024")
                self.assert_six(r, "REGISTRY_GENERATION_UNREADABLE")
                self.assertIsNone(r["base_ref"]["registry_generation"])

    def test_registry_path_is_the_repositorys_own(self):
        self.assertEqual(component.REGISTRY_PATHS, {LABS: "data/canonical-task-registry.json", ORG: ORG_REGISTRY})
        # org shape: its own registry declares no generation -> REGISTRY_GENERATION_NOT_DECLARED (Q-ORG-REGISTRY-GENERATION)
        r = ev(self.bare, self.c["org_shape"], repository_name=ORG, hb_epoch="1024")
        self.assert_six(r, "REGISTRY_GENERATION_NOT_DECLARED")
        self.assertEqual(r["failed_predicate"], "REGISTRY_DECLARES_GENERATION")
        self.assertIn("Q-ORG-REGISTRY-GENERATION", r["next_attempt"])
        self.assertEqual((r["joint_item"], r["repository"]), ("Q-ORG-REGISTRY-GENERATION", ORG))
        self.assertEqual(r["sources"], [{"file": ORG_REGISTRY, "blob_sha": _git(self.bare, "rev-parse", self.c["org_shape"] + ":" + ORG_REGISTRY)}])
        self.assertIsNone(r["base_ref"]["registry_generation"])
        # the same commit read as Labs uses Labs' path, which is not readable there
        self.assert_six(ev(self.bare, self.c["absent"], repository_name=LABS, hb_epoch="1024"), "REGISTRY_GENERATION_UNREADABLE")
        # an org-shaped registry that did declare a generation would be read from the org path
        r = ev(self.bare, self.c["org_gen"], repository_name=ORG, hb_epoch="1024")
        self.assertEqual((r["disposition"], r["base_ref"]["registry_generation"]), ("ALLOW", 7), r)
        self.assertEqual(r["sources"][0]["file"], ORG_REGISTRY)
        # Labs' registry is still read at Labs' path
        self.assertEqual(ev(self.bare, self.c["second"], repository_name=LABS, hb_epoch="1024")["base_ref"]["registry_generation"], 319)

    def test_unmapped_repository_has_no_default_path(self):
        for name in (None, "StegVerse-Labs/TVC", "", 3):
            with self.subTest(name=name):
                r = ev(self.bare, self.c["second"], repository_name=name, hb_epoch="1024")
                self.assert_six(r, "REGISTRY_PATH_NOT_DECLARED")
                self.assertEqual(r["failed_predicate"], "REGISTRY_PATH_DECLARED_FOR_REPOSITORY")

    def test_bound_commit_must_be_present_well_formed_and_on_main(self):
        for label, commit, predicate in (("malformed", "abc", "BOUND_MAIN_COMMIT_WELL_FORMED"),
                                         ("absent", "1" * 40, "BOUND_MAIN_COMMIT_PRESENT"),
                                         ("off-main", self.c["side"], "BOUND_COMMIT_IS_ON_MAIN")):
            with self.subTest(label):
                r = ev(self.bare, commit, hb_epoch="1024")
                self.assert_six(r, "BASE_STATE_NOT_OBSERVED")
                self.assertEqual(r["failed_predicate"], predicate)
                self.assertIsNone(r["base_ref"]["ledger_head"])
        self.assert_six(ev(self.work / "nope", self.c["second"]), "BASE_STATE_NOT_OBSERVED")

    def test_ledger_ref_absent_or_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            bare = Path(tmp) / "r.git"
            subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
            main = _commit(bare, Path(tmp), {"data/canonical-task-registry.json": registry_bytes(319)})
            _git(bare, "update-ref", "refs/heads/main", main)
            r = ev(bare, main, hb_epoch="1024")
            self.assert_six(r, "BASE_STATE_NOT_OBSERVED")
            self.assertEqual(r["failed_predicate"], "ORGANIZATION_LEDGER_REF_PRESENT")
            self.assertEqual(r["base_ref"], {"registry_generation": 319, "ledger_head": None})
            seed = _commit(bare, Path(tmp), {"MARKER": b"x\n"})  # a ref with no HEAD: the existing readback refuses
            _git(bare, "update-ref", REF, seed)
            r = ev(bare, main, hb_epoch="1024")
            self.assert_six(r, "BASE_STATE_NOT_OBSERVED")
            self.assertEqual(r["failed_predicate"], "ORGANIZATION_LEDGER_HEAD_PRESENT")

    def test_reuses_existing_readback_and_is_read_only(self):
        src = (ROOT / "resident-runtime/sv_change_base_state_readback.py").read_text(encoding="utf-8")
        self.assertIn("organization_ledger_readback.py", src)
        self.assertIn("readback.readback(", src)
        self.assertIsNone(re.search(r"^\s*(import|from)\s+(time|datetime|urllib|http|socket|requests|random)\b", src, re.M))
        verbs = set(re.findall(r'_git\(repo, "([a-z-]+)"', src))
        self.assertEqual(verbs, {"rev-parse", "cat-file", "merge-base"})  # read-only git only; no fetch, push or ref write
        code = src.split('"""', 2)[2]
        for call in ("write_text", "open(", "urlopen", "time.time"):
            self.assertNotIn(call, code)

    def test_contract_entry(self):
        model = json.loads(MODEL.read_text(encoding="utf-8"))
        entries = [c for c in json.loads(CONTRACT.read_text(encoding="utf-8"))["components"] if c["component_id"] == component.COMPONENT_ID]
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        for field in model["component_interface_minimum"]:
            self.assertIn(field, entry)
        self.assertEqual(entry["authority_effect"], "NONE_READBACK_ONLY")
        self.assertIn("BASE_STATE_NOT_OBSERVED", entry["failure_classes"])
        self.assertIn("REGISTRY_GENERATION_UNREADABLE", entry["failure_classes"])
        self.assertIn("REGISTRY_GENERATION_NOT_DECLARED", entry["failure_classes"])
        self.assertIn("REGISTRY_PATH_NOT_DECLARED", entry["failure_classes"])
        self.assertIn(component.RESULT_SCHEMA, entry["version_or_schema_binding"])
        self.assertEqual(entry["implementation"]["reuses"], ["resident-runtime/organization_ledger_readback.py::readback"])
        self.assertFalse(any(entry["invariants"][k] for k in ("writes_ledger_or_ref", "writes_registry", "bumps_registry_generation",
                                                               "reads_clock", "uses_network", "uses_credential", "derives_hb_epoch")))


if __name__ == "__main__":
    unittest.main()
