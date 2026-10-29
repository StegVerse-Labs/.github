"""Adjacency-ruling input to the collision check-in (scripts/adjacency_ruling.py), both ways, E0, no network.

A ruling is never trusted: each test changes observed state (records, the finish-point source) or the ruling
itself and checks the recomputation, not the ruling's claims, decides.
"""
from __future__ import annotations

import copy
import importlib.util
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KV_REQUEST = ROOT / "tests" / "fixtures" / "canonical_task_registration" / "i1-goal-manifests" / "KV-SKAP-VAULT-FUNCTIONAL-001.request.json"
KV_RULING = ROOT / "control" / "adjacency-rulings" / "KV-SKAP-VAULT-FUNCTIONAL-001.json"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ar = _load("adjacency_ruling_under_test", "scripts/adjacency_ruling.py")
transition = _load("transition_under_test_for_ruling", "scripts/canonical_task_registration_transition.py")


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def make_repo(files: dict[str, str]) -> tuple[Path, str]:
    root = Path(tempfile.mkdtemp(prefix="fp-repo-"))
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "fixture")
    return root, git(root, "rev-parse", "HEAD")


OWN_TEST = ("import subprocess\nfrom runtime import vault\n"
            "def test_x():\n    subprocess.run(['python', '-m', 'runtime.vault'])\n")
FILES = {"tests/test_fp.py": OWN_TEST, "runtime/vault.py": "import json\n",
         "runtime/task_registry_binding.py": "X = 1\n", "runtime/helper.py": "Y = 2\n"}


def candidate(task_id="CAND-A-001", components=("task-registry", "custody-projection"), refs=()):
    return {"schema": "stegverse.canonical-task-record/v1", "task_id": task_id, "parent_task_id": None,
            "root_correlation_id": task_id, "coordination_state": "ACTIVE",
            "targets": {"repositories": ["Org/fp"], "components": list(components)},
            "source_refs": list(refs), "adjacent_task_refs": []}


def request(components=("vault-module", "consent-receipt"), deps=("CAND-A-001",),
            test="Org/fp:tests/test_fp.py::test_x"):
    record = {"task_id": "SUBJ-001", "parent_task_id": None, "root_correlation_id": "SUBJ-001",
              "targets": {"repositories": ["Org/fp"], "components": list(components)},
              "dependencies": [{"dependency_id": f"TASK-{d}", "kind": "TASK", "state": "UNRESOLVED", "ref": d} for d in deps],
              "adjacent_task_refs": ["CAND-A-001"]}
    return {"task_id": "SUBJ-001", "record": record,
            "sealed_scope": {"scope": {"finish_point": {"acceptance_test": test}}}}


def ruling(commit, req, cands, consumes=("CAND-A-001",)):
    body = {"schema": ar.SCHEMA, "task_id": "SUBJ-001", "ruling_class": "D", "ruling": "ADJACENT_NOT_DUPLICATE",
            "ruled_by": "Coordination (test)",
            "subject": {"components": sorted(req["record"]["targets"]["components"]),
                        "finish_point": {"acceptance_test": req["sealed_scope"]["scope"]["finish_point"]["acceptance_test"],
                                         "repository": "Org/fp", "source_commit": commit}},
            "candidates": [{"task_id": c["task_id"], "components": sorted(c["targets"]["components"]),
                            "finish_point_paths": []} for c in cands],
            "consumes_dependencies": [{"task_id": t} for t in consumes], "evidence_digest": ""}
    body["evidence_digest"] = ar.ruling_digest(body)
    return body


class AdjacencyRulingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="ruling-base-"))
        shutil.copytree(ROOT / "scripts", self.base / "scripts")
        (self.base / ar.RECORDS).mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.base, True)

    def put(self, record) -> None:
        (self.base / ar.RECORDS / f"{record['task_id']}.json").write_text(json.dumps(record), encoding="utf-8")

    def fp(self, files=None):
        root, commit = make_repo(files or FILES)
        self.addCleanup(shutil.rmtree, root, True)
        return root, commit

    def refused(self, verdict, code):
        self.assertEqual(verdict["disposition"], "FAIL_CLOSED", verdict)
        self.assertEqual(verdict["failure_code"], code, verdict)
        for field in SIX:
            self.assertTrue(verdict[field], field)

    # -- ALLOW ------------------------------------------------------------------------------------------------
    def test_conditions_recompute_and_allow(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp()
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.assertEqual(verdict["disposition"], "ALLOW", verdict)
        self.assertEqual(sorted(verdict["finish_point"]["closure"]),
                         ["runtime/vault.py", "tests/test_fp.py"])
        self.assertEqual(verdict["candidates"][0]["condition_b"], "HELD")
        self.assertFalse(verdict["clock_read"] or verdict["network_used"] or verdict["llm_used"])

    def test_subprocess_module_string_is_in_the_closure(self) -> None:
        files = dict(FILES, **{"tests/test_fp.py": "import subprocess\nsubprocess.run(['python','-m','runtime.helper'])\n"})
        root, commit = self.fp(files)
        self.assertIn("runtime/helper.py", ar.static_closure(root, "tests/test_fp.py"))

    # -- (b) recomputed ---------------------------------------------------------------------------------------
    def test_b_fails_when_the_test_reaches_a_module_named_for_a_candidate_component(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp(dict(FILES, **{"tests/test_fp.py": "from runtime import task_registry_binding\n"}))
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.refused(verdict, "ADJACENCY_CONDITION_B_NOT_HELD")
        self.assertEqual(verdict["detail"][0]["component"], "task-registry")

    def test_b_fails_when_the_test_reaches_a_path_the_candidate_names(self) -> None:
        cand = candidate(refs=["Org/fp/runtime/helper.py"])
        self.put(cand)
        root, commit = self.fp(dict(FILES, **{"runtime/vault.py": "from runtime import helper\n"}))
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.refused(verdict, "ADJACENCY_CONDITION_B_NOT_HELD")
        self.assertEqual(verdict["detail"][0]["reason"], "PATH_NAMED_BY_CANDIDATE_RECORD")

    def test_b_needs_the_source_at_the_pinned_commit(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp()
        req = request()
        good = ruling(commit, req, [cand])
        self.refused(ar.verify(good, req, self.base, None), "ADJACENCY_RULING_FINISH_POINT_SOURCE_UNAVAILABLE")
        (root / "runtime" / "vault.py").write_text("from runtime import task_registry_binding\n", encoding="utf-8")
        git(root, "commit", "-qam", "drift")
        self.refused(ar.verify(good, req, self.base, root), "ADJACENCY_RULING_FINISH_POINT_SOURCE_UNAVAILABLE")

    # -- (b) dynamic loads in the closure: resolved from constants, or FAIL_CLOSED ---------------------------
    RUN_GATE = ("import importlib\nfrom pathlib import Path\n"
                "def _sdk_module(name):\n    return importlib.import_module(f'pkg.{name}')\n"
                "def run_gate(manifest):\n    validator = _sdk_module('structural_validator_candidate')\n"
                "    return validator.check(manifest)\n")

    def gate_files(self, gate=None, test="from pkg import gate\ndef test_x():\n    gate.run_gate({})\n"):
        return dict(FILES, **{"tests/test_fp.py": test, "pkg/__init__.py": "", "pkg/gate.py": gate or self.RUN_GATE,
                              "pkg/structural_validator_candidate.py": "def check(m):\n    return m\n",
                              "pkg/other.py": "Z = 3\n", "pkg/tables_a.py": "", "pkg/tables_b.py": "",
                              "scripts/loaded.py": "", "pkg/sibling.py": "", "pkg/run_me.py": "", "pkg/exec_me.py": ""})

    def test_run_gate_by_name_load_is_in_the_closure_and_fails_b(self) -> None:
        root, commit = self.fp(self.gate_files())
        closure = ar.static_closure(root, "tests/test_fp.py")
        self.assertIn("pkg/structural_validator_candidate.py", closure)
        self.assertNotIn("pkg/other.py", closure)
        cand = candidate(components=("structural-validator", "validator-inventory"))
        self.put(cand)
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.refused(verdict, "ADJACENCY_CONDITION_B_NOT_HELD")
        self.assertEqual(verdict["detail"][0]["path"], "pkg/structural_validator_candidate.py")

    def test_run_gate_load_with_unrelated_candidate_still_allows(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp(self.gate_files())
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.assertEqual(verdict["disposition"], "ALLOW", verdict)
        self.assertIn("pkg/structural_validator_candidate.py", verdict["finish_point"]["closure"])

    def test_constant_tables_paths_runpy_exec_and_aliases_resolve(self) -> None:
        gate = ("import importlib, importlib.util as iu, runpy\nfrom importlib import import_module as im\n"
                "from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n"
                "MODULES = ('pkg.tables_a', 'pkg.tables_b')\nNAMES = {'x': 'pkg.other'}\n"
                "def load_all():\n    for m in MODULES:\n        importlib.import_module(m)\n"
                "    im(NAMES['x'])\n    __import__('pkg.' + 'sibling')\n"
                "    iu.spec_from_file_location('l', ROOT / 'scripts' / 'loaded.py')\n"
                "    runpy.run_path(str(Path(__file__).with_name('run_me.py')))\n"
                "    exec(compile(open(ROOT / 'pkg' / 'exec_me.py').read(), 'e', 'exec'))\n"
                "    exec('import pkg.structural_validator_candidate')\n")
        root, _ = self.fp(self.gate_files(gate))
        closure = ar.static_closure(root, "tests/test_fp.py")
        for rel in ("pkg/tables_a.py", "pkg/tables_b.py", "pkg/other.py", "pkg/sibling.py", "scripts/loaded.py",
                    "pkg/run_me.py", "pkg/exec_me.py", "pkg/structural_validator_candidate.py"):
            self.assertIn(rel, closure, rel)

    # -- stub-seeded packages: __init__ left out only when every path loads under a provable stub -------------
    ENSURE = ("import importlib, sys, types\nfrom pathlib import Path\n"
              "def _sdk_module(name):\n    package = sys.modules.get('pkg')\n"
              "    if package is None or not hasattr(package, '__path__'):\n"
              "        package = types.ModuleType('pkg')\n        package.__path__ = [str(Path(__file__).parent)]\n"
              "        sys.modules['pkg'] = package\n    return importlib.import_module(f'pkg.{name}')\n"
              "def run():\n    return _sdk_module('verifier')\n")
    UNCOND = ("import importlib, sys, types\n"
              "def run():\n    stub = types.ModuleType('pkg')\n    stub.__path__ = ['pkg']\n"
              "    sys.modules['pkg'] = stub\n    return importlib.import_module('pkg.verifier')\n")
    BY_PATH = ("import importlib.util\nfrom pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n"
               "spec = importlib.util.spec_from_file_location('g', ROOT / 'pkg/gate.py')\n")

    RUNNER = "jobs:\n  fp:\n    steps:\n      - run: python -m unittest tests.test_fp -v\n"

    def stub_closure(self, gate, test=None, extra=None):
        files = dict(FILES, **{"tests/test_fp.py": test or self.BY_PATH, "pkg/gate.py": gate,
                               "pkg/__init__.py": "from . import danger\n", "pkg/danger.py": "D = 1\n",
                               "pkg/verifier.py": "from .helper import H\n", "pkg/helper.py": "H = 1\n",
                               "pkg/other.py": "O = 1\n", ".github/workflows/fp.yml": self.RUNNER})
        files.update(extra or {})
        files = {k: v for k, v in files.items() if v is not None}
        root, _ = self.fp(files)
        notes = {}
        return ar.static_closure(root, "tests/test_fp.py", notes), notes

    def assert_stub(self, closure) -> None:
        self.assertIn("pkg/verifier.py", closure)
        self.assertIn("pkg/helper.py", closure)  # relative import inside the stub-only module
        self.assertNotIn("pkg/__init__.py", closure)
        self.assertNotIn("pkg/danger.py", closure)

    def assert_init(self, closure) -> None:
        self.assertIn("pkg/verifier.py", closure)
        self.assertIn("pkg/__init__.py", closure)
        self.assertIn("pkg/danger.py", closure)

    def test_stub_seeded_ensure_idiom_excludes_init(self) -> None:
        closure, notes = self.stub_closure(self.ENSURE)
        self.assert_stub(closure)
        self.assertEqual(notes["stub_contexts"]["pkg/helper.py"], ["S:pkg"])
        self.assertEqual(notes["stub_contexts_disabled_by"], [])

    def test_stub_seeded_unconditionally_excludes_init(self) -> None:
        self.assert_stub(self.stub_closure(self.UNCOND)[0])

    def test_normal_import_elsewhere_keeps_init(self) -> None:
        self.assert_init(self.stub_closure(self.ENSURE, self.BY_PATH + "import pkg.other\n")[0])
        # the stub-only module reached normally too: its relative imports run under the real package
        self.assert_init(self.stub_closure(self.ENSURE, self.BY_PATH + "from pkg import verifier\n")[0])

    def test_conditional_seeding_keeps_init(self) -> None:
        gate = self.UNCOND.replace("    stub = ", "    if os.environ.get('SEED'):\n        stub = ").replace(
            "    stub.__path__", "        stub.__path__").replace("    sys.modules['pkg'] = stub",
                                                                 "        sys.modules['pkg'] = stub")
        self.assert_init(self.stub_closure("import os\n" + gate)[0])

    def test_non_constant_or_late_or_pathless_seeding_keeps_init(self) -> None:
        self.assert_init(self.stub_closure(self.UNCOND.replace("sys.modules['pkg']", "sys.modules[NAME]")
                                           + "NAME = 'pkg'\n")[0])
        self.assert_init(self.stub_closure(self.UNCOND.replace("types.ModuleType('pkg')", "types.ModuleType(N)")
                                           + "N = 'pkg'\n")[0])
        late = ("import importlib, sys, types\ndef run():\n    m = importlib.import_module('pkg.verifier')\n"
                "    stub = types.ModuleType('pkg')\n    stub.__path__ = []\n    sys.modules['pkg'] = stub\n    return m\n")
        self.assert_init(self.stub_closure(late)[0])
        self.assert_init(self.stub_closure(self.UNCOND.replace("    stub.__path__ = ['pkg']\n", ""))[0])
        other_fn = ("import importlib, sys, types\ndef seed():\n    stub = types.ModuleType('pkg')\n"
                    "    stub.__path__ = []\n    sys.modules['pkg'] = stub\n"
                    "def run():\n    seed()\n    return importlib.import_module('pkg.verifier')\n")
        self.assert_init(self.stub_closure(other_fn)[0])

    def test_removal_from_sys_modules_in_the_closure_keeps_init(self) -> None:
        closure, notes = self.stub_closure(self.ENSURE + "def reset():\n    sys.modules.pop('pkg', None)\n")
        self.assert_init(closure)
        self.assertEqual(notes["stub_contexts_disabled_by"],
                         [{"source": "pkg/gate.py", "reason": "SYS_MODULES_REMOVAL_IN_CLOSURE", "line": 13}])

    def test_guarded_seed_with_a_normal_import_in_another_closure_file_keeps_init(self) -> None:
        closure, notes = self.stub_closure(self.ENSURE, self.BY_PATH + "import side\n",
                                           {"side.py": "import pkg.other\n"})
        self.assert_init(closure)
        self.assertIn("side.py", closure)
        self.assertEqual(notes["stub_contexts_disabled_by"], [])  # kept by the closure itself: an N path imports pkg

    def reasons(self, notes):
        return [r["reason"] for r in notes["stub_contexts_disabled_by"]]

    def test_preload_from_outside_the_closure_keeps_init(self) -> None:
        cases = {
            "conftest": ({"tests/conftest.py": "import pkg.other\n"}, "PRELOAD_IMPORTS_STUB_PACKAGE"),
            "root conftest via helper": ({"conftest.py": "import side\n", "side.py": "from pkg import other\n"},
                                         "PRELOAD_IMPORTS_STUB_PACKAGE"),
            "test package": ({"tests/__init__.py": "import pkg\n"}, "PRELOAD_IMPORTS_STUB_PACKAGE"),
            "pytest.ini -p": ({"pytest.ini": "[pytest]\naddopts = -q -p pkg.other\n"},
                              "PYTEST_PLUGIN_IMPORTS_STUB_PACKAGE"),
            "pyproject -p external": ({"pyproject.toml": "[tool.pytest.ini_options]\naddopts = ['-p', 'xdist']\n"},
                                      "PYTEST_PLUGIN_NOT_IN_REPOSITORY"),
            "setup.cfg pytest11": ({"setup.cfg": "[options.entry_points]\npytest11 =\n    p = pkg.other\n"},
                                   "PYTEST_PLUGIN_IMPORTS_STUB_PACKAGE"),
            "tox.ini redirect": ({"tox.ini": "[pytest]\naddopts = -c other.ini\n"}, "PYTEST_CONFIG_REDIRECTED"),
            "sitecustomize": ({"sitecustomize.py": "import pkg.other\n"}, "PRELOAD_IMPORTS_STUB_PACKAGE"),
            "pth import": ({"x.pth": "import pkg\n"}, "PTH_IMPORTS_STUB_PACKAGE"),
            "pth code": ({"x.pth": "import os; os.environ.get('X')\n"}, "PTH_LINE_NOT_STATIC"),
            "conftest dynamic": ({"tests/conftest.py": "import importlib, os\nimportlib.import_module(os.environ['M'])\n"},
                                 "PRELOAD_LOAD_UNRESOLVED"),
            "no runner": ({".github/workflows/fp.yml": None}, "FINISH_TEST_RUNNER_NOT_OBSERVED"),
            "runner variable": ({".github/workflows/fp.yml": "steps:\n  - run: python -m unittest $T tests.test_fp\n"},
                                "RUNNER_COMMAND_NOT_STATIC"),
            "runner -W": ({".github/workflows/fp.yml": "steps:\n  - run: python -W error::pkg.W -m unittest tests.test_fp\n"},
                          "RUNNER_COMMAND_NAMES_STUB_PACKAGE"),
            "pytest autoload": ({".github/workflows/fp.yml": "steps:\n  - run: python -m pytest -q tests/test_fp.py\n"},
                                "PYTEST_PLUGIN_AUTOLOAD_UNRESOLVED"),
            "pytest env plugins": ({".github/workflows/fp.yml": "env:\n  PYTEST_DISABLE_PLUGIN_AUTOLOAD: 1\n"
                                    "  PYTEST_PLUGINS: pkg.other\nsteps:\n  - run: pytest tests/test_fp.py\n"},
                                   "PYTEST_PLUGIN_IMPORTS_STUB_PACKAGE"),
            "repo runner": ({"runner.py": "import pkg.other\n",
                             ".github/workflows/fp.yml": "steps:\n  - run: python runner.py tests/test_fp.py\n"},
                            "PRELOAD_IMPORTS_STUB_PACKAGE"),
            "repo -m shadow": ({"unittest/__init__.py": "", "unittest/__main__.py": "import pkg\n"},
                               "PRELOAD_IMPORTS_STUB_PACKAGE"),
            "unknown -m": ({".github/workflows/fp.yml": "steps:\n  - run: python -m nose2 tests.test_fp\n"},
                           "RUNNER_MODULE_NOT_IN_REPOSITORY"),
        }
        for name, (extra, reason) in cases.items():
            with self.subTest(name):
                closure, notes = self.stub_closure(self.ENSURE, extra=extra)
                self.assert_init(closure)
                self.assertIn(reason, self.reasons(notes), notes["stub_contexts_disabled_by"])

    def test_preload_sources_that_cannot_import_the_package_keep_the_stub(self) -> None:
        cases = {
            "conftest": {"tests/conftest.py": "import json\nfrom side import X\n", "side.py": "X = 1\n"},
            "pytest.ini no:": {"pytest.ini": "[pytest]\naddopts = -q -p no:cacheprovider\n"},
            "pytest no autoload": {".github/workflows/fp.yml": "env:\n  PYTEST_DISABLE_PLUGIN_AUTOLOAD: '1'\n"
                                   "steps:\n  - run: python -m pytest -q tests/test_fp.py\n"},
            "paths filter and runner": {".github/workflows/fp.yml": "on:\n  push:\n    paths:\n      - tests/test_fp.py\n"
                                        "jobs:\n  t:\n    steps:\n      - run: |\n          python -m unittest \\\n"
                                        "            tests.test_fp\n"},
            "repo runner clean": {"runner.py": "import sys\n",
                                  ".github/workflows/fp.yml": "steps:\n  - run: python runner.py tests/test_fp.py\n"},
        }
        for name, extra in cases.items():
            with self.subTest(name):
                closure, notes = self.stub_closure(self.ENSURE, extra=extra)
                self.assert_stub(closure)
                self.assertEqual(notes["stub_contexts_disabled_by"], [])
                self.assertTrue(notes["finish_test_runners"])

    def assert_unresolved(self, gate, test=None) -> None:
        cand = candidate()
        self.put(cand)
        files = self.gate_files(gate) if test is None else self.gate_files(gate, test)
        root, commit = self.fp(files)
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.refused(verdict, "ADJACENCY_RULING_FINISH_POINT_CLOSURE_UNRESOLVED")
        self.assertEqual(verdict["detail"][0]["path"], "pkg/gate.py")

    def test_data_driven_binding_fails_closed_never_disjoint(self) -> None:
        self.assert_unresolved("import importlib\ndef _load(binding):\n"
                               "    module_name, fn = binding.rsplit('.', 1)\n"
                               "    return importlib.import_module(module_name)\n"
                               "def run_gate(route):\n    return _load(route['binding'])\n")

    def test_public_loader_parameter_fails_closed(self) -> None:
        self.assert_unresolved("import importlib\ndef load(name):\n    return importlib.import_module(name)\n"
                               "def run_gate(m):\n    return load('pkg.other')\n")

    def test_private_loader_reached_from_another_module_fails_closed(self) -> None:
        cand = candidate()
        self.put(cand)
        test = "from pkg import gate\nfrom pkg.gate import _sdk_module\ndef test_x():\n    _sdk_module('other')\n"
        root, commit = self.fp(self.gate_files(test=test))
        req = request()
        verdict = ar.verify(ruling(commit, req, [cand]), req, self.base, root)
        self.refused(verdict, "ADJACENCY_RULING_FINISH_POINT_CLOSURE_UNRESOLVED")
        self.assertEqual(verdict["detail"][0]["path"], "tests/test_fp.py")

    def test_exec_of_runtime_text_and_env_paths_fail_closed(self) -> None:
        self.assert_unresolved("import os, runpy\ndef run_gate(src):\n    exec(src)\n")
        self.assert_unresolved("import os, runpy\ndef run_gate():\n    runpy.run_path(os.environ['P'])\n")

    def test_reassigned_module_constant_fails_closed(self) -> None:
        self.assert_unresolved("import importlib\nNAME = 'pkg.other'\ndef _f():\n    global NAME\n    NAME = input()\n"
                               "def run_gate():\n    importlib.import_module(NAME)\n")

    # -- (P) consumed-source pin and (R) owner routing ----------------------------------------------------------
    def pinned_fixture(self, *, edit_consumed=False, carry_pin=True, gate_loads=None):
        root = Path(tempfile.mkdtemp(prefix="fp-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        for rel, text in FILES.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")
        (root / "gate").mkdir()
        (root / "gate" / "__init__.py").write_text("", encoding="utf-8")
        (root / "gate" / "step.yml").write_text("run: exit 1\n", encoding="utf-8")
        reader = "def read():\n    return 'FAIL_CLOSED'\n"
        if gate_loads:
            reader = f"import importlib\ndef read():\n    return importlib.import_module('{gate_loads}')\n"
            (root / Path(*gate_loads.split("."))).with_suffix(".py").write_text("X = 1\n", encoding="utf-8")
        (root / "gate" / "gate_reader.py").write_text(reader, encoding="utf-8")
        git(root, "init", "-q")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "owner")
        pin_commit = git(root, "rev-parse", "HEAD")
        files = {rel: hashlib.sha256((root / rel).read_bytes()).hexdigest() for rel in ("gate/step.yml", "gate/gate_reader.py")}
        carried = f"PIN = {json.dumps({'commit': pin_commit, 'files': files})}\n" if carry_pin else "PIN = {}\n"
        (root / "tests" / "test_fp.py").write_text(carried + "from gate import gate_reader\n", encoding="utf-8")
        if edit_consumed:
            (root / "gate" / "gate_reader.py").write_text("def read():\n    return 'ALLOW'\n", encoding="utf-8")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "subject")
        return root, pin_commit, git(root, "rev-parse", "HEAD"), files

    def pinned_ruling(self, commit, pin_commit, files, mutate=None):
        cand = candidate(components=("gate-reader", "validator-inventory"))
        self.put(cand)
        req = request()
        body = ruling(commit, req, [cand])
        paths = sorted(files)
        body["candidates"][0]["finish_point_paths"] = paths
        body["consumes_dependencies"][0]["pinned_source"] = {"repository": "Org/fp", "commit": pin_commit, "files": dict(files)}
        body["protected_paths"] = [{"repository": "Org/fp", "owner_task_id": "CAND-A-001", "paths": paths,
                                    "on_modification": {"disposition": "FAIL_CLOSED", "failure_code": "OWNER_OWNED_EDIT",
                                                        "routed_to": "CAND-A-001"}}]
        if mutate:
            mutate(body)
        body["evidence_digest"] = ar.ruling_digest(body)
        return body, req

    # -- (U) unowned consumed source: pinned, edit-guarded, routed to Coordination, never a candidate ------------
    def unowned_ruling(self, commit, pin_commit, files, mutate=None):
        cand = candidate()
        self.put(cand)
        req = request()
        body = ruling(commit, req, [cand])
        body["consumes_dependencies"].append({
            "task_id": ar.UNOWNED, "consumed_by": "the finish test reads gate/*", "provenance": "Org/fp#70",
            "pinned_source": {"repository": "Org/fp", "commit": pin_commit, "files": dict(files)}})
        if mutate:
            mutate(body)
        body["evidence_digest"] = ar.ruling_digest(body)
        return body, req

    def test_unowned_consumed_pin_allows_and_is_not_a_candidate(self) -> None:
        for carry in (True, False):
            with self.subTest(carry_pin=carry):
                root, pin, head, files = self.pinned_fixture(carry_pin=carry)
                body, req = self.unowned_ruling(head, pin, files)
                verdict = ar.verify(body, req, self.base, root)
                self.assertEqual(verdict["disposition"], "ALLOW", verdict)
                self.assertEqual(verdict["condition_unowned_pin"], "HELD")
                row = next(r for r in verdict["consumed_pins"] if r["task_id"] == ar.UNOWNED)
                self.assertEqual(row["edit_routed_to"], ar.OWNING_GOAL)
                self.assertEqual(row["enforced_by_finish_test"], carry)
                self.assertTrue(row["in_finish_point_closure"]["gate/gate_reader.py"])
                self.assertNotIn(ar.UNOWNED, [c["task_id"] for c in verdict["candidates"]])
                self.assertEqual(verdict["condition_routing"], "NOT_APPLICABLE")

    def test_unowned_consumed_edit_fails_closed_to_coordination(self) -> None:
        root, pin, head, files = self.pinned_fixture(edit_consumed=True)
        body, req = self.unowned_ruling(head, pin, files)
        verdict = ar.verify(body, req, self.base, root)
        self.refused(verdict, "ADJACENCY_RULING_UNOWNED_CONSUMED_EDIT")
        self.assertEqual(verdict["owning_existing_goal"], "STEGVERSE-CANONICAL-WORK-COORDINATION-001")
        self.assertEqual(verdict["detail"]["modified"], ["gate/gate_reader.py"])
        change = ar.check_change(body, root, pin, head)
        self.refused(change, "ADJACENCY_RULING_UNOWNED_CONSUMED_EDIT")
        clean_root, clean_pin, clean_head, clean_files = self.pinned_fixture()
        clean, _ = self.unowned_ruling(clean_head, clean_pin, clean_files)
        self.assertEqual(ar.check_change(clean, clean_root, clean_pin, clean_head)["disposition"], "ALLOW")

    def test_unowned_consumed_pin_malformed_cases(self) -> None:
        root, pin, head, files = self.pinned_fixture()
        bad_sha = dict(files, **{"gate/step.yml": "0" * 64})
        cases = [
            (lambda b: b["consumes_dependencies"][-1].pop("pinned_source"), files, "ADJACENCY_RULING_CONSUMED_PIN_MALFORMED"),
            (lambda b: b["consumes_dependencies"][-1]["pinned_source"].update(commit=pin[:12]), files,
             "ADJACENCY_RULING_CONSUMED_PIN_MALFORMED"),
            (lambda b: b["consumes_dependencies"].append(dict(b["consumes_dependencies"][-1])), files,
             "ADJACENCY_RULING_CONSUMED_PIN_MALFORMED"),
            (None, bad_sha, "ADJACENCY_RULING_CONSUMED_PIN_DIGEST_DIVERGES"),
            (lambda b: b.__setitem__("protected_paths", [{
                "repository": "Org/fp", "owner_task_id": ar.UNOWNED, "paths": sorted(files),
                "on_modification": {"disposition": "FAIL_CLOSED", "failure_code": "X", "routed_to": ar.UNOWNED}}]),
             files, "ADJACENCY_RULING_PROTECTED_PATHS_MALFORMED"),
            (lambda b: b["candidates"].append(dict(b["candidates"][0], task_id=ar.UNOWNED)), files,
             "ADJACENCY_RULING_SCHEMA_INVALID"),
        ]
        for i, (mutate, pinned, code) in enumerate(cases):
            with self.subTest(case=i, code=code):
                body, req = self.unowned_ruling(head, pin, pinned, mutate)
                self.refused(ar.verify(body, req, self.base, root), code)

    # -- (E) consumes-edit: an unowned consumed edit is admitted when re-pinned and receipted (scratch) -----------
    def repinned(self, root, head, files, mutate=None):
        new = dict(files, **{"gate/gate_reader.py": hashlib.sha256((root / "gate" / "gate_reader.py").read_bytes()).hexdigest()})
        return self.unowned_ruling(head, head, new, mutate)

    def test_unowned_consumed_edit_with_a_consumes_edit_receipt_allows(self) -> None:
        root, pin, head, files = self.pinned_fixture(edit_consumed=True)
        body, req = self.repinned(root, head, files)
        receipt = ar.consumes_edit(body, root, pin, head, "gate/gate_reader.py", "SUBJ-001", "Org/fp#9")
        self.assertEqual(receipt["disposition"], "ALLOW", receipt)
        self.assertEqual(receipt["ledger_status"], ar.SCRATCH)
        self.assertEqual(receipt["relationship"]["ruling_digest"], body["evidence_digest"])
        self.assertEqual(receipt["from"]["sha256"], files["gate/gate_reader.py"])
        self.assertEqual(receipt[ar.SEAL], ar.seal(receipt)[ar.SEAL])
        change = ar.check_change(body, root, pin, head, [receipt])
        self.assertEqual(change["disposition"], "ALLOW", change)
        self.assertEqual(change["consumes_edits"][0]["path"], "gate/gate_reader.py")
        # verify at the finish point holds on the moved pin; without the receipt check-change still fails closed
        self.assertEqual(ar.verify(body, req, self.base, root)["disposition"], "ALLOW")
        self.refused(ar.check_change(body, root, pin, head), "ADJACENCY_RULING_UNOWNED_CONSUMED_EDIT")
        self.assertIn("consumes-edit", ar.check_change(body, root, pin, head)["required_evidence_or_repair"])

    def test_consumes_edit_fails_closed_without_repin_relationship_or_matching_receipt(self) -> None:
        root, pin, head, files = self.pinned_fixture(edit_consumed=True)
        stale, _ = self.unowned_ruling(head, pin, files)  # pin not moved
        self.refused(ar.consumes_edit(stale, root, pin, head, "gate/gate_reader.py", "SUBJ-001"),
                     "ADJACENCY_RULING_UNOWNED_CONSUMED_EDIT")
        body, _ = self.repinned(root, head, files)
        self.refused(ar.consumes_edit(body, root, pin, head, "gate/gate_reader.py", "SOMEONE-ELSE-001"),
                     "ADJACENCY_RULING_CONSUMES_EDIT_RECEIPT_INVALID")
        self.refused(ar.consumes_edit(body, root, pin, head, "runtime/vault.py", "SUBJ-001"),
                     "ADJACENCY_RULING_CONSUMES_EDIT_RECEIPT_INVALID")
        good = ar.consumes_edit(body, root, pin, head, "gate/gate_reader.py", "SUBJ-001")
        tampered = dict(good, path="gate/gate_reader.py", to=dict(good["to"], sha256="0" * 64))
        self.refused(ar.check_change(body, root, pin, head, [tampered]), "ADJACENCY_RULING_CONSUMES_EDIT_RECEIPT_INVALID")
        resealed = ar.seal(dict(good, writer={"task_id": "SOMEONE-ELSE-001", "ref": "Org/fp#9"}))
        self.refused(ar.check_change(body, root, pin, head, [resealed]), "ADJACENCY_RULING_CONSUMES_EDIT_RECEIPT_INVALID")
        # a receipt made under one ruling does not carry over to another (its ruling_digest no longer matches)
        other, _ = self.repinned(root, head, files, lambda b: b.__setitem__("ruled_by", "Coordination (other)"))
        self.refused(ar.check_change(other, root, pin, head, [good]), "ADJACENCY_RULING_CONSUMES_EDIT_RECEIPT_INVALID")
        # the owned (routed) path stays routed to its owner whatever receipt is supplied
        owned_root, opin, ohead, ofiles = self.pinned_fixture(edit_consumed=True)
        owned, _ = self.pinned_ruling(ohead, opin, ofiles)
        self.refused(ar.check_change(owned, owned_root, opin, ohead, [good]), "OWNER_OWNED_EDIT")

    def test_consumes_edit_cli_round_trip(self) -> None:
        root, pin, head, files = self.pinned_fixture(edit_consumed=True)
        body, _ = self.repinned(root, head, files)
        rpath, epath = root / "ruling.json", root / "edit.json"
        rpath.write_text(json.dumps(body), encoding="utf-8")
        self.assertEqual(ar.main(["consumes-edit", "--ruling", str(rpath), "--root", str(root), "--base", pin, "--head",
                                  head, "--path", "gate/gate_reader.py", "--writer-task", "SUBJ-001", "--out",
                                  str(epath)]), 0)
        self.assertEqual(ar.main(["check-change", "--ruling", str(rpath), "--root", str(root), "--base", pin, "--head",
                                  head, "--consumes-edit-receipt", str(epath)]), 0)
        self.assertEqual(ar.main(["check-change", "--ruling", str(rpath), "--root", str(root), "--base", pin, "--head",
                                  head]), 1)

    # -- (D) hashed pin data is data, not a closure edge, only when the ruling pins the same bytes ---------------
    def pin_data_repo(self, test):
        files = {"tests/test_fp.py": test, "pkg/__init__.py": "from . import danger\n", "pkg/danger.py": "D = 1\n",
                 "pkg/verifier.py": "X = 1\n", "pkg/other.py": "O = 1\n"}
        root, _ = self.fp(files)
        return root, hashlib.sha256((root / "pkg" / "verifier.py").read_bytes()).hexdigest()

    def test_hashed_pin_data_is_not_a_closure_edge(self) -> None:
        probe, digest = self.pin_data_repo("PIN = {}\n")
        test = f"PIN = {{'commit': 'c', 'files': {{'pkg/verifier.py': '{digest}'}}}}\n"
        root, _ = self.pin_data_repo(test)
        notes = {}
        closure = ar.static_closure(root, "tests/test_fp.py", notes, {"pkg/verifier.py": digest})
        self.assertEqual(sorted(closure), ["tests/test_fp.py"])
        self.assertEqual(notes["hashed_pin_data_paths"], ["pkg/verifier.py"])
        # no verified pin, or a different sha256: the literal is followed as before (fail closed)
        self.assertIn("pkg/verifier.py", ar.static_closure(root, "tests/test_fp.py"))
        self.assertIn("pkg/verifier.py", ar.static_closure(root, "tests/test_fp.py", None, {"pkg/verifier.py": "0" * 64}))

    def test_hashed_pin_path_reached_another_way_is_still_followed(self) -> None:
        _probe, digest = self.pin_data_repo("PIN = {}\n")
        pin = f"PIN = {{'pkg/verifier.py': '{digest}'}}\n"
        cases = {
            "import": pin + "from pkg import verifier\n",
            "path chain": pin + "from pathlib import Path\nP = Path(__file__).parents[1] / 'pkg/verifier.py'\n",
            "load over the pin table": pin + "import runpy\nfrom pathlib import Path\nfor rel in PIN:\n"
                                       "    runpy.run_path(str(Path(__file__).parents[1] / rel))\n",
        }
        for name, test in cases.items():
            with self.subTest(name):
                root, _ = self.pin_data_repo(test)
                self.assertIn("pkg/verifier.py", ar.static_closure(root, "tests/test_fp.py", None, {"pkg/verifier.py": digest}))

    def test_finish_test_carrying_the_unowned_pin_keeps_the_stub_context(self) -> None:
        """Lane C's case: the finish test carries the (U) pin of a module it loads only under a stub-seeded package.
        As a path edge the pin literal would load it in context N and pull the package __init__ back in."""
        root, pin, head, files = self.pinned_fixture()
        verifier = "pkg/verifier.py"
        digest = hashlib.sha256(b"from .helper import H\n").hexdigest()
        extra = {"pkg/gate.py": self.ENSURE, "pkg/__init__.py": "from . import danger\n", "pkg/danger.py": "D = 1\n",
                 verifier: "from .helper import H\n", "pkg/helper.py": "H = 1\n", ".github/workflows/fp.yml": self.RUNNER}
        for rel, text in extra.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "gate")
        pin2 = git(root, "rev-parse", "HEAD")
        test = (f"UNOWNED_PIN = {{'commit': '{pin2}', 'files': {{'{verifier}': '{digest}'}}}}\n"
                + self.BY_PATH + "from gate import gate_reader\n")
        (root / "tests" / "test_fp.py").write_text(test, encoding="utf-8")
        git(root, "commit", "-qam", "carry the unowned pin")
        head2 = git(root, "rev-parse", "HEAD")
        body, req = self.unowned_ruling(head2, pin2, {verifier: digest})
        verdict = ar.verify(body, req, self.base, root)
        self.assertEqual(verdict["disposition"], "ALLOW", verdict)
        closure = verdict["finish_point"]["closure"]
        self.assertIn(verifier, closure)
        self.assertNotIn("pkg/__init__.py", closure)
        self.assertEqual(verdict["finish_point"]["hashed_pin_data_paths"], [verifier])
        row = next(r for r in verdict["consumed_pins"] if r["task_id"] == ar.UNOWNED)
        self.assertTrue(row["enforced_by_finish_test"])

    def test_pinned_and_routed_consumed_paths_allow_and_are_exempt_from_b(self) -> None:
        root, pin, head, files = self.pinned_fixture()
        body, req = self.pinned_ruling(head, pin, files)
        verdict = ar.verify(body, req, self.base, root)
        self.assertEqual(verdict["disposition"], "ALLOW", verdict)
        self.assertEqual(verdict["condition_pin"], "HELD")
        self.assertEqual(verdict["condition_routing"], "HELD")
        self.assertIn("gate/gate_reader.py", verdict["finish_point"]["closure"])
        self.assertEqual(verdict["candidates"][0]["pinned_consumed_paths"], ["gate/gate_reader.py", "gate/step.yml"])

    def test_what_a_pinned_file_loads_by_name_is_not_exempt(self) -> None:
        root, pin, head, files = self.pinned_fixture(gate_loads="gate.validator_inventory")
        body, req = self.pinned_ruling(head, pin, files)
        verdict = ar.verify(body, req, self.base, root)
        self.refused(verdict, "ADJACENCY_CONDITION_B_NOT_HELD")
        self.assertEqual(verdict["detail"], [{"path": "gate/validator_inventory.py", "reason": "MODULE_NAMES_CANDIDATE_COMPONENT",
                                              "component": "validator-inventory"}])

    def test_subject_edit_of_a_protected_path_fails_closed_owned_by_the_owner(self) -> None:
        root, pin, head, files = self.pinned_fixture(edit_consumed=True)
        body, req = self.pinned_ruling(head, pin, files)
        verdict = ar.verify(body, req, self.base, root)
        self.refused(verdict, "OWNER_OWNED_EDIT")
        self.assertEqual(verdict["owning_existing_goal"], "CAND-A-001")
        self.assertEqual(verdict["detail"]["modified"], ["gate/gate_reader.py"])
        change = ar.check_change(body, root, pin, head)
        self.refused(change, "OWNER_OWNED_EDIT")
        self.assertEqual(change["owning_existing_goal"], "CAND-A-001")

    def test_check_change_outside_protected_paths_allows(self) -> None:
        root, pin, head, files = self.pinned_fixture()
        body, _req = self.pinned_ruling(head, pin, files)
        change = ar.check_change(body, root, pin, head)
        self.assertEqual(change["disposition"], "ALLOW", change)
        self.refused(ar.check_change(body, root, "0" * 40, head), "ADJACENCY_RULING_CHANGE_UNREADABLE")

    def test_pin_digest_commit_and_finish_test_enforcement_fail_closed(self) -> None:
        root, pin, head, files = self.pinned_fixture()
        def bad_digest(b):
            b["consumes_dependencies"][0]["pinned_source"]["files"]["gate/step.yml"] = "0" * 64
        def bad_commit(b):
            b["consumes_dependencies"][0]["pinned_source"]["commit"] = "1" * 40
        for mutate, code in ((bad_digest, "ADJACENCY_RULING_CONSUMED_PIN_DIGEST_DIVERGES"),
                             (bad_commit, "ADJACENCY_RULING_CONSUMED_PIN_COMMIT_UNAVAILABLE")):
            body, req = self.pinned_ruling(head, pin, files, mutate)
            self.refused(ar.verify(body, req, self.base, root), code)
        root, pin, head, files = self.pinned_fixture(carry_pin=False)
        body, req = self.pinned_ruling(head, pin, files)
        self.refused(ar.verify(body, req, self.base, root), "ADJACENCY_RULING_FINISH_TEST_DOES_NOT_ENFORCE_PIN")

    def test_malformed_unrouted_and_unpinned_relied_paths_fail_closed(self) -> None:
        root, pin, head, files = self.pinned_fixture()
        def short_commit(b):
            b["consumes_dependencies"][0]["pinned_source"]["commit"] = pin[:12]
        def other_repo(b):
            b["consumes_dependencies"][0]["pinned_source"]["repository"] = "Org/other"
        def no_failure_code(b):
            del b["protected_paths"][0]["on_modification"]["failure_code"]
        def misrouted(b):
            b["protected_paths"][0]["on_modification"]["routed_to"] = "SOMEONE-ELSE"
        def partial_paths(b):
            b["protected_paths"][0]["paths"] = ["gate/step.yml"]
        def no_pin(b):
            b["consumes_dependencies"][0].pop("pinned_source")
            b["protected_paths"] = []
        def no_route(b):
            b["protected_paths"] = []
        cases = ((short_commit, "ADJACENCY_RULING_CONSUMED_PIN_MALFORMED"),
                 (other_repo, "ADJACENCY_RULING_CONSUMED_PIN_MALFORMED"),
                 (no_failure_code, "ADJACENCY_RULING_PROTECTED_PATHS_MALFORMED"),
                 (misrouted, "ADJACENCY_RULING_PROTECTED_PATHS_UNROUTED"),
                 (partial_paths, "ADJACENCY_RULING_PROTECTED_PATHS_UNROUTED"),
                 (no_pin, "ADJACENCY_RULING_RELIED_PATHS_UNPINNED"),
                 (no_route, "ADJACENCY_RULING_RELIED_PATHS_UNPINNED"))
        for mutate, code in cases:
            body, req = self.pinned_ruling(head, pin, files, mutate)
            with self.subTest(mutate.__name__):
                self.refused(ar.verify(body, req, self.base, root), code)

    # -- (a) recomputed ---------------------------------------------------------------------------------------
    def test_a_fails_on_a_shared_component_even_if_the_ruling_omits_it(self) -> None:
        cand = candidate(components=("task-registry", "consent-receipt"))
        self.put(cand)
        root, commit = self.fp()
        req = request()
        claimed = ruling(commit, req, [cand])
        self.refused(ar.verify(claimed, req, self.base, root), "ADJACENCY_CONDITION_A_NOT_HELD")
        lying = copy.deepcopy(claimed)
        lying["candidates"][0]["components"] = ["task-registry"]
        lying["evidence_digest"] = ar.ruling_digest(lying)
        self.refused(ar.verify(lying, req, self.base, root), "ADJACENCY_RULING_COMPONENTS_DIVERGE")

    def test_a_fails_on_shared_lineage(self) -> None:
        cand = candidate()
        cand["parent_task_id"] = "SUBJ-001"
        self.put(cand)
        root, commit = self.fp()
        req = request()
        self.refused(ar.verify(ruling(commit, req, [cand]), req, self.base, root), "ADJACENCY_CONDITION_A_NOT_HELD")

    def test_a_candidate_without_declared_components_is_not_vacuously_adjacent(self) -> None:
        cand = candidate(components=())
        self.put(cand)
        root, commit = self.fp()
        req = request()
        self.refused(ar.verify(ruling(commit, req, [cand]), req, self.base, root),
                     "ADJACENCY_RULING_CANDIDATE_COMPONENTS_UNDECLARED")

    # -- (c) --------------------------------------------------------------------------------------------------
    def test_c_fails_when_the_consumes_dependency_is_not_recorded(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp()
        req = request(deps=())
        self.refused(ar.verify(ruling(commit, req, [cand]), req, self.base, root), "ADJACENCY_CONDITION_C_NOT_HELD")

    # -- the ruling itself ------------------------------------------------------------------------------------
    def test_ruling_integrity_class_and_scope(self) -> None:
        cand = candidate()
        self.put(cand)
        root, commit = self.fp()
        req = request()
        good = ruling(commit, req, [cand])
        tampered = copy.deepcopy(good)
        tampered["ruled_by"] = "someone else"
        self.refused(ar.verify(tampered, req, self.base, root), "ADJACENCY_RULING_DIGEST_MISMATCH")
        dup = copy.deepcopy(good)
        dup["ruling"] = "DUPLICATE"
        dup["evidence_digest"] = ar.ruling_digest(dup)
        self.refused(ar.verify(dup, req, self.base, root), "ADJACENCY_RULING_NOT_CLASS_D_ADJACENT")
        self.refused(ar.verify({"schema": "x"}, req, self.base, root), "ADJACENCY_RULING_SCHEMA_INVALID")
        prose = request(test="Org/fp tests/test_fp.py and more, run somewhere")
        self.refused(ar.verify(ruling(commit, prose, [cand]), prose, self.base, root),
                     "ADJACENCY_RULING_FINISH_POINT_NOT_ADDRESSABLE")
        self.put(candidate("CAND-B-001", components=("other",)))
        self.refused(ar.verify(good, req, self.base, root, [{"task_id": "SUBJ-001", "head_disposition": "COORDINATE_CONVERGENCE",
                     "evidence": {"collision_candidate_ids": ["CAND-A-001", "CAND-B-001"]}}]),
                     "ADJACENCY_RULING_DOES_NOT_COVER_CHECKIN")
        self.refused(ar.verify(good, req, self.base, root, [{"task_id": "SUBJ-001", "head_disposition": "STOP_COLLISION",
                     "evidence": {"collision_candidate_ids": ["CAND-A-001"], "hard_collision_task_ids": ["CAND-A-001"]}}]),
                     "ADJACENCY_RULING_CANNOT_CLEAR_HARD_COLLISION")
        self.refused(ar.verify(good, req, self.base, root, [{"task_id": "OTHER-001", "head_disposition": "COORDINATE_CONVERGENCE",
                     "evidence": {"collision_candidate_ids": ["CAND-A-001"]}}]),
                     "ADJACENCY_RULING_DOES_NOT_COVER_CHECKIN")


class TransitionWithRulingTests(unittest.TestCase):
    """The real KV request through the real transition against this tree; the finish-point source is a local
    fixture repository at a pinned commit that mirrors the real test's import shape."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        request = json.loads(KV_REQUEST.read_text())
        request["observed_registry_generation"] = json.loads((ROOT / "data/canonical-task-registry.json").read_text())["generation"]
        self.current_request = Path(tmp.name) / "request.json"
        self.current_request.write_text(json.dumps(request))

    def fixture(self, vault_source: str) -> tuple[Path, Path]:
        root, commit = make_repo({
            "tests/test_kv_skap_vault_finish_point.py": "from runtime import kv_skap_vault as kv\n",
            "runtime/kv_skap_vault.py": vault_source,
            "runtime/secret_field_policy.py": "X = 1\n",
            "runtime/task_registry_event_sovereign_kv_binding.py": "Y = 1\n"})
        self.addCleanup(shutil.rmtree, root, True)
        rul = json.loads(KV_RULING.read_text(encoding="utf-8"))
        rul["subject"]["finish_point"]["source_commit"] = commit
        # The fixture's finish test never reaches the consumed provider adapter, so the real ruling's consumed-source
        # pin (a real continuity-vault-kit commit, absent from this fixture repository) and its routing are dropped.
        for dep in rul["consumes_dependencies"]:
            dep.pop("pinned_source", None)
        for cand in rul["candidates"]:
            cand["finish_point_paths"] = []
        rul.pop("protected_paths", None)
        rul["evidence_digest"] = ar.ruling_digest(rul)
        path = root.parent / f"{root.name}.ruling.json"
        path.write_text(json.dumps(rul), encoding="utf-8")
        self.addCleanup(path.unlink, True)
        return root, path

    def test_without_a_ruling_the_kv_plan_stays_coordinate_convergence(self) -> None:
        body = transition.run("plan", self.current_request, ROOT)
        self.assertEqual(body["disposition"], "FAIL_CLOSED")
        self.assertEqual(body["failure_code"], "REGISTRY_COLLISION_CHECKIN_NOT_CONTINUE")

    def test_a_recomputed_ruling_lets_the_kv_plan_continue(self) -> None:
        root, path = self.fixture("from runtime.secret_field_policy import X\n")
        body = transition.run("plan", self.current_request, ROOT, None, path, root)
        self.assertEqual(body["disposition"], "ALLOW", body)
        self.assertTrue(body["evidence"]["collision_checkin"].startswith("CONTINUE_BY_VERIFIED_ADJACENCY_RULING"))
        self.assertEqual(body["evidence"]["successor_registry_generation"], body["evidence"]["predecessor_registry_generation"] + 1)
        self.assertEqual(body["evidence"]["adjacency_ruling"]["disposition"], "ALLOW")

    def test_the_same_ruling_fails_closed_when_the_test_reaches_the_sovereign_binding(self) -> None:
        root, path = self.fixture("from runtime import task_registry_event_sovereign_kv_binding\n")
        body = transition.run("plan", self.current_request, ROOT, None, path, root)
        self.assertEqual(body["disposition"], "FAIL_CLOSED")
        self.assertEqual(body["failure_code"], "ADJACENCY_CONDITION_B_NOT_HELD")
        for field in SIX:
            self.assertTrue(body[field])

    def test_committed_kv_ruling_is_sealed_and_covers_the_checkin_candidates(self) -> None:
        rul = json.loads(KV_RULING.read_text(encoding="utf-8"))
        self.assertEqual(rul["evidence_digest"], ar.ruling_digest(rul))
        req = json.loads(KV_REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(rul["subject"]["finish_point"]["acceptance_test"],
                         req["sealed_scope"]["scope"]["finish_point"]["acceptance_test"])
        self.assertEqual({c["task_id"] for c in rul["candidates"]},
                         {"SS-KV-SKAP-SOCIAL-RELEASE-001", "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001",
                          "TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001"})


if __name__ == "__main__":
    unittest.main()
