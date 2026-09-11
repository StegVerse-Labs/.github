from __future__ import annotations

import unittest

from scripts import install_erl_device_kv_prior_lineage as installer


class InstallerTests(unittest.TestCase):
    def test_transform_preserves_legacy_fallback_and_is_idempotent(self):
        source = '''def event_materialization_basis():\n    request = {}\n    ingress = {}\n    source_ref = ingress.get("node_id") or ingress.get("interlock_id") or request.get("transport_intent_hash")\n    return {\n        "prior_receipt_hash":sha256_uri(ingress),\n    }\n'''
        once = installer.transform(source)
        twice = installer.transform(once)
        self.assertEqual(once, twice)
        self.assertIn('request.get("prior_transport_receipt_hash") or sha256_uri(ingress)', once)
        self.assertIn('erl_upstream_receipt_hashes', once)
        self.assertIn('sha256_uri(ingress)', once)

    def test_transform_fails_when_anchor_drifts(self):
        with self.assertRaises(SystemExit):
            installer.transform('def unrelated():\n    pass\n')


if __name__ == "__main__":
    unittest.main()
