from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "hil_intr_profiled_ingress",
    ROOT / "workers/hil_intr_profiled_ingress.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class HILInTrProfiledIngressTests(unittest.TestCase):
    def test_profile_is_non_authorizing_and_exact(self) -> None:
        profile = mod.build_profile(tls_enabled=True)
        self.assertEqual(profile["schema"], "stegverse.hil-intr-materialization-ingress-profile/v1")
        self.assertEqual(profile["state"], "ACTIVE_SOVEREIGN_INTR_INGRESS")
        self.assertEqual(profile["protocol"], "InTr")
        self.assertEqual(profile["profile_path"], "/intr/profile")
        self.assertEqual(profile["materialization_path"], "/intr/materialization")
        self.assertEqual(profile["supported_origins"], ["STEGOS_NODE_OUTBOX", "TVC_RELAY_EGRESS"])
        self.assertEqual(profile["direct_node_credential_requirement"], "NONE")
        self.assertFalse(profile["direct_node_tvc_authorization_required"])
        self.assertTrue(profile["relay_tvc_authorization_required"])
        self.assertTrue(profile["event_triggered"])
        self.assertFalse(profile["always_on_receiver_required"])
        self.assertFalse(profile["second_user_device_required"])
        self.assertTrue(profile["exact_request_validation_required"])
        self.assertTrue(profile["write_once_queue_admission"])
        self.assertTrue(profile["tls_enabled"])
        self.assertFalse(profile["runtime_execution_attempted"])
        self.assertFalse(profile["hil_receiver_readiness_claimed"])
        self.assertFalse(profile["hil_custody_claimed"])
        self.assertFalse(profile["g18_required"])
        self.assertEqual(profile["credential_authority"], "TV/TVC")
        self.assertEqual(profile["github_token_runtime_authority"], "NONE")
        self.assertEqual(profile["execution_authority"], "NONE")
        self.assertEqual(profile["authority_effect"], "NONE_DISCOVERY_EVIDENCE_ONLY")

    def test_loopback_profile_cannot_be_misread_as_https_rendezvous(self) -> None:
        profile = mod.build_profile(tls_enabled=False)
        self.assertFalse(profile["tls_enabled"])
        self.assertEqual(profile["state"], "ACTIVE_SOVEREIGN_INTR_INGRESS")
        self.assertFalse(profile["runtime_execution_attempted"])

    def test_profile_wrapper_preserves_validated_post_handler(self) -> None:
        self.assertTrue(issubclass(mod.ProfiledIngressHandler, mod.ingress.IngressHandler))
        self.assertIs(mod.ProfiledIngressHandler.do_POST, mod.ingress.IngressHandler.do_POST)
        self.assertEqual(mod.ingress.INGRESS_PATH, "/intr/materialization")

    def test_profile_reads_do_not_claim_hil_receiver_readiness(self) -> None:
        profile = mod.build_profile(tls_enabled=True)
        forbidden_true = (
            "runtime_execution_attempted",
            "hil_receiver_readiness_claimed",
            "hil_custody_claimed",
            "g18_required",
        )
        for field in forbidden_true:
            self.assertIs(profile[field], False, field)


if __name__ == "__main__":
    unittest.main()
