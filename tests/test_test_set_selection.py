"""Callable test sets and the diff-driven selector (scripts/test_set_selection.py), with the adjudication of a
selected run (scripts/test_suite_baseline_drift.py pr --selection). StegVerse-org/.github#166."""
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
import test_set_selection as sel  # noqa: E402
import test_suite_baseline_drift as drift  # noqa: E402

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
PASSING = "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n"


class Toy:
    """tests/test_a.py verifies src/a.py; tests/test_b.py verifies src/b.py and needs an input; tests/test_core.py
    is the always-run core."""

    def __init__(self, base: Path):
        self.path = base / "repo"
        self.path.mkdir()
        self.git("init", "-q", "-b", "main")
        self.write("src/a.py", "A = 1\n")
        self.write("src/b.py", "B = 1\n")
        self.write("src/c.py", "C = 1\n")
        self.write("tests/__init__.py", "")
        self.write("tests/test_core.py", PASSING)
        self.write("tests/test_a.py", 'SOURCE = "src/a.py"\n' + PASSING)
        self.write("tests/test_b.py", 'SOURCE = "src/b.py"\n' + PASSING)
        self.write("tests/test_c.py", 'SOURCE = "src/c.py"\n' + PASSING)
        self.write("baseline.json", json.dumps({"known_failing": [], "excluded": []}))
        self.spec({})
        self.base = self.commit("base")

    def spec(self, inputs: dict, module_inputs: dict | None = None) -> None:
        self.write(".stegverse/test-set-spec.json", json.dumps({
            "schema": sel.SPEC_SCHEMA, "repository": "toy/repo", "runner": "unittest",
            "manifest": ".stegverse/test-sets.json", "test_globs": ["tests/**"], "import_roots": ["src"],
            "core": {"tests": ["tests/test_core.py"], "surfaces": [], "inputs": []},
            "selects_all": ["tests/*__init__.py"], "inputs": inputs, "module_inputs": module_inputs or {}}))
        self.generate()

    def generate(self) -> None:
        self.assertok(sel.main(["generate", "--root", str(self.path), "--spec", ".stegverse/test-set-spec.json",
                                "--out", ".stegverse/test-sets.json"]))

    @staticmethod
    def assertok(code: int) -> None:
        assert code == 0, code

    def git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.path, env=ENV, check=True, capture_output=True,
                              text=True).stdout.strip()

    def write(self, rel: str, text: str) -> None:
        p = self.path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")


class SelectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.toy = Toy(Path(self.tmp.name))

    def select(self, base: str | None = None, env: dict | None = None) -> tuple[int, dict]:
        out = Path(self.tmp.name) / "selection.json"
        argv = ["select", "--root", str(self.toy.path), "--manifest", ".stegverse/test-sets.json",
                "--spec", ".stegverse/test-set-spec.json", "--head", "HEAD", "--retry-entrypoint", "toy.yml",
                "--out", str(out), "--args-out", str(Path(self.tmp.name) / "args.txt")]
        if base:
            argv[argv.index("--head"):argv.index("--head")] = ["--base", base]
        old = dict(os.environ)
        os.environ.update(env or {})
        try:
            code = sel.main(argv)
        finally:
            os.environ.clear()
            os.environ.update(old)
        record = json.loads(out.read_text())
        self.assertTrue(sel.seal_verifies(record))
        return code, record

    def ids(self, record: dict) -> list[str]:
        return [x["id"] for x in record["selected"]]

    def test_a_diff_path_selects_the_set_that_declares_it_and_the_core_set_always_runs(self) -> None:
        self.toy.write("src/a.py", "A = 2\n")
        self.toy.commit("change a")
        code, record = self.select(self.toy.base)
        self.assertEqual((code, record["mode"], self.ids(record)), (0, "DIFF", ["core", "tests/test_a.py"]))
        self.assertEqual(record["selected"][0]["reasons"], [{"reason": "ALWAYS_RUN_CORE"}])
        self.assertEqual(record["selected"][1]["reasons"], [{"reason": "DIFF_PATH_MATCHES_SURFACE", "path": "src/a.py",
                                                             "surface": "src/a.py",
                                                             "declared_surface": "tests/test_a.py"}])
        self.assertEqual(record["run"]["tests"], ["tests.test_core", "tests.test_a"])

    def test_the_core_set_runs_on_a_change_that_reaches_no_other_set(self) -> None:
        self.toy.write("tests/test_core.py", PASSING + "# touched\n")
        self.toy.commit("touch core")
        _, record = self.select(self.toy.base)
        self.assertEqual((record["mode"], self.ids(record)), ("DIFF", ["core"]))

    def test_an_unmapped_path_selects_every_set(self) -> None:
        self.toy.write("docs/NOTES.md", "nothing declares this\n")
        self.toy.commit("unmapped")
        _, record = self.select(self.toy.base)
        self.assertEqual(record["mode"], "ALL")
        self.assertEqual(record["unmapped_paths"], ["docs/NOTES.md"])
        self.assertEqual(sorted(self.ids(record)), ["core", "tests/test_a.py", "tests/test_b.py", "tests/test_c.py"])
        self.assertEqual(record["not_selected_count"], 0)

    def test_an_unavailable_diff_selects_every_set(self) -> None:
        _, record = self.select(None)
        self.assertEqual((record["mode"], record["all_reasons"][0]["reason"]), ("ALL", "DIFF_UNAVAILABLE"))
        _, record = self.select("0" * 40)                     # a base this clone does not hold
        self.assertEqual((record["mode"], record["diff_available"]), ("ALL", False))

    def test_a_path_that_shapes_selection_and_a_stale_manifest_select_every_set(self) -> None:
        self.toy.write("tests/__init__.py", "# shared\n")
        self.toy.commit("shared fixture")
        _, record = self.select(self.toy.base)
        self.assertEqual((record["mode"], record["all_reasons"][0]["reason"]), ("ALL", "PATH_SHAPES_SELECTION"))
        base = self.toy.git("rev-parse", "HEAD")
        manifest = json.loads((self.toy.path / ".stegverse/test-sets.json").read_text())
        manifest["sets"][1]["surfaces"] = []                  # a hand-narrowed manifest
        self.toy.write(".stegverse/test-sets.json", json.dumps(manifest))
        self.toy.write("src/a.py", "A = 3\n")
        self.toy.commit("narrow")
        code, record = self.select(base)
        self.assertEqual((code, record["mode"], record["disposition"]), (1, "ALL", "FAIL_CLOSED"))
        self.assertEqual(record["failure_code"], "TEST_SET_MANIFEST_STALE")

    def test_an_unselected_set_is_absent_rather_than_reported_as_skipped(self) -> None:
        self.toy.write("src/a.py", "A = 2\n")
        self.toy.commit("change a")
        _, record = self.select(self.toy.base)
        text = json.dumps(record)
        self.assertNotIn("tests/test_b.py", text)
        self.assertNotIn("tests.test_b", text)
        self.assertNotIn("skipped", text.replace("not reported as skipped", ""))
        self.assertEqual(record["not_selected_count"], 2)

    def test_an_unavailable_input_is_routed_to_its_owner_and_blocks_only_changes_that_select_its_set(self) -> None:
        inputs = {"toy-sdk": {"check": {"kind": "env_path", "env": "TOY_SDK_ROOT"}, "owner": "P1 (toy#163)",
                              "finish_point": "TOY_SDK_ROOT is supplied and test_b passes", "repair": "supply it"}}
        self.toy.spec(inputs, {"tests/test_b.py": ["toy-sdk"]})
        base = self.toy.commit("declare the input")
        self.toy.write("src/a.py", "A = 2\n")
        self.toy.commit("change a")
        code, record = self.select(base)
        self.assertEqual((code, record["disposition"], record["input_unavailable"]), (0, "SELECTED", []))
        self.toy.write("src/b.py", "B = 2\n")
        self.toy.commit("change b")
        code, record = self.select(base)
        self.assertEqual((code, record["disposition"]), (1, "FAIL_CLOSED"))
        [item] = record["input_unavailable"]
        self.assertEqual((item["failure_code"], item["owning_existing_goal"], item["set"], item["input"]),
                         (sel.INPUT_UNAVAILABLE, "P1 (toy#163)", "tests/test_b.py", "toy-sdk"))
        self.assertTrue(all(item[k] for k in sel.SIX))
        self.assertNotIn("tests.test_b", record["run"]["tests"])          # an unavailable set is not run
        code, record = self.select(base, {"TOY_SDK_ROOT": str(self.toy.path)})
        self.assertEqual((code, record["disposition"]), (0, "SELECTED"))
        self.assertIn("tests.test_b", record["run"]["tests"])

    def test_importlib_by_path_loads_and_relative_imports_are_surfaces(self) -> None:
        # a by-path load next to the importing file and a relative import inside a package (TVC_SETS_SURFACE_UNDER_DECLARED)
        self.toy.write("src/pkg/__init__.py", "")
        self.toy.write("src/pkg/engine_v2.py", "V = 2\n")
        self.toy.write("src/pkg/engine_v3.py", "from .engine_v2 import V\n")
        self.toy.write("src/kernel/node_store.py", "S = 1\n")
        self.toy.write("src/kernel/kernel.py", "import importlib.util\nfrom pathlib import Path\n"
                       "_s = importlib.util.spec_from_file_location('ns', Path(__file__).resolve().parent / 'node_store.py')\n")
        self.toy.write("tests/test_d.py", "import importlib.util\nfrom pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n"
                       "K = ROOT / 'src' / 'kernel' / 'kernel.py'\nE = ROOT / 'src' / 'pkg' / 'engine_v3.py'\n" + PASSING)
        self.toy.generate()
        base = self.toy.commit("by-path loads")
        manifest = json.loads((self.toy.path / ".stegverse/test-sets.json").read_text())
        [d] = [s for s in manifest["sets"] if s["id"] == "tests/test_d.py"]
        reach = sel.closure(manifest["surface_graph"], d["surfaces"])
        for path in ("src/kernel/kernel.py", "src/kernel/node_store.py", "src/pkg/engine_v3.py", "src/pkg/engine_v2.py",
                     "src/pkg/__init__.py"):
            self.assertIn(path, reach)
        self.toy.write("src/kernel/node_store.py", "S = 2\n")
        self.toy.write("src/pkg/engine_v2.py", "V = 3\n")
        self.toy.commit("change what is loaded by path")
        code, record = self.select(base)
        self.assertEqual(record["mode"], "DIFF")
        self.assertEqual(self.ids(record), ["core", "tests/test_d.py"])

    def receipt_inputs(self, consumer_body: str | None) -> str:
        inputs = {"tvc": {"check": {"kind": sel.RECEIPT_KIND, "consumer": "scripts/consume.py",
                                    "argv": ["consume", "--head-root", "{root}"], "allow": "ALLOW",
                                    "consumer_source": "toy#3332, not merged"},
                          "owner": "Lane C (toy#164)", "finish_point": "the consumer returns ALLOW at this head",
                          "repair": "append a matching receipt"}}
        if consumer_body is not None:
            self.toy.write("scripts/consume.py", consumer_body)
        self.toy.spec(inputs, {"tests/test_b.py": ["tvc"]})
        return self.toy.commit("declare a receipt-backed input")

    CONSUMER = ("import json, sys\nout = sys.argv[sys.argv.index('--out') + 1]\n"
                "json.dump({0}, open(out, 'w'))\nsys.exit({1})\n")

    def test_a_receipt_backed_input_without_its_consumer_blocks_only_changes_that_select_the_set(self) -> None:
        base = self.receipt_inputs(None)
        self.toy.write("src/a.py", "A = 2\n")
        self.toy.commit("change a")
        code, record = self.select(base)
        self.assertEqual((code, record["disposition"], record["input_unavailable"]), (0, "SELECTED", []))
        self.toy.write("src/b.py", "B = 2\n")
        self.toy.commit("change b")
        code, record = self.select(base)
        self.assertEqual((code, record["disposition"]), (1, "FAIL_CLOSED"))
        [item] = record["input_unavailable"]
        self.assertEqual((item["failure_code"], item["failed_predicate"], item["set"], item["input"],
                          item["owning_existing_goal"]),
                         (sel.INPUT_UNAVAILABLE, sel.RECEIPT_PREDICATE, "tests/test_b.py", "tvc", "Lane C (toy#164)"))
        self.assertTrue(all(item[k] for k in sel.SIX))
        self.assertIn("not present at this head (toy#3332, not merged)", item["required_evidence_or_repair"])
        self.assertNotIn("tests.test_b", record["run"]["tests"])
        # an environment path or checkout does not satisfy a receipt-backed input
        code, record = self.select(base, {"STEGVERSE_TVC_ROOT": str(self.toy.path)})
        self.assertEqual((code, record["disposition"]), (1, "FAIL_CLOSED"))

    def test_only_a_consumer_allow_satisfies_a_receipt_backed_input_and_the_set_is_not_run_here(self) -> None:
        refused = {"disposition": "FAIL_CLOSED", "refusals": [{"failed_predicate": "TVC_CONFORMANCE_RECEIPT_ON_ORGANIZATION_LEDGER"}]}
        base = self.receipt_inputs(self.CONSUMER.format(repr(refused), 1))
        self.toy.write("src/b.py", "B = 2\n")
        self.toy.commit("change b")
        code, record = self.select(base)
        [item] = record["input_unavailable"]
        self.assertEqual((code, item["failed_predicate"]), (1, sel.RECEIPT_PREDICATE))
        self.assertIn("TVC_CONFORMANCE_RECEIPT_ON_ORGANIZATION_LEDGER", item["required_evidence_or_repair"])
        # ALLOW without a bound receipt, or with a non-zero exit, is not ALLOW
        self.toy.write("scripts/consume.py", self.CONSUMER.format(repr({"disposition": "ALLOW", "refusals": []}), 0))
        self.toy.commit("allow without a receipt")
        self.assertEqual(self.select(base)[0], 1)
        allow = {"disposition": "ALLOW", "refusals": [], "bound_receipt_sha256": "sha256:" + "a" * 64,
                 "bound_by_organization_receipt_sha256": "sha256:" + "b" * 64}
        self.toy.write("scripts/consume.py", self.CONSUMER.format(repr(allow), 1))
        self.toy.commit("allow with a failing exit")
        self.assertEqual(self.select(base)[0], 1)
        self.toy.write("scripts/consume.py", self.CONSUMER.format(repr(allow), 0))
        self.toy.commit("allow")
        code, record = self.select(base)
        self.assertEqual((code, record["disposition"], record["input_unavailable"]), (0, "SELECTED", []))
        [entry] = [x for x in record["selected"] if x["id"] == "tests/test_b.py"]
        self.assertFalse(entry["runnable"])
        self.assertEqual(entry["satisfied_by_receipt"][0]["bound_receipt_sha256"], allow["bound_receipt_sha256"])
        self.assertEqual([r["set"] for r in record["satisfied_by_receipt"]], ["tests/test_b.py"])
        self.assertNotIn("tests.test_b", record["run"]["tests"])          # verified by the receipt, not run here

    def test_a_selection_change_and_a_main_push_reach_the_receipt_backed_set(self) -> None:
        base = self.receipt_inputs(None)
        self.toy.write(".stegverse/test-set-spec.json", (self.toy.path / ".stegverse/test-set-spec.json").read_text() + " ")
        self.toy.generate()
        self.toy.commit("touch the spec")
        code, record = self.select(base)
        self.assertEqual(record["mode"], "ALL")
        self.assertIn("tests/test_b.py", self.ids(record))
        self.assertEqual([i["set"] for i in record["input_unavailable"]], ["tests/test_b.py"])
        code, record = self.select(None)                                   # a push: no base, every set
        self.assertEqual(record["mode"], "ALL")
        self.assertEqual([i["set"] for i in record["input_unavailable"]], ["tests/test_b.py"])

    def test_a_set_is_callable_by_id(self) -> None:
        out = subprocess.run([sys.executable, str(ROOT / "scripts/test_set_selection.py"), "set", "--root",
                              str(self.toy.path), "--manifest", ".stegverse/test-sets.json", "--id", "tests/test_a.py"],
                             capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(out, ["tests.test_a"])

    # -- the adjudicated run of the selection ------------------------------------------------------------------

    def adjudicate(self, base: str) -> tuple[int, dict]:
        sel_path = Path(self.tmp.name) / "selection.json"
        args = (Path(self.tmp.name) / "args.txt").read_text().split()
        done = subprocess.run([sys.executable, "-m", "unittest", "-v", *args], cwd=self.toy.path, env=ENV,
                              capture_output=True, text=True)
        out = Path(self.tmp.name) / "unittest.txt"
        out.write_text(done.stdout + done.stderr)
        out_dir = Path(self.tmp.name) / "adjudication"
        code = drift.main(["pr", "--root", str(self.toy.path), "--base", base, "--baseline", "baseline.json",
                           "--unittest-output", str(out), "--unittest-modules", *args, "--suite-status",
                           str(done.returncode), "--selection", str(sel_path), "--hb-epoch", "469411750",
                           "--repository", "toy/repo", "--retry-entrypoint", "toy.yml", "--out-dir", str(out_dir)])
        return code, json.loads((out_dir / "pr-disposition.json").read_text())

    def test_a_skip_inside_a_selected_set_fails_closed_and_an_unselected_skip_is_not_run(self) -> None:
        skipping = ("import unittest\nclass T(unittest.TestCase):\n    @unittest.skip('needs an input')\n"
                    "    def test_ok(self):\n        pass\n")
        self.toy.write("tests/test_c.py", 'SOURCE = "src/c.py"\n' + skipping)
        base = self.toy.commit("test_c skips (not selected below)")
        self.toy.write("src/a.py", "A = 2\n")
        self.toy.commit("change a")
        self.select(base)
        code, record = self.adjudicate(base)
        self.assertEqual((code, record["disposition"]), (0, "ALLOW"), record)
        self.assertEqual(record["verification"]["selection"]["selected_count"], 2)
        self.assertNotIn("tests.test_c", json.dumps(record))
        self.toy.write("tests/test_a.py", 'SOURCE = "src/a.py"\n' + skipping)
        self.toy.commit("a selected test skips")
        self.select(base)
        code, record = self.adjudicate(base)
        self.assertEqual((code, record["disposition"], record["failure_code"]),
                         (1, "FAIL_CLOSED", "REQUIRED_VERIFICATION_SKIPPED"))
        row = next(r for r in record["tests"] if r.get("kind") == "SKIPPED")
        self.assertEqual(row["test"], "tests.test_a.T.test_ok")
        self.assertTrue(all(row[k] for k in drift.SIX))

    def test_an_unavailable_input_item_blocks_the_adjudicated_run_with_its_owner(self) -> None:
        self.toy.spec({"toy-sdk": {"check": {"kind": "unavailable", "reason": "not here"}, "owner": "P1 (toy#163)"}},
                      {"tests/test_b.py": ["toy-sdk"]})
        base = self.toy.commit("declare")
        self.toy.write("src/b.py", "B = 2\n")
        self.toy.commit("change b")
        self.select(base)
        code, record = self.adjudicate(base)
        self.assertEqual((code, record["failure_code"], record["owning_existing_goal"]),
                         (1, sel.INPUT_UNAVAILABLE, "P1 (toy#163)"))

    def test_an_unavailable_input_item_also_blocks_a_pytest_adjudication(self) -> None:
        self.toy.spec({"toy-sdk": {"check": {"kind": "unavailable", "reason": "not here"}, "owner": "P1 (toy#163)"}},
                      {"tests/test_b.py": ["toy-sdk"]})
        base = self.toy.commit("declare")
        self.toy.write("src/b.py", "B = 2\n")
        self.toy.commit("change b")
        self.select(base)
        pytest_out = Path(self.tmp.name) / "pytest.txt"
        pytest_out.write_text("..\n\n2 passed in 0.01s\n")
        out_dir = Path(self.tmp.name) / "adjudication-pytest"
        code = drift.main(["pr", "--root", str(self.toy.path), "--base", base, "--baseline", "baseline.json",
                           "--pytest-output", str(pytest_out), "--suite-status", "0", "--selection",
                           str(Path(self.tmp.name) / "selection.json"), "--hb-epoch", "469411750",
                           "--repository", "toy/repo", "--retry-entrypoint", "toy.yml", "--out-dir", str(out_dir)])
        record = json.loads((out_dir / "pr-disposition.json").read_text())
        self.assertEqual(code, 1)
        self.assertEqual(record["disposition"], "FAIL_CLOSED")
        rows = [r for r in record["tests"] if r.get("failure_code") == sel.INPUT_UNAVAILABLE]
        self.assertEqual([(r["test"], r["owning_existing_goal"]) for r in rows], [("set:tests/test_b.py", "P1 (toy#163)")])

    def test_a_tampered_selection_fails_closed(self) -> None:
        self.toy.write("src/a.py", "A = 2\n")
        self.toy.commit("change a")
        self.select(self.toy.base)
        path = Path(self.tmp.name) / "selection.json"
        record = json.loads(path.read_text())
        record["run"]["tests"] = ["tests.test_core"]
        path.write_text(json.dumps(record))
        (Path(self.tmp.name) / "args.txt").write_text("tests.test_core\n")
        code, out = self.adjudicate(self.toy.base)
        self.assertEqual(code, 1)
        self.assertTrue(any(r.get("kind") == "SELECTION_UNVERIFIED" for r in out["tests"]))

    # -- the record binds the exact head and base ---------------------------------------------------------------

    def test_the_sealed_selection_binds_the_exact_head_base_and_pull_request_head(self) -> None:
        self.toy.write("src/a.py", "A = 2\n")
        head = self.toy.commit("change a")
        code, record = self.select(self.toy.base)
        self.assertEqual((record["head_sha"], record["base_sha"]), (head, self.toy.base))
        self.assertEqual(record["head_parents"], [self.toy.base])
        tampered = dict(record, head_sha=self.toy.base)
        self.assertFalse(sel.seal_verifies(tampered))
        # a merge ref built from the pull request head: the PR head is its second parent
        self.toy.git("checkout", "-q", "-b", "pr", head)
        self.toy.git("checkout", "-q", "main")
        self.toy.git("reset", "-q", "--hard", self.toy.base)
        self.toy.write("src/c.py", "C = 2\n")
        main2 = self.toy.commit("main moves")
        self.toy.git("merge", "-q", "--no-ff", "-m", "merge ref", "pr")
        merge = self.toy.git("rev-parse", "HEAD")
        rec = sel.select(self.toy.path, json.loads((self.toy.path / ".stegverse/test-sets.json").read_text()),
                         sel.changed(self.toy.path, main2, "HEAD"), manifest_path=".stegverse/test-sets.json",
                         spec=None, spec_path=None, base=main2, head="HEAD", pr_head=head)
        self.assertEqual((rec["head_sha"], rec["head_parents"], rec["pr_head_sha"]), (merge, [main2, head], head))
        self.assertEqual(rec["rows"], [])
        wrong = sel.select(self.toy.path, json.loads((self.toy.path / ".stegverse/test-sets.json").read_text()),
                           sel.changed(self.toy.path, main2, "HEAD"), manifest_path=".stegverse/test-sets.json",
                           spec=None, spec_path=None, base=main2, head="HEAD", pr_head=self.toy.base)
        self.assertEqual(wrong["disposition"], "FAIL_CLOSED")
        self.assertEqual(wrong["failure_code"], "TEST_SET_SELECTION_HEAD_IS_NOT_THE_PULL_REQUEST_HEAD")

    def test_an_unresolvable_base_or_head_fails_closed(self) -> None:
        manifest = json.loads((self.toy.path / ".stegverse/test-sets.json").read_text())
        rec = sel.select(self.toy.path, manifest, None, manifest_path=".stegverse/test-sets.json", spec=None,
                         spec_path=None, base="0" * 40, head="no-such-ref")
        codes = [r["failure_code"] for r in rec["rows"]]
        self.assertEqual(codes, ["TEST_SET_SELECTION_HEAD_UNRESOLVED", "TEST_SET_SELECTION_BASE_UNRESOLVED"])
        self.assertEqual((rec["mode"], rec["disposition"]), ("ALL", "FAIL_CLOSED"))

    def test_a_selection_computed_for_another_head_fails_closed_in_the_adjudication(self) -> None:
        self.toy.write("src/a.py", "A = 2\n")
        self.toy.commit("change a")
        self.select(self.toy.base)
        code, record = self.adjudicate(self.toy.base)
        self.assertEqual((code, record["disposition"]), (0, "ALLOW"), record)
        self.assertEqual(record["verification"]["selection"]["head_sha"], self.toy.git("rev-parse", "HEAD"))
        self.toy.write("src/a.py", "A = 3\n")      # the head moves; the old (validly sealed) record is reused
        self.toy.commit("change a again")
        code, record = self.adjudicate(self.toy.base)
        self.assertEqual(code, 1)
        row = next(r for r in record["tests"] if r.get("kind") == "SELECTION_HEAD_MISMATCH")
        self.assertEqual(row["failed_predicate"], "TEST_SET_SELECTION_IS_BOUND_TO_THIS_EXACT_HEAD")
        self.assertTrue(all(row[k] for k in drift.SIX))
        code, record = self.adjudicate(self.toy.git("rev-parse", "HEAD~1"))
        self.assertTrue(any(r.get("kind") == "SELECTION_BASE_MISMATCH" for r in record["tests"]))


class UnittestNamesTests(unittest.TestCase):
    def test_fixture_bases_and_mixins_are_not_runnable_units_and_inherited_tests_are_listed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "t.py").write_text(
                "import unittest\n"
                "class Fixture(unittest.TestCase):\n    def setUp(self):\n        pass\n"
                "class Mixin:\n    def test_shared(self):\n        pass\n"
                "class A(Fixture):\n    def test_a(self):\n        pass\n"
                "class B(Mixin, unittest.TestCase):\n    def test_b(self):\n        pass\n")
            names = sel.unittest_names(Path(tmp), "t.py")
        self.assertEqual(names, {"A": ["test_a"], "B": ["test_b", "test_shared"]})


