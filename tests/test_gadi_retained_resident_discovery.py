from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import observe_gadi_retained_resident_discovery as module


class GADIRetainedResidentDiscoveryTests(unittest.TestCase):
    def valid_discovery(self, node: str = "SV-NODE-0123456789abcdef01234567") -> dict:
        return {
            "schema": module.DISCOVERY_SCHEMA,
            "state": "AVAILABLE",
            "target_node_ref": node,
            "gateway_execution_authority": "NONE",
            "credential_authority": "TV/TVC",
            "discovery_grants_authority": False,
            "authority_effect": "NONE_DISCOVERY_ONLY",
        }

    def test_contract_validation_accepts_exact_non_authorizing_discovery(self) -> None:
        value = module._validate(self.valid_discovery())
        self.assertEqual(value["target_node_ref"], "SV-NODE-0123456789abcdef01234567")
        self.assertFalse(value["discovery_grants_authority"])

    def test_contract_validation_rejects_authority_drift(self) -> None:
        value = self.valid_discovery()
        value["discovery_grants_authority"] = True
        with self.assertRaisesRegex(ValueError, "may not grant authority"):
            module._validate(value)

    def test_contract_validation_rejects_noncanonical_node(self) -> None:
        value = self.valid_discovery("node-1")
        with self.assertRaisesRegex(ValueError, "node ref invalid"):
            module._validate(value)

    def test_observe_uses_only_local_existing_contract_and_writes_observation(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            raw = b'{"exact":"bytes"}'
            with patch.object(module, "_probe", return_value=("REACHABLE", raw, self.valid_discovery())) as probe:
                result = module.observe(runtime)
            self.assertEqual(result["state"], "CURRENT_RETAINED_RESIDENT_DISCOVERY_OBSERVED")
            self.assertEqual(result["target_node_ref"], "SV-NODE-0123456789abcdef01234567")
            self.assertFalse(result["hosted_fallback_used"])
            self.assertFalse(result["runtime_binding_granted"])
            self.assertFalse(result["execution_authority_granted"])
            self.assertEqual(probe.call_args.args[0], "http://127.0.0.1:8000")
            self.assertTrue((runtime / module.OUTPUT_REL).is_file())

    def test_unreachable_local_contract_fails_closed_without_hosted_fallback(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            with patch.object(module, "_probe", return_value=("UNAVAILABLE", None, None)) as probe:
                result = module.observe(runtime)
            self.assertEqual(result["state"], "RETAINED_RESIDENT_DISCOVERY_UNOBSERVED_FAIL_CLOSED")
            self.assertIsNone(result["target_node_ref"])
            self.assertFalse(result["hosted_fallback_used"])
            self.assertEqual(probe.call_count, 2)
            self.assertEqual(result["attempted_local_bases"], list(module.LOCAL_BASES))

    def test_observer_has_no_hosted_or_task_submission_surface(self) -> None:
        text = Path(module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("STEGVERSE_RESIDENT_RENDEZVOUS_URL", text)
        self.assertNotIn("RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003", text)
        self.assertNotIn("https://", text)
        self.assertIn("NONE_DISCOVERY_ONLY", text)


if __name__ == "__main__":
    unittest.main()
