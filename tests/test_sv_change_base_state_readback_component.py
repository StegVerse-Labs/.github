"""RTC-SV-CHANGE-BASE-STATE-READBACK-014 against temporary git repositories.

The fixture ledger is written by the real writer (intr_destination_ingress.self_close) into a temporary
bare repository, as in RTC-REPOSITORY-LEDGER-GENESIS-READBACK-013's tests, and a main commit carrying a
fixture data/canonical-task-registry.json is added to the same repository. Exercise evidence on temporary
repositories only; no network; the real registry is never read or written.
"""
from __future__ import annotations

import copy
import hashlib
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

    def assert_six(self, r, code, disposition="FAIL_CLOSED"):
        self.assertEqual(r["disposition"], disposition)
        self.assertEqual(r["failure_code"], code)
        for f in SIX:
            self.assertTrue(isinstance(r[f], str) and r[f].strip(), f)
        self.assertEqual(r["owning_existing_goal"], "StegVerse-org/.github#164")
        self.assertTrue(component.seal_verifies(r))

    def test_allow_receipt_shape_and_seal(self):
        r = ev(self.bare, self.c["second"], hb_epoch="44")
        self.assertEqual(r["disposition"], "ALLOW", r)
        self.assertEqual(r["schema"], "stegverse.sv-change-base-state-readback/v1")
        self.assertEqual(r["base_ref"], {"registry_generation": 319, "ledger_head": self.ledger_head})
        self.assertEqual(r["bound_main_commit"], self.c["second"])
        self.assertEqual(r["hb_epoch"], "44")  # observed on the head receipt the real writer appended (self_close hb_epoch=44)
        self.assertNotIn("open_questions", r)
        reg_blob = _git(self.bare, "rev-parse", self.c["second"] + ":data/canonical-task-registry.json")
        head_blob = _git(self.bare, "rev-parse", self.ledger_head + ":HEAD.json")
        key = "receipts/" + r["ledger_head_receipt_sha256"].split(":", 1)[1] + ".json"
        rec_blob = _git(self.bare, "rev-parse", self.ledger_head + ":" + key)
        self.assertEqual(r["sources"], [{"file": "data/canonical-task-registry.json", "blob_sha": reg_blob},
                                        {"file": REF + ":HEAD.json", "blob_sha": head_blob},
                                        {"file": REF + ":" + key, "blob_sha": rec_blob}])
        # exact names (Lane B #46 consumes them): {ledger_head, receipt, field}
        self.assertEqual(r["hb_epoch_source"], {"ledger_head": self.ledger_head, "receipt": key, "field": "$.hb_reference.epoch"})
        self.assertTrue(r["ledger_chain_verifies"])
        self.assertEqual(r["authority_effect"], "NONE_READBACK_ONLY")
        self.assertTrue(component.seal_verifies(r))
        for k in ("schema", "base_ref", "bound_main_commit", "sources", "disposition", "result_sha256", "hb_epoch"):
            self.assertIn(k, r)
        tampered = copy.deepcopy(r); tampered["base_ref"]["registry_generation"] = 320
        self.assertFalse(component.seal_verifies(tampered))

    def test_generation_is_read_at_the_bound_commit_exactly(self):
        self.assertEqual(ev(self.bare, self.c["first"], hb_epoch="44")["base_ref"]["registry_generation"], 318)
        self.assertEqual(ev(self.bare, self.c["second"], hb_epoch="44")["base_ref"]["registry_generation"], 319)

    def test_hb_epoch_is_observed_on_the_head_receipt(self):
        """ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH: no caller epoch is needed; a differing expectation fails closed."""
        r = ev(self.bare, self.c["second"])
        self.assertEqual((r["disposition"], r["hb_epoch"]), ("ALLOW", "44"))
        self.assertNotIn("open_questions", r)
        r = ev(self.bare, self.c["second"], hb_epoch="1024")
        self.assert_six(r, "HB_EPOCH_MISMATCH", "DENY")  # observed contradiction: DENY; P4's name traces in the detail
        self.assertEqual((r["failed_predicate"], r["hb_epoch"], r["expected_hb_epoch"], r["flag_failure_code"]),
                         ("ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH", "44", "1024", "HB_EPOCH_FLAG_MISMATCH"))
        self.assertEqual(r["hb_epoch_source"]["ledger_head"], self.ledger_head)  # DENY: the epoch was observed, so its source is sealed
        self.assertEqual(ev(self.bare, self.c["second"], hb_epoch="44")["disposition"], "ALLOW")
        for bad in ("31", "abc", "", True, 12.5):
            with self.subTest(bad=bad):
                self.assert_six(ev(self.bare, self.c["second"], hb_epoch=bad), "BASE_STATE_NOT_OBSERVED")

    def test_head_receipt_without_valid_epoch_is_unobserved(self):
        head = self.ledger_head
        rec_digest = json.loads(_git(self.bare, "show", head + ":HEAD.json"))["receipt_sha256"]
        good = json.loads(_git(self.bare, "show", head + ":receipts/" + rec_digest.split(":", 1)[1] + ".json"))
        self.assertEqual(component.ledger_head_epoch(self.bare, head)[0], "44")

        def reseal(doc):
            body = {k: v for k, v in doc.items() if k != "receipt_sha256"}
            return {**body, "receipt_sha256": "sha256:" + hashlib.sha256(component.canon(body)).hexdigest()}
        ref = dict(good["hb_reference"])
        cases = {"clock": reseal(dict(good, hb_reference=dict(ref, derived_from_clock=True))),
                 "below-32": reseal(dict(good, hb_reference=dict(ref, epoch=31))),
                 "string": reseal(dict(good, hb_reference=dict(ref, epoch="44"))),
                 "bool": reseal(dict(good, hb_reference=dict(ref, epoch=True))),
                 "no-clock-flag": reseal(dict(good, hb_reference={k: v for k, v in ref.items() if k != "derived_from_clock"})),
                 "no-reference": reseal({k: v for k, v in good.items() if k != "hb_reference"}),
                 "schema": reseal(dict(good, schema="stegverse.repo-transition-receipt/v1")),
                 "broken-seal": dict(good, hb_reference=dict(ref, epoch=45))}
        for label, doc in cases.items():
            with self.subTest(label):
                digest = doc["receipt_sha256"]
                files = {"HEAD.json": json.dumps({"receipt_sha256": digest}).encode(),
                         "receipts/" + digest.split(":", 1)[1] + ".json": json.dumps(doc).encode()}
                commit = _commit(self.bare, self.work, files)
                epoch, why, sources = component.ledger_head_epoch(self.bare, commit)
                self.assertIsNone(epoch, label)
                self.assertTrue(why)
        empty = _commit(self.bare, self.work, {"HEAD.json": b"{}"})
        self.assertIsNone(component.ledger_head_epoch(self.bare, empty)[0])

    def test_epoch_rule_source_is_kernel_hb_reference(self):
        self.assertEqual(component.EPOCH_RULE_SOURCE["lines"], "68-74")
        kernel = (ROOT / "org-kernel" / "kernel.py").read_bytes()
        blob = hashlib.sha1(b"blob %d\0" % len(kernel) + kernel).hexdigest()
        self.assertEqual(blob, component.EPOCH_RULE_SOURCE["git_blob_sha"])
        # P1's citation: sha256 of the source segment of kernel.py::supplied_epoch_failure (lines 236-269).
        import ast
        src = kernel.decode("utf-8")
        fn = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == component.EPOCH_RULE_FUNCTION["function"]][0]
        self.assertEqual(f"{fn.lineno}-{fn.end_lineno}", component.EPOCH_RULE_FUNCTION["lines"])
        self.assertEqual(hashlib.sha256(ast.get_source_segment(src, fn).encode("utf-8")).hexdigest(),
                         component.EPOCH_RULE_FUNCTION["source_segment_sha256"])

    def test_fail_closed_seals_null_epoch_and_null_source(self):
        """Every FAIL_CLOSED seals hb_epoch null and hb_epoch_source present and null (never omitted)."""
        cases = [ev(self.bare, self.c["second"], hb_epoch="31"), ev(self.bare, "0" * 40, hb_epoch="44"),
                 ev(self.bare, self.c["second"], repository_name="Nope/nope")]
        for r in cases:
            self.assertEqual(r["disposition"], "FAIL_CLOSED", r)
            self.assertIn("hb_epoch_source", r)
            self.assertIsNone(r["hb_epoch_source"])
            self.assertIsNone(r["hb_epoch"])
            self.assertTrue(component.seal_verifies(r))

    def test_known_answer_live_labs_head(self):
        """KAT: the real Labs ledger head a5bb54d8 (receipt 35810b65) reads "469411750", when a clone holding it is supplied."""
        repo = os.environ.get("RTC014_LIVE_LABS_REPO")
        if not repo:
            self.skipTest("set RTC014_LIVE_LABS_REPO to a clone holding refs/stegverse/organization-ledger a5bb54d8")
        epoch, why, sources = component.ledger_head_epoch(Path(repo), "a5bb54d81893b392a3ce28182986fc39857807e1")
        self.assertEqual(epoch, "469411750", why)
        self.assertIn("35810b6598e99cef32d9a0f1f97d07394d9f21c540ed7d3a395d9d78b753db3d", sources[1]["file"])
        kat_source = {"ledger_head": "a5bb54d81893b392a3ce28182986fc39857807e1",
                      "receipt": "receipts/35810b6598e99cef32d9a0f1f97d07394d9f21c540ed7d3a395d9d78b753db3d.json",
                      "field": "$.hb_reference.epoch"}
        self.assertEqual(sources[1]["file"].split(":", 1)[1], kat_source["receipt"])
        def rev(ref):
            return subprocess.run(["git", "-C", repo, "rev-parse", "--verify", "--quiet", ref], capture_output=True, text=True).stdout.strip()
        main_ref = "refs/remotes/origin/main" if rev("refs/remotes/origin/main") else "refs/heads/main"
        if rev(REF) == kat_source["ledger_head"]:
            r = ev(Path(repo), rev(main_ref), repository_name=LABS, main_ref=main_ref)
            self.assertEqual((r["disposition"], r["hb_epoch"], r["hb_epoch_source"]), ("ALLOW", "469411750", kat_source), r)

    def test_registry_generation_unreadable(self):
        for key in ("broken", "no_gen", "absent"):
            with self.subTest(key):
                r = ev(self.bare, self.c[key], hb_epoch="44")
                self.assert_six(r, "REGISTRY_GENERATION_UNREADABLE")
                self.assertIsNone(r["base_ref"]["registry_generation"])

    def test_registry_path_is_the_repositorys_own(self):
        self.assertEqual(component.REGISTRY_PATHS, {LABS: "data/canonical-task-registry.json", ORG: ORG_REGISTRY})
        # org shape: its own registry declares no generation -> REGISTRY_GENERATION_NOT_DECLARED (Q-ORG-REGISTRY-GENERATION)
        r = ev(self.bare, self.c["org_shape"], repository_name=ORG, hb_epoch="44")
        self.assert_six(r, "REGISTRY_GENERATION_NOT_DECLARED")
        self.assertEqual(r["failed_predicate"], "REGISTRY_DECLARES_GENERATION")
        self.assertIn("Q-ORG-REGISTRY-GENERATION", r["next_attempt"])
        self.assertEqual((r["joint_item"], r["repository"]), ("Q-ORG-REGISTRY-GENERATION", ORG))
        self.assertEqual(r["sources"], [{"file": ORG_REGISTRY, "blob_sha": _git(self.bare, "rev-parse", self.c["org_shape"] + ":" + ORG_REGISTRY)}])
        self.assertIsNone(r["base_ref"]["registry_generation"])
        # the same commit read as Labs uses Labs' path, which is not readable there
        self.assert_six(ev(self.bare, self.c["absent"], repository_name=LABS, hb_epoch="44"), "REGISTRY_GENERATION_UNREADABLE")
        # an org-shaped registry that did declare a generation would be read from the org path
        r = ev(self.bare, self.c["org_gen"], repository_name=ORG, hb_epoch="44")
        self.assertEqual((r["disposition"], r["base_ref"]["registry_generation"]), ("ALLOW", 7), r)
        self.assertEqual(r["sources"][0]["file"], ORG_REGISTRY)
        # Labs' registry is still read at Labs' path
        self.assertEqual(ev(self.bare, self.c["second"], repository_name=LABS, hb_epoch="44")["base_ref"]["registry_generation"], 319)

    def test_unmapped_repository_has_no_default_path(self):
        for name in (None, "StegVerse-Labs/TVC", "", 3):
            with self.subTest(name=name):
                r = ev(self.bare, self.c["second"], repository_name=name, hb_epoch="44")
                self.assert_six(r, "REGISTRY_PATH_NOT_DECLARED")
                self.assertEqual(r["failed_predicate"], "REGISTRY_PATH_DECLARED_FOR_REPOSITORY")

    def test_bound_commit_must_be_present_well_formed_and_on_main(self):
        for label, commit, predicate in (("malformed", "abc", "BOUND_MAIN_COMMIT_WELL_FORMED"),
                                         ("absent", "1" * 40, "BOUND_MAIN_COMMIT_PRESENT"),
                                         ("off-main", self.c["side"], "BOUND_COMMIT_IS_ON_MAIN")):
            with self.subTest(label):
                r = ev(self.bare, commit, hb_epoch="44")
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
            r = ev(bare, main, hb_epoch="44")
            self.assert_six(r, "BASE_STATE_NOT_OBSERVED")
            self.assertEqual(r["failed_predicate"], "ORGANIZATION_LEDGER_REF_PRESENT")
            self.assertEqual(r["base_ref"], {"registry_generation": 319, "ledger_head": None})
            seed = _commit(bare, Path(tmp), {"MARKER": b"x\n"})  # a ref with no HEAD: the existing readback refuses
            _git(bare, "update-ref", REF, seed)
            r = ev(bare, main, hb_epoch="44")
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
        self.assertEqual(entry["implementation"]["reuses"], ["resident-runtime/organization_ledger_readback.py::readback",
                                                             "resident-runtime/ledger_store.py::HEAD_KEY,receipt_key"])
        self.assertIn("HB_EPOCH_SOURCE_UNOBSERVED", entry["failure_classes"])
        self.assertFalse(any(entry["invariants"][k] for k in ("writes_ledger_or_ref", "writes_registry", "bumps_registry_generation",
                                                               "reads_clock", "uses_network", "uses_credential", "derives_hb_epoch")))


if __name__ == "__main__":
    unittest.main()
