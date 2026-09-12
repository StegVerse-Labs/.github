from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str, name: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def populate(source: Path, dependencies) -> None:
    for index, rel in enumerate(dependencies, start=1):
        path = source / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# canonical local dependency {index}: {rel.as_posix()}\n", encoding="utf-8")


class ERLLocalSourceSelfMaterializationTests(unittest.TestCase):
    def test_binding_consumer_materializes_exact_allowlist_and_repairs_drift(self):
        mod = load(
            "control/resident-execution-request.d/consume-erl-active-research-intr-runtime-binding.py",
            "erl_binding_local_source",
        )
        with tempfile.TemporaryDirectory() as src_td, tempfile.TemporaryDirectory() as rt_td:
            source = Path(src_td)
            runtime = Path(rt_td)
            populate(source, mod.SOURCE_DEPENDENCIES)
            first = mod.materialize_source_dependencies(source, runtime)
            self.assertEqual(set(first["copied"]), {p.as_posix() for p in mod.SOURCE_DEPENDENCIES})
            self.assertFalse(first["network_source_fetch_attempted"])
            target = runtime / mod.SOURCE_DEPENDENCIES[-1]
            target.write_text("# drift\n", encoding="utf-8")
            second = mod.materialize_source_dependencies(source, runtime)
            self.assertIn(mod.SOURCE_DEPENDENCIES[-1].as_posix(), second["copied"])
            self.assertEqual(target.read_bytes(), (source / mod.SOURCE_DEPENDENCIES[-1]).read_bytes())
            third = mod.materialize_source_dependencies(source, runtime)
            self.assertEqual(third["copied"], [])
            self.assertEqual(set(third["verified"]), {p.as_posix() for p in mod.SOURCE_DEPENDENCIES})

    def test_binding_consumer_fails_closed_when_allowlisted_source_dependency_missing(self):
        mod = load(
            "control/resident-execution-request.d/consume-erl-active-research-intr-runtime-binding.py",
            "erl_binding_local_source_missing",
        )
        with tempfile.TemporaryDirectory() as src_td, tempfile.TemporaryDirectory() as rt_td:
            source = Path(src_td)
            runtime = Path(rt_td)
            populate(source, mod.SOURCE_DEPENDENCIES[:-1])
            with self.assertRaisesRegex(RuntimeError, "canonical_local_source_dependency_missing"):
                mod.materialize_source_dependencies(source, runtime)

    def test_submission_consumer_is_independently_source_complete(self):
        mod = load(
            "control/resident-execution-request.d/consume-erl-active-research-intr-submission.py",
            "erl_submission_local_source",
        )
        with tempfile.TemporaryDirectory() as src_td, tempfile.TemporaryDirectory() as rt_td:
            source = Path(src_td)
            runtime = Path(rt_td)
            populate(source, mod.SOURCE_DEPENDENCIES)
            result = mod.materialize_source_dependencies(source, runtime)
            self.assertEqual(set(result["copied"]), {p.as_posix() for p in mod.SOURCE_DEPENDENCIES})
            self.assertFalse(result["network_source_fetch_attempted"])
            self.assertTrue((runtime / mod.SUBMITTER).is_file())
            self.assertTrue((runtime / mod.MATERIALIZER).is_file())
            self.assertTrue((runtime / mod.PREP).is_file())

    def test_prepare_runs_apply_then_check(self):
        binding = load(
            "control/resident-execution-request.d/consume-erl-active-research-intr-runtime-binding.py",
            "erl_binding_prepare_sequence",
        )
        calls = []

        class Result:
            returncode = 0
            stdout = "PASS\n"
            stderr = ""

        def runner(command, **kwargs):
            calls.append(command)
            return Result()

        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            ok, _ = binding.run_prep(runtime / binding.PREP, runtime, {}, runner=runner)
        self.assertTrue(ok)
        self.assertEqual(len(calls), 2)
        self.assertNotIn("--check", calls[0])
        self.assertEqual(calls[1][-1], "--check")


if __name__ == "__main__":
    unittest.main()
