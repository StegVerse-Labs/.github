import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "workers" / "sv_dn1_production_source_prep_current_identity_worker.py"


def load_wrapper():
    spec = importlib.util.spec_from_file_location("sv_dn1_current_identity_worker", WRAPPER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SvDn1CurrentSourceIdentityTests(unittest.TestCase):
    def test_evolved_current_marker_is_accepted_and_historical_hash_retained(self):
        module = load_wrapper()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            component_id = "stegverse.sdk"
            anchors = module.base.COMPONENTS[component_id]["anchors"]
            for rel in anchors:
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"current evolved source for {rel}\n", encoding="utf-8")

            observed = module.verify_current_source_markers(root, component_id)
            self.assertEqual(set(observed), set(anchors))
            self.assertTrue(all(row["role"] == "HISTORICAL_PROVENANCE_MARKER" for row in observed.values()))
            self.assertTrue(all(row["historical_blob_sha1"] == anchors[rel] for rel, row in observed.items()))
            self.assertTrue(any(row["historical_match"] is False for row in observed.values()))

    def test_missing_current_runtime_marker_fails_closed(self):
        module = load_wrapper()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(module.base.SourceIdentityDrift):
                module.verify_current_source_markers(root, "stegverse.sdk")

    def test_adapter_uses_current_identity_worker(self):
        import json
        adapter = json.loads((ROOT / "control/process-worker-adapters.d/sv-dn1-production-source-prep-001.json").read_text())
        command = adapter["adapters"][0]["command"]
        self.assertEqual(command, ["python", "workers/sv_dn1_production_source_prep_current_identity_worker.py"])

    def test_core_integrity_controls_remain_in_base_worker(self):
        module = load_wrapper()
        source = (ROOT / "workers/sv_dn1_production_source_prep_worker.py").read_text()
        self.assertIn("compute_source_manifest", source)
        self.assertIn("source_bundle_sha256", source)
        self.assertIn("credential-bearing environment forbidden", source)
        self.assertIn("hosted environments cannot execute sovereign production source preparation", source)
        self.assertIn("network_source_fetch_performed", source)
        self.assertEqual(module.base.PACKAGE_SCHEMA, "stegverse.source-package/v1")


if __name__ == "__main__":
    unittest.main()
