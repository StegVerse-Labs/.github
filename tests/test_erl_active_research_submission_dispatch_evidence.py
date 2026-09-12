from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    path = ROOT / "control/resident-execution-request.d/consume-erl-active-research-intr-submission.py"
    spec = importlib.util.spec_from_file_location("erl_submission_dispatch_evidence", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ERLSubmissionDispatchEvidenceTests(unittest.TestCase):
    def test_materialization_records_exact_roots_and_digests(self):
        mod = load()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            for index, rel in enumerate(mod.SOURCE_DEPENDENCIES):
                path = source / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"source-{index}\n", encoding="utf-8")
            evidence = mod.materialize_source_dependencies(source, runtime)
            self.assertEqual(evidence["source_root"], str(source.resolve()))
            self.assertEqual(evidence["runtime_root"], str(runtime.resolve()))
            self.assertEqual(set(evidence["digests"]), {p.as_posix() for p in mod.SOURCE_DEPENDENCIES})
            for rel in mod.SOURCE_DEPENDENCIES:
                expected = "sha256:" + mod.file_sha256(source / rel)
                self.assertEqual(evidence["digests"][rel.as_posix()], expected)
                self.assertEqual(mod.file_sha256(runtime / rel), mod.file_sha256(source / rel))

    def test_persist_writes_exact_dispatch_receipt_and_readback(self):
        mod = load()
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            value = {
                "schema": "stegverse.erl-active-research-intr-submission-dispatch/v1",
                "state": "INGRESS_NOT_MATERIALIZED",
                "runtime_execution_attempted": False,
                "transport_submission_attempted": False,
                "provider_operation_attempted": False,
                "authority_effect": "NONE_WAIT_STATE",
            }
            result = mod.persist(runtime, value)
            self.assertEqual(result, value)
            path = runtime / mod.RECEIPT_REL
            self.assertTrue(path.is_file())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), value)

    def test_persist_replaces_latest_atomically_without_claiming_runtime(self):
        mod = load()
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            first = {"state": "INGRESS_NOT_MATERIALIZED", "runtime_execution_attempted": False}
            second = {"state": "PROFILE_ADMITTED_TERMINAL_MATERIALIZATION_PENDING", "runtime_execution_attempted": True}
            mod.persist(runtime, first)
            mod.persist(runtime, second)
            path = runtime / mod.RECEIPT_REL
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), second)


if __name__ == "__main__":
    unittest.main()
