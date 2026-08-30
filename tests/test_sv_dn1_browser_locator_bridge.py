from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


portable = load("svdn1_portable", ROOT / "scripts/refresh_and_dispatch_resident_requests.py")
adapter = load("svdn1_adapter", ROOT / "workers/sv_dn1_sdk_browser_evidence_adapter.py")


class SvDn1BrowserLocatorBridgeTests(unittest.TestCase):
    def test_portable_bridge_persists_local_only_locator_for_sv_dn1(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"
            runtime.mkdir()
            bundle = base / "bundle.json"
            bundle.write_text("{}\n", encoding="utf-8")
            safe = {
                "STEGVERSE_SV_DN1_BROWSER_OBSERVATION_BUNDLE": str(bundle),
            }
            self.assertTrue(portable.persist_sv_dn1_browser_locator(runtime, safe, "sv_dn1"))
            locator = json.loads((runtime / portable.SV_DN1_BROWSER_LOCATOR_REL).read_text(encoding="utf-8"))
            self.assertEqual(locator["schema"], "stegverse.sv-dn1.browser-observation-locator/v1")
            self.assertEqual(locator["state"], "AVAILABLE_LOCAL_ONLY")
            self.assertEqual(locator["bundle_path"], str(bundle.resolve()))
            self.assertFalse(locator["credential_material_included"])
            self.assertFalse(locator["network_fetch_performed"])
            self.assertEqual(locator["authority_effect"], "NONE_LOCAL_EVIDENCE_LOCATOR_ONLY")

    def test_non_sv_dn1_dispatch_does_not_persist_locator(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            runtime.mkdir()
            self.assertFalse(portable.persist_sv_dn1_browser_locator(runtime, {}, "hil"))
            self.assertFalse((runtime / portable.SV_DN1_BROWSER_LOCATOR_REL).exists())

    def test_missing_declared_bundle_fails_closed_before_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            runtime.mkdir()
            with self.assertRaisesRegex(RuntimeError, "browser observation bundle missing"):
                portable.persist_sv_dn1_browser_locator(
                    runtime,
                    {"STEGVERSE_SV_DN1_BROWSER_OBSERVATION_BUNDLE": str(Path(td) / "missing.json")},
                    "sv_dn1",
                )

    def test_adapter_discovers_locator_when_environment_was_stripped(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            (runtime / "control").mkdir(parents=True)
            bundle = Path(td) / "bundle.json"
            bundle.write_text("{}\n", encoding="utf-8")
            locator = {
                "schema": "stegverse.sv-dn1.browser-observation-locator/v1",
                "state": "AVAILABLE_LOCAL_ONLY",
                "bundle_path": str(bundle),
                "credential_material_included": False,
                "network_fetch_performed": False,
                "authority_effect": "NONE_LOCAL_EVIDENCE_LOCATOR_ONLY",
            }
            (runtime / adapter.LOCATOR_REL).write_text(json.dumps(locator) + "\n", encoding="utf-8")
            with mock.patch.object(adapter, "ROOT", runtime), mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual(adapter.resolve_bundle_path(), bundle.resolve())

    def test_adapter_rejects_locator_that_claims_network_fetch(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            (runtime / "control").mkdir(parents=True)
            bundle = Path(td) / "bundle.json"
            bundle.write_text("{}\n", encoding="utf-8")
            locator = {
                "schema": "stegverse.sv-dn1.browser-observation-locator/v1",
                "state": "AVAILABLE_LOCAL_ONLY",
                "bundle_path": str(bundle),
                "credential_material_included": False,
                "network_fetch_performed": True,
                "authority_effect": "NONE_LOCAL_EVIDENCE_LOCATOR_ONLY",
            }
            (runtime / adapter.LOCATOR_REL).write_text(json.dumps(locator) + "\n", encoding="utf-8")
            with mock.patch.object(adapter, "ROOT", runtime), mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(RuntimeError, "network_fetch_performed mismatch"):
                    adapter.resolve_bundle_path()


if __name__ == "__main__":
    unittest.main()
