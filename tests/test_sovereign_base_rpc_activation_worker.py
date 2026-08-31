from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers.sovereign_base_rpc_activation_worker import (
    credential_free_command,
    credential_free_endpoint,
    proof_is_live,
    candidate_roots,
    find_micro_node_root,
)


class SovereignBaseRpcActivationWorkerTests(unittest.TestCase):
    def live_proof(self):
        methods = [
            "eth_chainId",
            "eth_blockNumber",
            "eth_getBalance",
            "eth_call",
            "eth_getCode",
            "eth_estimateGas",
            "eth_gasPrice",
        ]
        return {
            "schema": "stegverse.sovereign-base-rpc-proof/v1",
            "endpoint": "http://127.0.0.1:8545",
            "source": "operator-configured-private-runtime",
            "private_endpoint": True,
            "validation_only": False,
            "observed_chain_id": "0x2105",
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "github_token_required": False,
            "non_tv_tvc_secret_or_token_used": False,
            "render_required": False,
            "trade_authority": "NONE",
            "wallet_authority": "NONE",
            "passed": True,
            "method_proofs": [{"method": name, "passed": True, "detail": "ok"} for name in methods],
            "proof_hash": "sha256:test",
        }

    def test_live_private_base_proof_is_accepted(self):
        self.assertTrue(proof_is_live(self.live_proof()))

    def test_validation_reference_proof_is_rejected(self):
        proof = self.live_proof()
        proof["validation_only"] = True
        self.assertFalse(proof_is_live(proof))

    def test_wrong_chain_or_failed_method_is_rejected(self):
        proof = self.live_proof()
        proof["observed_chain_id"] = "0x1"
        self.assertFalse(proof_is_live(proof))
        proof = self.live_proof()
        proof["method_proofs"][3]["passed"] = False
        self.assertFalse(proof_is_live(proof))

    def test_endpoint_rejects_credentials_query_and_fragment(self):
        self.assertTrue(credential_free_endpoint("http://127.0.0.1:8545"))
        self.assertFalse(credential_free_endpoint("https://user:pass@node.local"))
        self.assertFalse(credential_free_endpoint("https://node.local/?api_key=value"))
        self.assertFalse(credential_free_endpoint("https://node.local/#secret"))

    def test_command_rejects_credential_like_arguments(self):
        self.assertTrue(credential_free_command("reth node --chain base --http --http.addr 127.0.0.1"))
        self.assertFalse(credential_free_command("reth node --auth-token abc"))
        self.assertFalse(credential_free_command("geth --api-key abc"))
        self.assertFalse(credential_free_command("client --rpc https://user:pass@node.local"))


    def test_portable_micro_node_locator_and_repo_map_are_discoverable(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            micro = base / "resident-control-plane" / "vendor" / "micro-node-runtime"
            (micro / "micro_node").mkdir(parents=True)
            (micro / "tools").mkdir(parents=True)
            (micro / "docs").mkdir(parents=True)
            (micro / "micro_node" / "base_rpc_runtime.py").write_text("# runtime\n")
            (micro / "tools" / "run_sovereign_base_rpc.py").write_text("# runner\n")
            (micro / "docs" / "SOVEREIGN_BASE_RPC_MIRROR_HANDOFF.md").write_text("# handoff\n")
            with mock.patch.dict(os.environ, {
                "STEGVERSE_MICRO_NODE_RUNTIME_ROOT": str(micro),
                "STEGVERSE_REPO_ROOTS_JSON": json.dumps({"StegVerse-002/micro-node-runtime": str(micro)}),
            }, clear=True):
                roots = candidate_roots()
                selected = find_micro_node_root()
            self.assertEqual(roots[0], micro.resolve())
            self.assertEqual(selected, micro.resolve())

    def test_legacy_micro_node_locator_remains_compatible(self):
        with tempfile.TemporaryDirectory() as td:
            micro = Path(td) / "micro-node-runtime"
            (micro / "micro_node").mkdir(parents=True)
            (micro / "tools").mkdir(parents=True)
            (micro / "docs").mkdir(parents=True)
            (micro / "micro_node" / "base_rpc_runtime.py").write_text("# runtime\n")
            (micro / "tools" / "run_sovereign_base_rpc.py").write_text("# runner\n")
            (micro / "docs" / "SOVEREIGN_BASE_RPC_MIRROR_HANDOFF.md").write_text("# handoff\n")
            with mock.patch.dict(os.environ, {"STEGVERSE_MICRO_NODE_ROOT": str(micro)}, clear=True):
                self.assertEqual(find_micro_node_root(), micro.resolve())


if __name__ == "__main__":
    unittest.main()
