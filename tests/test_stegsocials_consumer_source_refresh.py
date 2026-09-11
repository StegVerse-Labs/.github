from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TARGET = Path("scripts/consume_stegsocials_bounded_intr_admission_request.py")


def load(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StegSocialsConsumerSourceRefreshTests(unittest.TestCase):
    def test_current_refresh_materializes_registered_consumer(self) -> None:
        module = load("socials_refresh", "scripts/refresh_sovereign_worker_runtime_source.py")
        self.assertIn(TARGET, module.STATIC_FILES)

    def test_base_refresh_cannot_regress_registered_consumer(self) -> None:
        module = load("socials_refresh_base", "scripts/refresh_sovereign_worker_runtime_source_base.py")
        self.assertIn(TARGET, module.STATIC_FILES)


if __name__ == "__main__":
    unittest.main()
