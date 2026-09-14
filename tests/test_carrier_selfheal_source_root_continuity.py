from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
INSTALLER_SPEC = importlib.util.spec_from_file_location(
    "install_sovereign_heartbeat_service_source_continuity",
    ROOT / "scripts" / "install_sovereign_heartbeat_service.py",
)
assert INSTALLER_SPEC and INSTALLER_SPEC.loader
installer = importlib.util.module_from_spec(INSTALLER_SPEC)
INSTALLER_SPEC.loader.exec_module(installer)

CARRIER_SPEC = importlib.util.spec_from_file_location(
    "run_heartbeat_runtime_source_continuity",
    ROOT / "scripts" / "run_heartbeat_runtime.py",
)
assert CARRIER_SPEC and CARRIER_SPEC.loader
carrier = importlib.util.module_from_spec(CARRIER_SPEC)
CARRIER_SPEC.loader.exec_module(carrier)


def _materialize_with_recorded_source(runtime: Path, source: Path) -> None:
    installer.materialize(ROOT, runtime)
    receipt_path = runtime / carrier.MATERIALIZATION_RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["source_root"] = str(source.resolve())
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class CarrierSelfHealSourceRootContinuityTests(unittest.TestCase):
    def test_carrier_recovers_canonical_source_locator_for_worker_self_heal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = base / "heartbeat"
            source = base / "canonical-source"
            source.mkdir()
            _materialize_with_recorded_source(runtime, source)

            with mock.patch.dict(os.environ, {}, clear=True):
                recovered = carrier._restore_local_source_root(runtime)
                self.assertEqual(recovered, str(source.resolve()))
                self.assertEqual(
                    os.environ.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT"),
                    str(source.resolve()),
                )

    def test_existing_carrier_source_locator_remains_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = base / "heartbeat"
            receipt_source = base / "receipt-source"
            env_source = base / "service-source"
            receipt_source.mkdir()
            env_source.mkdir()
            _materialize_with_recorded_source(runtime, receipt_source)

            with mock.patch.dict(
                os.environ,
                {"STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(env_source)},
                clear=True,
            ):
                recovered = carrier._restore_local_source_root(runtime)
                self.assertEqual(recovered, str(env_source.resolve()))
                self.assertEqual(
                    os.environ.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT"),
                    str(env_source.resolve()),
                )


if __name__ == "__main__":
    unittest.main()
