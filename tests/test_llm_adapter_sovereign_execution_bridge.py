from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "llm_adapter_sovereign_execution_bridge",
    ROOT / "workers" / "llm_adapter_sovereign_execution_bridge.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def proof() -> dict:
    return {
        "schema": "stegverse.sovereign-local-model-proof/v1",
        "state": "VERIFIED_REFERENCE_MODEL_RUNTIME",
        "model_id": "stegverse-reference-lm-v1",
        "model_hash": "model-hash",
        "authority_effect": "NONE",
    }


def route(runtime_proof: dict) -> dict:
    return {
        "state": "ROUTE_ADMITTED",
        "route_authority": "StegVerse-Labs/TVC",
        "endpoint": "http://127.0.0.1:31415",
        "runtime_proof_hash": mod.stable_hash(runtime_proof),
        "receipt_hash": "route-receipt-hash",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "execution_authority": False,
        "authority_effect": "NONE",
    }


class LLMAdapterSovereignExecutionBridgeTests(unittest.TestCase):
    def test_discovers_only_materialized_canonical_adapter_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            adapter = Path(temp)
            for relative in (
                "scripts/execute_canonical_sovereign_route.py",
                "llm_adapter/sovereign_local_model_binding.py",
                "llm_adapter/http_provider_clients.py",
                "tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json",
                "LLM_ADAPTER_MIRROR_HANDOFF.md",
            ):
                path = adapter / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("present\n", encoding="utf-8")
            old = os.environ.get("STEGVERSE_LLM_ADAPTER_ROOT")
            os.environ["STEGVERSE_LLM_ADAPTER_ROOT"] = str(adapter)
            try:
                self.assertEqual(mod.find_llm_adapter_root(ROOT), adapter.resolve())
            finally:
                if old is None:
                    os.environ.pop("STEGVERSE_LLM_ADAPTER_ROOT", None)
                else:
                    os.environ["STEGVERSE_LLM_ADAPTER_ROOT"] = old

    def test_child_environment_strips_all_github_auth_and_binds_tc_tvc(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            old = {name: os.environ.get(name) for name in mod.GITHUB_AUTH_ENV}
            try:
                for name in mod.GITHUB_AUTH_ENV:
                    os.environ[name] = "must-not-cross-boundary"
                env = mod.credential_free_child_env(Path(temp))
                for name in mod.GITHUB_AUTH_ENV:
                    self.assertNotIn(name, env)
                self.assertEqual(env["STEGVERSE_LOCAL_MODEL_CREDENTIAL_REQUIREMENT"], "NONE")
                self.assertEqual(env["STEGVERSE_TC_TVC_CREDENTIAL_AUTHORITY"], "TC/TVC")
                self.assertNotIn("STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY", env)
            finally:
                for name, value in old.items():
                    if value is None:
                        os.environ.pop(name, None)
                    else:
                        os.environ[name] = value

    def test_execution_receipt_requires_exact_route_and_proof_with_no_credentials(self) -> None:
        runtime_proof = proof()
        tvc_route = route(runtime_proof)
        receipt = {
            "schema": "stegverse.llm_adapter.canonical_sovereign_route_execution/v1",
            "state": "EXECUTED",
            "route_authority": "StegVerse-Labs/TVC",
            "route_receipt_hash": tvc_route["receipt_hash"],
            "runtime_proof_hash": mod.stable_hash(runtime_proof),
            "credential_requirement": "NONE",
            "github_token_required": False,
            "third_party_execution_platform_required": False,
            "execution_authority": False,
            "authority_effect": "NONE",
            "measured_usage": {"prompt_tokens": {"value": "3"}},
        }
        self.assertTrue(mod.execution_receipt_verified(receipt, proof=runtime_proof, route=tvc_route))
        receipt["github_token_required"] = True
        self.assertFalse(mod.execution_receipt_verified(receipt, proof=runtime_proof, route=tvc_route))

    def test_executes_local_adapter_cli_without_forwarding_github_auth(self) -> None:
        runtime_proof = proof()
        tvc_route = route(runtime_proof)
        with tempfile.TemporaryDirectory() as temp:
            adapter = Path(temp) / "LLM-adapter"
            script = adapter / "scripts" / "execute_canonical_sovereign_route.py"
            script.parent.mkdir(parents=True, exist_ok=True)
            for relative in (
                "llm_adapter/sovereign_local_model_binding.py",
                "llm_adapter/http_provider_clients.py",
                "tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json",
                "LLM_ADAPTER_MIRROR_HANDOFF.md",
            ):
                path = adapter / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("present\n", encoding="utf-8")
            script.write_text(
                "import argparse,json,os,hashlib\n"
                "p=argparse.ArgumentParser(); [p.add_argument(x, required=True) for x in ('--proof','--route','--session-id','--transition-id','--measurement-id','--output')]; a=p.parse_args()\n"
                "proof=json.load(open(a.proof)); route=json.load(open(a.route)); h=hashlib.sha256(json.dumps(proof,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()\n"
                "assert not any(os.getenv(k) for k in ('GITHUB_TOKEN','GH_TOKEN','GITHUB_PAT','GITHUB_PERSONAL_ACCESS_TOKEN','ACTIONS_RUNTIME_TOKEN','ACTIONS_ID_TOKEN_REQUEST_TOKEN'))\n"
                "assert os.getenv('STEGVERSE_LOCAL_MODEL_CREDENTIAL_REQUIREMENT') == 'NONE'\n"
                "assert os.getenv('STEGVERSE_TC_TVC_CREDENTIAL_AUTHORITY') == 'TC/TVC'\n"
                "r={'schema':'stegverse.llm_adapter.canonical_sovereign_route_execution/v1','state':'EXECUTED','route_authority':'StegVerse-Labs/TVC','route_receipt_hash':route['receipt_hash'],'runtime_proof_hash':h,'credential_requirement':'NONE','github_token_required':False,'third_party_execution_platform_required':False,'execution_authority':False,'authority_effect':'NONE','measured_usage':{'prompt_tokens':{'value':'3'}}}\n"
                "open(a.output,'w').write(json.dumps(r)); print(json.dumps(r))\n",
                encoding="utf-8",
            )
            proof_path = Path(temp) / "proof.json"
            route_path = Path(temp) / "route.json"
            output_path = Path(temp) / "execution.json"
            proof_path.write_text(json.dumps(runtime_proof), encoding="utf-8")
            route_path.write_text(json.dumps(tvc_route), encoding="utf-8")
            old = os.environ.get("GITHUB_TOKEN")
            os.environ["GITHUB_TOKEN"] = "must-not-cross-boundary"
            try:
                result = mod.execute_admitted_route(
                    adapter,
                    proof_path=proof_path,
                    route_path=route_path,
                    proof=runtime_proof,
                    route=tvc_route,
                    session_id="session",
                    transition_id="transition",
                    measurement_id="measurement",
                    output_path=output_path,
                )
            finally:
                if old is None:
                    os.environ.pop("GITHUB_TOKEN", None)
                else:
                    os.environ["GITHUB_TOKEN"] = old
            self.assertEqual(result["state"], "COMPLETE")
            self.assertFalse(result["github_token_required"])
            self.assertFalse(result["github_auth_env_forwarded"])
            self.assertEqual(result["credential_authority"], "TC/TVC")


if __name__ == "__main__":
    unittest.main()