class ThisRepositoryTests(unittest.TestCase):
    def test_the_committed_manifest_is_generated_from_the_spec(self) -> None:
        spec = json.loads((ROOT / ".stegverse/test-set-spec.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / ".stegverse/test-sets.json").read_text(encoding="utf-8"))
        self.assertEqual(sel.canonical(sel.generate(ROOT, spec, ".stegverse/test-set-spec.json")),
                         sel.canonical(manifest))
        listed = {t.split("::")[0] for s in manifest["sets"] for t in s["tests"]}
        self.assertEqual(listed, set(sel.test_files(ROOT, sel.repo_files(ROOT), spec["test_globs"])))
        for s in manifest["sets"]:
            for name in s["inputs"]:
                decl = manifest["inputs"][name]
                self.assertTrue(decl["owner"] and decl["finish_point"] and decl["check"]["kind"], name)

    def test_the_tvc_sets_reach_what_they_load_by_path_and_are_receipt_backed(self) -> None:
        manifest = json.loads((ROOT / ".stegverse/test-sets.json").read_text(encoding="utf-8"))
        sets = {s["id"]: s for s in manifest["sets"]}
        canon = sets["tests/test_canonical_work_in_process_admission.py[tvc]"]
        reach = sel.closure(manifest["surface_graph"], canon["surfaces"])
        for path in ("org-kernel/node_store.py", "heartbeat_runtime/engine_v2.py", "heartbeat_runtime/worker_task_admission.py",
                     "resident-runtime/organization_egress_boundary.py", "tests/test_origin_attestation_tvc_conformance.py"):
            self.assertIn(path, reach)
        origin = sets["tests/test_origin_attestation_tvc_conformance.py[tvc]"]
        self.assertIn("org-kernel/node_store.py", sel.closure(manifest["surface_graph"], origin["surfaces"]))
        for shared in ("tests/__init__.py", "tests/conftest.py",           # read by every pytest run
                       "scripts/test_set_selection.py", ".github/workflows/test-suite-ratchet.yml",
                       ".stegverse/test-set-spec.json", ".stegverse/test-sets.json"):  # shape selection: ALL
            self.assertTrue(any(sel.glob_match(g, shared) for g in manifest["selects_all"]), shared)
        check = manifest["inputs"]["tvc"]["check"]
        self.assertEqual((check["kind"], check["consumer"], check["allow"]),
                         (sel.RECEIPT_KIND, "scripts/tvc_conformance_receipt.py", "ALLOW"))
        self.assertEqual(canon["inputs"], ["tvc"])
        self.assertEqual(origin["inputs"], ["tvc"])

    def test_the_ratchet_runs_the_selection_and_nothing_else(self) -> None:
        text = (ROOT / ".github/workflows/test-suite-ratchet.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/test_set_selection.py select", text)
        self.assertIn('python -m pytest "${selected[@]}"', text)
        self.assertIn("--selection /tmp/test-set-selection.json", text)
        self.assertNotIn("python -m pytest tests ", text)
        self.assertNotIn("check_test_suite_ratchet.py --findings", text)   # no second, unselected run
        for word in ("schedule:", "cron", "contents: write"):
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
