from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

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
        "model_hash": "model-hash",
        "authority_effect": "NONE",
    }
    route = {
        "state": "ROUTE_ADMITTED",
        "route_authority": "StegVerse-Labs/TVC",
        "endpoint": "http://127.0.0.1:31415",
        "runtime_proof_hash": mod.stable_hash(proof),
        "receipt_hash": "route-hash",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "execution_authority": False,
        "authority_effect": "NONE",
    }
    execution = {
        "schema": "stegverse.llm_adapter.canonical_sovereign_route_execution/v1",
        "state": "EXECUTED",
        "session_id": "session-1",
        "transition_id": "transition-1",
        "measurement_id": "measurement-1",
        "request_hash": "request-hash",
        "response_hash": "response-hash",
        "model_id": "stegverse-reference-lm-v1",
        "model_hash": "model-hash",
        "provider_usage_event": {"event_sha256": "usage-hash"},
    }
    return proof, route, execution


def valid_receipt(proof: dict, route: dict, execution: dict) -> dict:
    receipt = {
        "schema": "stegverse.master_records.ecosystem_chat_sovereign_reconstruction/v1",
        "task_id": "MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024",
        "state": "PASS",
        "session_id": execution["session_id"],
        "transition_id": execution["transition_id"],
        "measurement_id": execution["measurement_id"],
        "runtime_proof_hash": mod.stable_hash(proof),
        "tvc_route_receipt_hash": route["receipt_hash"],
        "provider_usage_event_sha256": execution["provider_usage_event"]["event_sha256"],
        "request_hash": execution["request_hash"],
        "response_hash": execution["response_hash"],
        "model_id": execution["model_id"],
        "model_hash": execution["model_hash"],
        "route_authority": "StegVerse-Labs/TVC",
        "credential_authority": "StegVerse-Labs/TV+TVC",
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
    def test_discovers_only_complete_local_master_records_capsule(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "orchestration"
            for relative in (
                "scripts/reconstruct_ecosystem_chat_sovereign_execution.py",
                "tasks/MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024.json",
                "ECOSYSTEM_CHAT_SOVEREIGN_RECONSTRUCTION_MIRROR_HANDOFF.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("present\n", encoding="utf-8")
            old = os.environ.get("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT")
            os.environ["STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT"] = str(root)
            try:
                self.assertEqual(mod.find_master_records_root(ROOT), root.resolve())
            finally:
                if old is None:
                    os.environ.pop("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", None)
                else:
                    os.environ["STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT"] = old

    def test_child_environment_strips_github_and_master_records_credentials(self) -> None:
        old = {name: os.environ.get(name) for name in mod.AUTH_ENV}
        try:
            for name in mod.AUTH_ENV:
                os.environ[name] = "must-not-cross-boundary"
            env = mod.credential_free_child_env(Path("/tmp/master-records"))
            for name in mod.AUTH_ENV:
                self.assertNotIn(name, env)
            self.assertEqual(env["STEGVERSE_LOCAL_MODEL_CREDENTIAL_REQUIREMENT"], "NONE")
            self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "StegVerse-Labs/TV+TVC")
            self.assertEqual(env["STEGVERSE_MASTER_RECORDS_RECONSTRUCTION_MODE"], "CREDENTIAL_FREE_LOCAL")
        finally:
            for name, value in old.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    def test_receipt_verifier_binds_exact_same_execution(self) -> None:
        proof, route, execution = fixtures()
        receipt = valid_receipt(proof, route, execution)
        self.assertTrue(mod.reconstruction_receipt_verified(receipt, proof=proof, route=route, execution=execution))
        receipt["transition_id"] = "different"
        receipt["reconstruction_receipt_hash"] = mod.hash_without(receipt, "reconstruction_receipt_hash")
        self.assertFalse(mod.reconstruction_receipt_verified(receipt, proof=proof, route=route, execution=execution))

    def test_executes_local_verifier_without_forwarding_credentials(self) -> None:
        proof, route, execution = fixtures()
        with tempfile.TemporaryDirectory() as temp:
            master_records = Path(temp) / "orchestration"
            script = master_records / "scripts" / "reconstruct_ecosystem_chat_sovereign_execution.py"
            script.parent.mkdir(parents=True, exist_ok=True)
            for relative in (
                "tasks/MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024.json",
                "ECOSYSTEM_CHAT_SOVEREIGN_RECONSTRUCTION_MIRROR_HANDOFF.md",
            ):
                path = master_records / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("present\n", encoding="utf-8")
            script.write_text(
                "import argparse,hashlib,json,os\n"
                "p=argparse.ArgumentParser(); p.add_argument('--packet',required=True); p.add_argument('--output',required=True); a=p.parse_args()\n"
                "for k in ('GITHUB_TOKEN','GH_TOKEN','GITHUB_PAT','GITHUB_PERSONAL_ACCESS_TOKEN','ACTIONS_RUNTIME_TOKEN','ACTIONS_ID_TOKEN_REQUEST_TOKEN','MASTER_RECORDS_AUTH_TOKEN','MASTER_RECORDS_RECEIPT_KEY','STEGVERSE_MASTER_RECORDS_TOKEN'): assert not os.getenv(k)\n"
                "packet=json.load(open(a.packet)); proof=packet['runtime_proof']; route=packet['tvc_route_receipt']; execution=packet['llm_adapter_execution_receipt']\n"
                "h=lambda v: hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()\n"
                "r={'schema':'stegverse.master_records.ecosystem_chat_sovereign_reconstruction/v1','task_id':'MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024','state':'PASS','session_id':execution['session_id'],'transition_id':execution['transition_id'],'measurement_id':execution['measurement_id'],'runtime_proof_hash':h(proof),'tvc_route_receipt_hash':route['receipt_hash'],'provider_usage_event_sha256':execution['provider_usage_event']['event_sha256'],'request_hash':execution['request_hash'],'response_hash':execution['response_hash'],'model_id':execution['model_id'],'model_hash':execution['model_hash'],'route_authority':'StegVerse-Labs/TVC','credential_authority':'StegVerse-Labs/TV+TVC','credential_requirement':'NONE','github_token_required':False,'third_party_execution_platform_required':False,'provider_usage_reconstruction_pass':True,'transition_reconstruction_pass':True,'same_execution':True,'execution_authority':False,'admissibility_determined':False,'authority_effect':'NONE','next_transition':'ECOSYSTEM_CHAT_ZERO_BLOCKER_ACTIVATION_VERIFICATION'}\n"
                "r['reconstruction_receipt_hash']=h(r); open(a.output,'w').write(json.dumps(r)); print(json.dumps(r))\n",
                encoding="utf-8",
            )
            packet_path = Path(temp) / "packet.json"
            output_path = Path(temp) / "receipt.json"
            old = {name: os.environ.get(name) for name in mod.AUTH_ENV}
            try:
                for name in mod.AUTH_ENV:
                    os.environ[name] = "must-not-cross-boundary"
                result = mod.execute_reconstruction(
                    master_records,
                    proof=proof,
                    route=route,
                    execution=execution,
                    packet_path=packet_path,
                    output_path=output_path,
                )
            finally:
                for name, value in old.items():
                    if value is None:
                        os.environ.pop(name, None)
                    else:
                        os.environ[name] = value
            self.assertEqual(result["state"], "COMPLETE")
            self.assertFalse(result["github_auth_env_forwarded"])
            self.assertFalse(result["master_records_bearer_auth_forwarded"])
            self.assertEqual(result["credential_requirement"], "NONE")


if __name__ == "__main__":
    unittest.main()
