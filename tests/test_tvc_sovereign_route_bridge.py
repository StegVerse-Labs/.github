from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "tvc_sovereign_route_bridge",
    ROOT / "workers" / "tvc_sovereign_route_bridge.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def proof() -> dict:
    return {
        "schema": "stegverse.sovereign-local-model-proof/v1",
        "state": "VERIFIED_REFERENCE_MODEL_RUNTIME",
        "model_id": "stegverse-reference-lm-v1",
        "authority_effect": "NONE",
        "qualifies_as_large_production_llm": False,
        "predicates": {
            "real_model_process_observed": True,
            "real_inference_response_observed": True,
            "third_party_inference_required": False,
            "model_output_grants_authority": False,
        },
        "selection": {"selected": {"engine": "stegverse-reference"}},
    }


class TVCSovereignRouteBridgeTests(unittest.TestCase):
    def test_finds_only_materialized_tvc_control_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            tvc = Path(temp)
            for relative in (
                "scripts/evaluate_sovereign_local_model_route.py",
                "tvc_sovereign_local_model_route.py",
                "tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json",
            ):
                path = tvc / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("present\n", encoding="utf-8")
            old = os.environ.get("STEGVERSE_TVC_ROOT")
            os.environ["STEGVERSE_TVC_ROOT"] = str(tvc)
            try:
                self.assertEqual(mod.find_tvc_root(ROOT), tvc.resolve())
            finally:
                if old is None:
                    os.environ.pop("STEGVERSE_TVC_ROOT", None)
                else:
                    os.environ["STEGVERSE_TVC_ROOT"] = old

    def test_verified_receipt_requires_exact_proof_endpoint_and_no_credentials(self) -> None:
        runtime_proof = proof()
        endpoint = "http://127.0.0.1:31415"
        receipt = {
            "state": "ROUTE_ADMITTED",
            "route_authority": "StegVerse-Labs/TVC",
            "endpoint": endpoint,
            "runtime_proof_hash": mod.stable_hash(runtime_proof),
            "credential_requirement": "NONE",
            "github_token_required": False,
            "third_party_execution_platform_required": False,
            "execution_authority": False,
            "authority_effect": "NONE",
            "canonical_micro_node_proof_consumed": True,
        }
        self.assertTrue(mod.route_receipt_verified(receipt, runtime_proof, endpoint))
        receipt["credential_requirement"] = "GITHUB_TOKEN"
        self.assertFalse(mod.route_receipt_verified(receipt, runtime_proof, endpoint))

    def test_executes_local_tvc_cli_and_preserves_authority_ceiling(self) -> None:
        runtime_proof = proof()
        endpoint = "http://127.0.0.1:31415"
        with tempfile.TemporaryDirectory() as temp:
            tvc = Path(temp) / "TVC"
            cli = tvc / "scripts" / "evaluate_sovereign_local_model_route.py"
            cli.parent.mkdir(parents=True, exist_ok=True)
            (tvc / "tasks").mkdir(parents=True, exist_ok=True)
            (tvc / "tvc_sovereign_local_model_route.py").write_text("present\n", encoding="utf-8")
            (tvc / "tasks" / "TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json").write_text("{}\n", encoding="utf-8")
            cli.write_text(
                "import argparse, hashlib, json\n"
                "p=argparse.ArgumentParser(); p.add_argument('--proof'); p.add_argument('--endpoint'); p.add_argument('--output'); a=p.parse_args()\n"
                "proof=json.load(open(a.proof)); h=hashlib.sha256(json.dumps(proof,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()\n"
                "r={'state':'ROUTE_ADMITTED','route_authority':'StegVerse-Labs/TVC','endpoint':a.endpoint,'runtime_proof_hash':h,'credential_requirement':'NONE','github_token_required':False,'third_party_execution_platform_required':False,'execution_authority':False,'authority_effect':'NONE','canonical_micro_node_proof_consumed':True}\n"
                "open(a.output,'w').write(json.dumps(r)); print(json.dumps(r))\n",
                encoding="utf-8",
            )
            proof_path = Path(temp) / "proof.json"
            output_path = Path(temp) / "route.json"
            proof_path.write_text(json.dumps(runtime_proof), encoding="utf-8")
            result = mod.evaluate_route(tvc, proof_path=proof_path, proof=runtime_proof, endpoint=endpoint, output_path=output_path)
            self.assertEqual(result["state"], "COMPLETE")
            self.assertFalse(result["github_token_required"])
            self.assertFalse(result["execution_authority"])
            self.assertEqual(result["credential_requirement"], "NONE")


if __name__ == "__main__":
    unittest.main()
