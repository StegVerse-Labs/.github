from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from workers.hil_sovereign_receiver_bridge import (
    PRIMARY_SHA256,
    PROMPT_SHA256,
    credential_free_receiver_env,
    find_hil_receiver_root,
    receiver_command,
    verify_receiver,
)


class HILSovereignReceiverBridgeTests(unittest.TestCase):
    def test_finds_only_complete_hil_receiver_tree(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adapter = root / "workloads" / "LLM-adapter"
            for relative in (
                "llm_adapter/combined_gateway.py",
                "llm_adapter/hil_intake_v1_1_api.py",
                "llm_adapter/hil_sovereign_receiver_profile.py",
                "tasks/LLMA-HIL-SOVEREIGN-RECEIVER-021.json",
                "docs/HIL_RUNTIME_MIRROR_HANDOFF.md",
            ):
                path = adapter / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("ok\n", encoding="utf-8")
            self.assertEqual(find_hil_receiver_root(root, {}), adapter.resolve())

    def test_receiver_environment_is_sovereign_durable_and_credential_free(self) -> None:
        env = {
            "GITHUB_TOKEN": "must-not-forward",
            "GH_TOKEN": "must-not-forward",
            "HOME": "/home/test",
        }
        child = credential_free_receiver_env(
            Path("/opt/stegverse/LLM-adapter"),
            Path("/var/lib/stegverse/hil-carrier"),
            env,
        )
        self.assertNotIn("GITHUB_TOKEN", child)
        self.assertNotIn("GH_TOKEN", child)
        self.assertEqual(child["STEGVERSE_RUNTIME_PROFILE"], "sovereign-carrier")
        self.assertEqual(child["STEGVERSE_SOVEREIGN_STATE_DURABLE"], "true")
        self.assertEqual(child["STEGVERSE_SOVEREIGN_STATE_DIR"], "/var/lib/stegverse/hil-carrier")
        self.assertEqual(child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")
        self.assertEqual(
            child["STEGVERSE_ALLOWED_ORIGINS"],
            "https://stegverse.org,https://www.stegverse.org",
        )

    def test_receiver_environment_rejects_hosted_and_temporary_roots(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "third_party_host"):
            credential_free_receiver_env(
                Path("/opt/stegverse/LLM-adapter"),
                Path("/var/lib/stegverse/hil"),
                {"GITHUB_ACTIONS": "true"},
            )
        with self.assertRaisesRegex(RuntimeError, "must_not_be_temporary"):
            credential_free_receiver_env(
                Path("/opt/stegverse/LLM-adapter"),
                Path("/tmp/hil"),
                {},
            )

    def test_receiver_command_is_loopback_only(self) -> None:
        command = receiver_command(8765)
        self.assertIn("127.0.0.1", command)
        self.assertNotIn("0.0.0.0", command)
        self.assertEqual(command[-1], "8765")

    @patch("workers.hil_sovereign_receiver_bridge._get_json")
    def test_verifies_exact_hil_profile_and_readiness_without_granting_authority(self, get_json) -> None:
        get_json.side_effect = [
            {
                "state": "ACTIVE_SOVEREIGN_RECEIVER",
                "credential_authority": "TV/TVC",
                "participant_machine_required": False,
                "developer_machine_required": False,
                "github_hosted_runtime_required": False,
                "third_party_runtime_required": False,
                "authority_granted": False,
            },
            {
                "state": "READY",
                "primary_sha256": PRIMARY_SHA256,
                "prompt_sha256": PROMPT_SHA256,
                "execution_authority": False,
                "publication_authority": False,
                "master_record_append_authority": False,
            },
        ]
        result = verify_receiver("http://127.0.0.1:8765")
        self.assertEqual(result["state"], "READY")
        self.assertTrue(result["profile_verified"])
        self.assertTrue(result["readiness_verified"])
        self.assertEqual(result["github_token_runtime_authority"], "NONE")
        self.assertFalse(result["public_https_rendezvous_proven"])
        self.assertFalse(result["browser_submission_proven"])
        self.assertFalse(result["post_restart_exact_byte_proven"])
        self.assertFalse(result["tvc_lifecycle_handoff_proven"])
        self.assertEqual(result["authority_effect"], "NONE")

    @patch("workers.hil_sovereign_receiver_bridge._get_json")
    def test_mismatch_fails_closed(self, get_json) -> None:
        get_json.side_effect = [
            {
                "state": "ACTIVE_SOVEREIGN_RECEIVER",
                "credential_authority": "TV/TVC",
                "participant_machine_required": False,
                "developer_machine_required": False,
                "github_hosted_runtime_required": False,
                "third_party_runtime_required": False,
                "authority_granted": False,
            },
            {
                "state": "READY",
                "primary_sha256": "wrong",
                "prompt_sha256": PROMPT_SHA256,
                "execution_authority": False,
                "publication_authority": False,
                "master_record_append_authority": False,
            },
        ]
        result = verify_receiver("http://127.0.0.1:8765")
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertFalse(result["readiness_verified"])


if __name__ == "__main__":
    unittest.main()
