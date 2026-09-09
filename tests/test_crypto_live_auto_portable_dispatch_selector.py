#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFRESH_DISPATCH = ROOT / "scripts" / "refresh_and_dispatch_resident_requests.py"
DISPATCHER = ROOT / "scripts" / "dispatch_resident_execution_requests.py"


def load_refresh_dispatch():
    spec = importlib.util.spec_from_file_location("refresh_dispatch_crypto_selector", REFRESH_DISPATCH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CryptoLiveAutoPortableDispatchSelectorTests(unittest.TestCase):
    def test_portable_refresh_dispatch_admits_canonical_work_consumer(self):
        mod = load_refresh_dispatch()
        self.assertIn("canonical_work_coordination", mod.ALLOWED_TARGET_CONSUMERS)

    def test_generic_dispatcher_registers_same_selector(self):
        text = DISPATCHER.read_text(encoding="utf-8")
        self.assertIn('(\"canonical_work_coordination\", \"control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py\")', text)


if __name__ == "__main__":
    unittest.main()
