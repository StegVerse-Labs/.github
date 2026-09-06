from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workers" / "sovereign_runtime_activation_worker.py"
spec = importlib.util.spec_from_file_location("g18_source_binding_worker", SCRIPT)
assert spec is not None and spec.loader is not None
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def prepare_source(root: Path) -> None:
    for rel in (
        "scripts/bootstrap_sovereign_runtime.py",
        "scripts/run_sovereign_ephemeral_console.py",
    ):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# test\n", encoding="utf-8")


def write_refresh_receipt(runtime: Path, source: Path, **overrides) -> None:
    body = {
        "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
        "source_root": str(source.resolve()),
        "runtime_root": str(runtime.resolve()),
        "network_fetch_performed": False,
        "credential_read_or_acquired": False,
        "authority_effect": "NONE_LOCAL_SOURCE_REFRESH",
    }
    body.update(overrides)
    path = runtime / "receipts/sovereign-host/worker-source-refresh.latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")


class G18LocalSourceBindingParityTests(unittest.TestCase):
    def test_resident_refresh_receipt_selects_distinct_canonical_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            runtime = base / "runtime"
            prepare_source(source)
            runtime.mkdir()
            write_refresh_receipt(runtime, source)

            resolved, mode, error = worker.resolve_canonical_source_root(runtime, env={})
            self.assertEqual(source.resolve(), resolved)
            self.assertEqual("RESIDENT_SOURCE_REFRESH_RECEIPT", mode)
            self.assertIsNone(error)

    def test_resident_refresh_receipt_rejects_source_equal_to_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            runtime.mkdir(parents=True)
            prepare_source(runtime)
            write_refresh_receipt(runtime, runtime)

            resolved, mode, error = worker.resolve_canonical_source_root(runtime, env={})
            self.assertIsNone(resolved)
            self.assertEqual("RESIDENT_SOURCE_REFRESH_RECEIPT", mode)
            self.assertEqual("CANONICAL_SOURCE_EQUALS_RESIDENT_RUNTIME", error)

    def test_refresh_receipt_and_explicit_binding_must_agree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            other = base / "other"
            runtime = base / "runtime"
            prepare_source(source)
            prepare_source(other)
            runtime.mkdir()
            write_refresh_receipt(runtime, source)

            resolved, mode, error = worker.resolve_canonical_source_root(
                runtime,
                env={"STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(other)},
            )
            self.assertIsNone(resolved)
            self.assertEqual("INVALID_REFRESH_RECEIPT", mode)
            self.assertEqual("SOURCE_BINDING_ENV_RECEIPT_MISMATCH", error)

    def test_refresh_receipt_rejects_network_or_authority_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            runtime = base / "runtime"
            prepare_source(source)
            runtime.mkdir()
            write_refresh_receipt(runtime, source, network_fetch_performed=True)

            resolved, mode, error = worker.resolve_canonical_source_root(runtime, env={})
            self.assertIsNone(resolved)
            self.assertEqual("INVALID_REFRESH_RECEIPT", mode)
            self.assertEqual("SOURCE_REFRESH_NETWORK_INVARIANT_INVALID", error)

    def test_direct_canonical_source_invocation_remains_supported_without_refresh_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            prepare_source(source)

            resolved, mode, error = worker.resolve_canonical_source_root(source, env={})
            self.assertEqual(source.resolve(), resolved)
            self.assertEqual("DIRECT_CANONICAL_SOURCE", mode)
            self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
