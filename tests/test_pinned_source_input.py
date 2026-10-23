"""A pinned source tree as a declared verification input (StegVerse-org/.github#163, P1).

Offline: the source repository is a local git repository built here, so nothing is fetched from the network. Each
refusal is FAIL_CLOSED with the six fields; nothing is skipped.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pinned_source_input as psi  # noqa: E402
import test_set_selection as sel  # noqa: E402
import test_suite_baseline_drift as drift  # noqa: E402

SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t.invalid", *args], cwd=cwd,
                          check=True, capture_output=True, text=True).stdout.strip()


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pinned-input-"))
        self.src = self.tmp / "src"
        (self.src / "fakesdk").mkdir(parents=True)
        (self.src / "fakesdk/__init__.py").write_text("VALUE = 'pinned'\n")
        (self.src / "fakesdk/sub.py").write_text("X = 1\n")
        (self.src / "unrelated").mkdir()
        (self.src / "unrelated/secret.txt").write_text("not declared\n")
        git(self.src, "init", "-q")
        git(self.src, "add", "-A")
        git(self.src, "commit", "-q", "-m", "one")
        self.commit = git(self.src, "rev-parse", "HEAD")
        self.manifest = self.tmp / "manifest.json"
        self.manifest.write_text(json.dumps({"schema": psi.SCHEMA, "input": "fakesdk", "repository": str(self.src),
                                             "exports": {"PYTHONPATH": "{root}", "FAKESDK_REQUIRED": "1"}}))
        text = json.dumps(psi.author_pin(self.manifest, "p1", self.src, self.commit, ["fakesdk"],
                                         json.loads(self.manifest.read_text())), indent=1, sort_keys=True)
        self.manifest.write_text(text)

    def tearDown(self) -> None:
        subprocess.run(["rm", "-rf", str(self.tmp)], check=False)

    def materialize(self) -> Path:
        dest = self.tmp / "in"
        psi.materialize(self.manifest, "p1", dest, str(self.src))
        return dest / "tree"

    def refused(self, fn, code: str) -> dict:
        with self.assertRaises(psi.PinRefused) as ctx:
            fn()
        record = ctx.exception.record
        self.assertEqual(code, record["failure_code"])
        self.assertEqual("FAIL_CLOSED", record["disposition"])
        for k in SIX:
            self.assertTrue(record[k], k)
        self.assertIn("#163", record["owning_existing_goal"])
        return record


class MaterializeTests(Fixture):
    def test_only_the_declared_modules_are_extracted_and_every_file_matches(self) -> None:
        tree = self.materialize()
        self.assertTrue((tree / "fakesdk/__init__.py").is_file())
        self.assertFalse((tree / "unrelated").exists())
        receipt = json.loads((tree.parent / "receipt.json").read_text())
        self.assertEqual(("ALLOW", self.commit, 2), (receipt["disposition"], receipt["commit"],
                                                      receipt["files_verified"]))
        self.assertEqual("E0", receipt["lowest_supported_mode"])

    def test_a_file_that_differs_is_refused(self) -> None:
        tree = self.materialize()
        (tree / "fakesdk/sub.py").write_text("X = 2\n")
        record = self.refused(lambda: psi.verify(self.manifest, "p1", tree), "PINNED_INPUT_SHA256_MISMATCH")
        self.assertEqual(["fakesdk/sub.py"], record["differ"])

    def test_an_undeclared_or_absent_file_is_refused(self) -> None:
        tree = self.materialize()
        (tree / "fakesdk/extra.py").write_text("")
        self.refused(lambda: psi.verify(self.manifest, "p1", tree), "PINNED_INPUT_UNDECLARED_FILE")
        (tree / "fakesdk/extra.py").unlink()
        (tree / "fakesdk/sub.py").unlink()
        self.refused(lambda: psi.verify(self.manifest, "p1", tree), "PINNED_INPUT_DECLARED_FILE_ABSENT")

    def test_a_hand_edited_manifest_is_refused(self) -> None:
        m = json.loads(self.manifest.read_text())
        m["pins"]["p1"]["modules"]["fakesdk"]["file_sha256"]["fakesdk/sub.py"] = "0" * 64
        self.manifest.write_text(json.dumps(m))
        self.refused(self.materialize, "PINNED_INPUT_MANIFEST_SEAL_MISMATCH")

    def test_an_undeclared_pin_is_refused(self) -> None:
        self.refused(lambda: psi.materialize(self.manifest, "nope", self.tmp / "x", str(self.src)),
                     "PINNED_INPUT_PIN_UNDECLARED")

    def test_a_commit_the_source_cannot_serve_is_refused(self) -> None:
        m = json.loads(self.manifest.read_text())
        m["pins"]["p1"]["commit"] = "1" * 40
        self.manifest.write_text(json.dumps(psi.sealed(m)))
        self.refused(self.materialize, "PINNED_INPUT_FETCH_FAILED")

    def test_a_moved_tree_is_refused(self) -> None:
        m = json.loads(self.manifest.read_text())
        m["pins"]["p1"]["tree"] = "2" * 40
        self.manifest.write_text(json.dumps(psi.sealed(m)))
        self.refused(self.materialize, "PINNED_INPUT_TREE_MISMATCH")


class SelectorInputTests(Fixture):
    def check(self, **extra) -> dict:
        return {"kind": "pinned_source", "manifest": str(self.manifest), "pin": "p1", "env": "FAKESDK_PIN",
                "module": "fakesdk", **extra}

    def test_available_only_when_verified_and_imported_from_the_pinned_root(self) -> None:
        tree = self.materialize()
        ok, detail = sel.input_available(self.tmp, {"check": self.check()}, sys.executable, {"FAKESDK_PIN": str(tree)})
        self.assertTrue(ok, detail)
        ok, detail = sel.input_available(self.tmp, {"check": self.check()}, sys.executable, {})
        self.assertFalse(ok)
        self.assertIn("FAKESDK_PIN unset", detail)
        (tree / "fakesdk/sub.py").write_text("X = 3\n")
        ok, detail = sel.input_available(self.tmp, {"check": self.check()}, sys.executable, {"FAKESDK_PIN": str(tree)})
        self.assertFalse(ok)
        self.assertIn("FAIL_CLOSED PINNED_INPUT_SHA256_MISMATCH", detail)

    def test_a_runtime_module_the_pin_declares_must_already_be_importable(self) -> None:
        base = json.loads(self.manifest.read_text())
        self.manifest.write_text(json.dumps(psi.author_pin(self.manifest, "p1", self.src, self.commit, ["fakesdk"],
                                                           base, ["no_such_module_p1_163"])))
        tree = self.materialize()
        ok, detail = sel.input_available(self.tmp, {"check": self.check()}, sys.executable, {"FAKESDK_PIN": str(tree)})
        self.assertFalse(ok)
        self.assertIn("PINNED_INPUT_RUNTIME_MODULE_UNAVAILABLE", detail)
        self.assertIn("installs nothing", detail)


class RunGroupTests(unittest.TestCase):
    def test_each_group_runs_in_its_own_process_with_only_its_exports(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "tests").mkdir()
            (root / "tests/__init__.py").write_text("")
            (root / "tests/test_g.py").write_text(
                "import os, unittest\n"
                "class A(unittest.TestCase):\n"
                "    def test_unpinned(self):\n"
                "        self.assertNotIn('P1_PIN', os.environ)\n"
                "class B(unittest.TestCase):\n"
                "    def test_pinned(self):\n"
                "        self.assertEqual('x', os.environ['P1_PIN'])\n")
            selection = {"runner": "unittest", "run": {"tests": [], "deselect": []}, "run_groups": [
                {"id": "no-pinned-input", "inputs": [], "env": {}, "tests": ["tests.test_g.A"], "deselect": []},
                {"id": "sdk", "inputs": ["sdk"], "env": {"P1_PIN": "x"}, "tests": ["tests.test_g.B"],
                 "deselect": []}]}
            out = root / "out.txt"
            cwd = os.getcwd()
            os.chdir(root)
            try:
                status = sel.run_groups(selection, out, None)
            finally:
                os.chdir(cwd)
            text = out.read_text()
            self.assertEqual(0, status, text)
            self.assertEqual(2, text.count(sel.GROUP_MARKER))
            results, counts, ran = drift.unittest_results(text)
            self.assertEqual(2, ran)            # Ran is added up over the groups, not the last one only
            self.assertEqual({"ok"}, set(results.values()))

    def test_pytest_counts_are_added_up_per_group(self) -> None:
        text = (f"{drift.GROUP_MARKER}a inputs=- tests=1\n1 passed, 1 skipped in 0.1s\n"
                f"{drift.GROUP_MARKER}b inputs=sdk tests=1\n2 passed in 0.1s\n")
        _rows, counts, _nodes = drift.pytest_verification(ROOT, text, None, "r", "g")
        self.assertEqual({"passed": 3, "skipped": 1}, counts)

    def test_a_test_is_judged_in_the_group_that_ran_it_pinned_first(self) -> None:
        drift.RUN_GROUPS[:] = [
            {"id": "no-pinned-input", "inputs": [], "env": {}, "tests": ["tests/test_x.py"]},
            {"id": "sdk", "inputs": ["sdk"], "env": {"PYTHONPATH": "/pinned"}, "tests": ["tests/test_x.py::Real"]}]
        try:
            self.assertEqual("sdk", drift.group_of("tests/test_x.py::Real::test_a")["id"])
            self.assertEqual("no-pinned-input", drift.group_of("tests/test_x.py::Other::test_b")["id"])
            self.assertEqual("/pinned", drift.group_env("tests/test_x.py::Real::test_a")["PYTHONPATH"])
        finally:
            drift.RUN_GROUPS[:] = []


class ThisRepositoryTests(unittest.TestCase):
    def test_every_sdk_input_of_the_spec_is_a_pinned_source_of_the_committed_manifest(self) -> None:
        spec = json.loads((ROOT / ".stegverse/test-set-spec.json").read_text())
        pins = [d["check"] for n, d in spec["inputs"].items() if n.startswith("stegverse-sdk")]
        self.assertTrue(pins)
        for check in pins:
            self.assertEqual("pinned_source", check["kind"])
            manifest, pin = psi.load_manifest(ROOT / check["manifest"], check["pin"], "test")
            self.assertEqual("https://github.com/StegVerse-org/StegVerse-SDK", manifest["repository"])
            self.assertEqual(40, len(pin["commit"]))
            self.assertTrue(pin["commit"].startswith(check["pin"]))
            for mod in pin["modules"].values():
                self.assertEqual(psi.module_digest(mod["file_sha256"]), mod["sha256"])


if __name__ == "__main__":
    unittest.main()
