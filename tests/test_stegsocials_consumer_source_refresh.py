from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = Path("scripts/consume_stegsocials_bounded_intr_admission_request.py")
BUILDER = Path("scripts/build_stegsocials_bounded_intr_materialization.py")
INPUT_MATERIALIZER = Path("scripts/materialize_stegsocials_bounded_intr_admission_input.py")


def load(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StegSocialsConsumerSourceRefreshTests(unittest.TestCase):
    def assert_socials_runtime_dependencies(self, module) -> None:
        self.assertIn(CONSUMER, module.STATIC_FILES)
        self.assertIn(BUILDER, module.STATIC_FILES)
        self.assertIn(INPUT_MATERIALIZER, module.STATIC_FILES)

    def test_current_refresh_materializes_registered_consumer_builder_and_input_materializer(self) -> None:
        module = load("socials_refresh", "scripts/refresh_sovereign_worker_runtime_source.py")
        self.assert_socials_runtime_dependencies(module)

    def test_base_refresh_cannot_regress_socials_runtime_dependencies(self) -> None:
        module = load("socials_refresh_base", "scripts/refresh_sovereign_worker_runtime_source_base.py")
        self.assert_socials_runtime_dependencies(module)


if __name__ == "__main__":
    unittest.main()
