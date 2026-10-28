"""B-P11 dependency reduction: workflows that need no pytest run under stdlib unittest.

The DeepSeek resident and SDK WorkSpace reseal workflows installed pytest only
to run a test module that needs nothing from it. They now run it with
``python -m unittest``. These tests pin that the workflows install nothing and
that unittest runs the same tests the module defines, all passing, so the
behaviour the pytest run checked is preserved. The KV AI memory workflow still
needs pytest (its tests use pytest fixtures); it no longer upgrades pip first,
and installs the pinned pytest==8.3.5 (StegVerse-Labs/.github#3183 V2a).

Non-authorizing: source validation only.
"""
from __future__ import annotations

import importlib
import inspect
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"

STDLIB_RUN = {
    "validate-deepseek-resident.yml": "tests.test_deepseek_intr_resident_bridge",
    "sdk-workspace-external-collab-reseal-resident-validation.yml":
        "tests.test_sdk_workspace_external_collab_client_secret_reseal_resident",
}


def defined_test_names(module) -> set[str]:
    names = {name for name, fn in vars(module).items()
             if name.startswith("test_") and inspect.isfunction(fn)}
    for _, cls in inspect.getmembers(module, inspect.isclass):
        if issubclass(cls, unittest.TestCase) and cls.__module__ == module.__name__:
            names |= {name for name in vars(cls) if name.startswith("test_")}
    return names


def suite_test_names(suite: unittest.TestSuite) -> set[str]:
    names = set()
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            names |= suite_test_names(test)
        elif isinstance(test, unittest.FunctionTestCase):
            names.add(test._testFunc.__name__)
        else:
            names.add(test._testMethodName)
    return names


class StdlibTestRunnerWorkflowTests(unittest.TestCase):
    def test_workflows_install_nothing_and_run_unittest(self):
        for workflow, module in STDLIB_RUN.items():
            with self.subTest(workflow=workflow):
                text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
                self.assertNotIn("pip install", text)
                self.assertNotIn("pytest", text)
                self.assertIn(f"-m unittest -v {module}", text)

    def test_unittest_runs_every_defined_test_and_all_pass(self):
        for module_name in STDLIB_RUN.values():
            with self.subTest(module=module_name):
                module = importlib.import_module(module_name)
                suite = unittest.defaultTestLoader.loadTestsFromModule(module)
                expected = defined_test_names(module)
                self.assertTrue(expected)
                self.assertEqual(suite_test_names(suite), expected)
                result = unittest.TestResult()
                suite.run(result)
                self.assertEqual(result.testsRun, len(expected))
                self.assertEqual(result.failures, [])
                self.assertEqual(result.errors, [])

    def test_kv_ai_memory_installs_only_pytest(self):
        text = (WORKFLOWS / "validate-kv-ai-memory-resident.yml").read_text(encoding="utf-8")
        self.assertNotIn("--upgrade pip", text)
        installs = [line.strip() for line in text.splitlines() if "pip install" in line]
        self.assertEqual(installs, ["- run: python -m pip install pytest==8.3.5"])


if __name__ == "__main__":
    unittest.main()
