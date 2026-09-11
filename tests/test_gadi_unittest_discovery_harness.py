from __future__ import annotations

import importlib.util
import inspect
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# These GADI regression modules intentionally remain directly runnable by pytest,
# but their free test functions are otherwise invisible to the repository-wide
# `python -m unittest discover -v tests` validation carrier.
PYTEST_STYLE_GADI_MODULES = (
    "tests/test_gadi_resident_execution_preflight.py",
    "tests/test_gadi_resident_preflight_dispatch.py",
    "tests/test_gadi_worker_adapter_preflight_gate.py",
    "tests/test_gadi_runtime_evidence_materializer.py",
    "tests/test_gadi_runtime_source_resolution.py",
    "tests/test_gadi_stegos_preflight_contract.py",
    "tests/test_gadi_stegos_command_contract.py",
)


def load_module(path: Path):
    name = f"gadi_unittest_bridge_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GADIUnittestDiscoveryHarnessTests(unittest.TestCase):
    def test_pytest_style_gadi_regressions_are_exercised_by_unittest_discovery(self) -> None:
        exercised = []
        for relative in PYTEST_STYLE_GADI_MODULES:
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            module = load_module(path)
            functions = [
                (name, function)
                for name, function in inspect.getmembers(module, inspect.isfunction)
                if name.startswith("test_") and function.__module__ == module.__name__
            ]
            self.assertTrue(functions, f"no free GADI tests found in {relative}")

            for name, function in functions:
                with self.subTest(module=relative, test=name):
                    parameters = list(inspect.signature(function).parameters)
                    if not parameters:
                        function()
                    elif parameters == ["tmp_path"]:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            function(Path(temp_dir))
                    else:
                        self.fail(
                            f"unsupported fixture signature for {relative}::{name}: {parameters}"
                        )
                    exercised.append(f"{relative}::{name}")

        self.assertGreaterEqual(len(exercised), 1)


if __name__ == "__main__":
    unittest.main()
