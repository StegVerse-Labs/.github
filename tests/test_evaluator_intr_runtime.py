from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "serve_evaluator_intr_runtime",
    ROOT / "scripts/serve_evaluator_intr_runtime.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class EvaluatorReadReviewRuntimeTests(unittest.TestCase):
    def test_manifest_hash_is_canonical(self) -> None:
        one = mod._manifest_hash({"manifest": {"b": 2, "a": 1}})
        two = mod._manifest_hash({"manifest": {"a": 1, "b": 2}})
        self.assertEqual(one, two)
        self.assertEqual(len(one), 64)

    def test_projection_source_is_fixed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            site = Path(td)
            (site / "data/evaluator-review").mkdir(parents=True)
            (site / mod.DEFAULT_SOURCE).write_text("{}\n", encoding="utf-8")
            with self.assertRaises(mod.EvaluatorRuntimeError):
                mod._load_projection(site, "../secret.json")

    def test_projection_binding_rejects_version_mismatch(self) -> None:
        review = {
            "test": {"id": "t1", "version": 2},
            "manifest": {"request_id": "t1"},
        }
        request = {
            "bindings": {
                "test_id": "t1",
                "revision": 3,
                "manifest_hash": mod._manifest_hash(review),
            }
        }
        with self.assertRaises(mod.EvaluatorRuntimeError):
            mod._validate_projection_binding(request, review)

    def test_hosted_environment_is_rejected(self) -> None:
        prior = dict(mod.os.environ)
        try:
            mod.os.environ["GITHUB_ACTIONS"] = "true"
            with self.assertRaises(mod.EvaluatorRuntimeError):
                mod._reject_hosted_or_secret_env()
        finally:
            mod.os.environ.clear()
            mod.os.environ.update(prior)

    def test_write_once_is_idempotent_and_collision_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "r.json"
            mod._write_once(path, {"a": 1})
            mod._write_once(path, {"a": 1})
            with self.assertRaises(mod.EvaluatorRuntimeError):
                mod._write_once(path, {"a": 2})


if __name__ == "__main__":
    unittest.main()
