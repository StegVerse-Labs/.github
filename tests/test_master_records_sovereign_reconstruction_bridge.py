from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "master_records_sovereign_reconstruction_bridge",
    ROOT / "workers" / "master_records_sovereign_reconstruction_bridge.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def fixtures() -> tuple[dict, dict, dict]:
    proof = {
        "schema": "stegverse.sovereign-local-model-proof/v1",
        "state": "VERIFIED_REFERENCE_MODEL_RUNTIME",
        "model_id": "stegverse-reference-lm-v1",
        "model_hash": "model-1",
        "authority_effect": "NONE",
    }
    route = {
        "state": "ROUTE_ADMITTED",
        "endpoint": "http://127.0.0.1:31415",
        "route_authority": "StegVerse-Labs/TVC",
        "runtime_proof_hash": mod.stable_hash(proof),
    }
    route["receipt_hash"] = mod.stable_hash(route)
    execution = {
        "session_id": "session-1",
        "transition_id": "transition-1",
        "measurement_id": "measurement-1",
        "request_hash": "request-1",
        "response_hash": "response-1",
        "model_id": "stegverse-reference-lm-v1",
        "model_hash": "model-1",
        "provider_usage_event": {"event_sha256": "usage-1"},
    }
    return proof, route, execution


def pass_receipt(proof: dict, route: dict, execution: dict) -> dict:
    receipt = {
        "schema": "stegverse.master_records.ecosystem_chat_sovereign_reconstruction/v1",
        "task_id": "MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024",
        "state": "PASS",
        "runtime_proof_hash": mod.stable_hash(proof),
        "tvc_route_receipt_hash": route["receipt_hash"],
        "provider_usage_event_sha256": execution["provider_usage_event"]["event_sha256"],
        "session_id": execution["session_id"],
        "transition_id": execution["transition_id"],
        "measurement_id": execution["measurement_id"],
        "request_hash": execution["request_hash"],
        "response_hash": execution["response_hash"],
        "model_id": execution["model_id"],
        "model_hash": execution["model_hash"],
        "route_authority": "StegVerse-Labs/TVC",
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "provider_usage_reconstruction_pass": True,
        "transition_reconstruction_pass": True,
        "same_execution": True,
        "execution_authority": False,
        "admissibility_determined": False,
        "authority_effect": "NONE",
        "next_transition": "ECOSYSTEM_CHAT_ZERO_BLOCKER_ACTIVATION_VERIFICATION",
    }
    receipt["reconstruction_receipt_hash"] = mod.stable_hash(receipt)
    return receipt


class MasterRecordsSovereignReconstructionBridgeTests(unittest.TestCase):
    def test_discovers_only_materialized_reconstruction_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for relative in (
                "scripts/reconstruct_ecosystem_chat_sovereign_execution.py",
                "tasks/MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024.json",
                "ECOSYSTEM_CHAT_SOVEREIGN_RECONSTRUCTION_MIRROR_HANDOFF.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("present\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": str(root)}, clear=False):
                self.assertEqual(mod.find_master_records_root(ROOT), root.resolve())

    def test_child_environment_cannot_forward_github_credentials(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"GITHUB_TOKEN": "secret", "GH_TOKEN": "secret2", "PATH": "/usr/bin", "LANG": "C.UTF-8"},
            clear=True,
        ):
            env = mod.credential_free_child_env(Path("/tmp/master-records"))
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")

    def test_cached_receipt_binds_exact_proof_route_usage_and_self_hash(self) -> None:
        proof, route, execution = fixtures()
        receipt = pass_receipt(proof, route, execution)
        self.assertTrue(mod.reconstruction_receipt_verified(receipt, proof=proof, route=route, execution=execution))
        for field, replacement in (
            ("runtime_proof_hash", "other-proof"),
            ("tvc_route_receipt_hash", "other-route"),
            ("provider_usage_event_sha256", "other-usage"),
            ("reconstruction_receipt_hash", "other-self-hash"),
        ):
            tampered = dict(receipt)
            tampered[field] = replacement
            self.assertFalse(mod.reconstruction_receipt_verified(tampered, proof=proof, route=route, execution=execution), field)

    def test_receipt_requires_tv_tvc_and_exact_execution_identity(self) -> None:
        proof, route, execution = fixtures()
        receipt = pass_receipt(proof, route, execution)
        self.assertTrue(mod.reconstruction_receipt_verified(receipt, proof=proof, route=route, execution=execution))
        receipt["credential_authority"] = "TC/TVC"
        receipt["reconstruction_receipt_hash"] = mod.hash_without(receipt, "reconstruction_receipt_hash")
        self.assertFalse(mod.reconstruction_receipt_verified(receipt, proof=proof, route=route, execution=execution))

    def test_executes_locally_materialized_verifier_and_removes_packet(self) -> None:
        proof, route, execution = fixtures()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "mr"
            script = root / "scripts" / "reconstruct_ecosystem_chat_sovereign_execution.py"
            script.parent.mkdir(parents=True, exist_ok=True)
            (root / "tasks").mkdir(parents=True, exist_ok=True)
            (root / "tasks" / "MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024.json").write_text("{}\n", encoding="utf-8")
            (root / "ECOSYSTEM_CHAT_SOVEREIGN_RECONSTRUCTION_MIRROR_HANDOFF.md").write_text("handoff\n", encoding="utf-8")
            script.write_text(
                "import argparse,hashlib,json\n"
                "p=argparse.ArgumentParser();p.add_argument('--packet');p.add_argument('--output');a=p.parse_args()\n"
                "packet=json.load(open(a.packet));proof=packet['runtime_proof'];route=packet['tvc_route_receipt'];e=packet['llm_adapter_execution_receipt']\n"
                "h=lambda v: hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()\n"
                "r={'schema':'stegverse.master_records.ecosystem_chat_sovereign_reconstruction/v1','task_id':'MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024','state':'PASS','runtime_proof_hash':h(proof),'tvc_route_receipt_hash':route['receipt_hash'],'provider_usage_event_sha256':e['provider_usage_event']['event_sha256'],'session_id':e['session_id'],'transition_id':e['transition_id'],'measurement_id':e['measurement_id'],'request_hash':e['request_hash'],'response_hash':e['response_hash'],'model_id':e['model_id'],'model_hash':e['model_hash'],'route_authority':'StegVerse-Labs/TVC','credential_authority':'TV/TVC','credential_requirement':'NONE','github_token_required':False,'third_party_execution_platform_required':False,'provider_usage_reconstruction_pass':True,'transition_reconstruction_pass':True,'same_execution':True,'execution_authority':False,'admissibility_determined':False,'authority_effect':'NONE','next_transition':'ECOSYSTEM_CHAT_ZERO_BLOCKER_ACTIVATION_VERIFICATION'}\n"
                "r['reconstruction_receipt_hash']=h(r);open(a.output,'w').write(json.dumps(r));print(json.dumps(r))\n",
                encoding="utf-8",
            )
            out = Path(temp) / "receipts" / "reconstruction.json"
            result = mod.reconstruct_same_execution(root, proof=proof, route=route, execution=execution, output_path=out)
            self.assertEqual(result["state"], "COMPLETE")
            self.assertTrue(mod.reconstruction_receipt_verified(result["reconstruction_receipt"], proof=proof, route=route, execution=execution))
            self.assertEqual(list(out.parent.glob("mr-reconstruction-packet-*.json")), [])


if __name__ == "__main__":
    unittest.main()
