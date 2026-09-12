from __future__ import annotations

import unittest

from scripts import install_erl_device_kv_prior_lineage as installer


class InstallerTests(unittest.TestCase):
    def test_transform_installs_terminal_identity_path_and_is_idempotent(self):
        source = '''def event_materialization_basis():\n    request = {}\n    ingress = {}\n    source_ref = ingress.get("node_id") or ingress.get("interlock_id") or request.get("transport_intent_hash")\n    return {\n        "prior_receipt_hash":sha256_uri(ingress),\n        "queued_payload_hash":request.get("payload_hash"),\n    }\n\ndef main():\n    try:\n        connector = load_canonical_device_kv_connector(stegos_root)\n    except Exception:\n        pass\n    if parent_valid:\n        continuity_id = str(continuity["continuity_id"]); state_root = str(continuity["node_kv_state_root"])\n'''
        once = installer.transform(source)
        twice = installer.transform(once)
        self.assertEqual(once, twice)
        self.assertIn('request.get("prior_transport_receipt_hash") or sha256_uri(ingress)', once)
        self.assertIn('erl_upstream_receipt_hashes', once)
        self.assertIn('"materialization_request":request', once)
        self.assertIn('erl_terminal_mod = load_module', once)
        self.assertIn('ERL_DEVICE_KV_TERMINAL_REPAIR_REQUIRED', once)
        self.assertIn('erl_terminal_transport', once)

    def test_transform_fails_when_anchor_drifts(self):
        with self.assertRaises(SystemExit):
            installer.transform('def unrelated():\n    pass\n')


if __name__ == "__main__":
    unittest.main()
