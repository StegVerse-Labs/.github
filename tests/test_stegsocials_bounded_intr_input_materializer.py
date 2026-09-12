from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MOD = load("socials_input_materializer", "scripts/materialize_stegsocials_bounded_intr_admission_input.py")


def received_record() -> dict:
    return {
        "schema": "stegverse.universal-work-interlock/v1",
        "work_id": "WORK-1",
        "correlation_id": "CORR-1",
        "direction": "INGRESS",
        "state": "RECEIVED",
        "source": {"type": "RUNTIME_EVENT", "identity": MOD.TASK_ID, "evidence_refs": []},
        "goal": "test",
        "organization": "StegVerse-Labs",
        "repository": "StegVerse-Labs/StegSocials",
        "component": "bounded-group-social-publication",
        "dependencies": [],
        "blockers": [],
        "convergence_refs": ["CONV-1"],
        "result_refs": [],
        "next_owner": "INTERLOCK_INTR",
        "human_action_required": False,
        "authority": {
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "heartbeat_granted_authority": False,
            "authority_effect": "NONE_RECEIVED_INGRESS_RECORD_ONLY",
            "interlock_self_grants_authority": False,
            "intr_self_grants_authority": False,
        },
        "recorded_at": "2026-09-12T00:00:00Z",
        "bounded_social_intent": {"task_id": MOD.TASK_ID},
        "admission_receipt_ref": None,
        "runtime_admission_observed": False,
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def authentic_env(runtime: Path, *, endpoint: str = "http://127.0.0.1:43119/intr/materialization", corrupt_hash: bool = False, transition_authority: bool = False) -> dict[str, str]:
    payload = runtime / "runtime-state/stegsocials/received.json"
    write_json(payload, received_record())
    raw = payload.read_bytes()
    common = {
        "binding_id": "BINDING-1",
        "route_receipt_hash": "a" * 64,
        "route_candidate_hash": "b" * 64,
        "route_id": "ROUTE-1",
        "transport_id": "INTR-1",
        "next_hop_transport_endpoint": endpoint,
        "next_hop_identity_binding": "NODE-LOCAL-INTR",
    }
    binding = {
        "schema": MOD.BINDING_SCHEMA,
        **common,
        "route_admitted": True,
        "egress_authorized": False,
        "runtime_executed": False,
        "credential_authority": "TV/TVC",
        "credential_material_present": False,
    }
    authorization = {
        "schema": MOD.AUTH_SCHEMA,
        "decision": "ALLOW_RELAY_EGRESS",
        "authorization_id": "RELAY-EGRESS-AUTH-1",
        "issuer_authority": "TV/TVC",
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "credential_material_present": False,
        "route_admitted": True,
        "egress_authorized": True,
        "runtime_executed": False,
        "payload_inspection_authority": False,
        "canonical_transition_authority": transition_authority,
        "settlement_authority": False,
        "authority_effect": "BOUNDED_RELAY_EGRESS_AUTHORIZATION",
        **common,
        "payload_sha256": "0" * 64 if corrupt_hash else hashlib.sha256(raw).hexdigest(),
        "payload_size": len(raw),
    }
    authorization["authorization_sha256"] = MOD.sha_hex(authorization)
    binding_path = runtime / "relay/binding.json"
    auth_path = runtime / "relay/authorization.json"
    write_json(binding_path, binding)
    write_json(auth_path, authorization)
    return {
        MOD.BINDING_ENV: str(binding_path),
        MOD.AUTH_ENV: str(auth_path),
        MOD.PAYLOAD_ENV: str(payload),
    }


class StegSocialsBoundedIntrInputMaterializerTests(unittest.TestCase):
    def test_missing_relay_artifacts_is_non_authorizing_wait_even_in_hosted_validation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            result = MOD.materialize(Path(td), env={"GITHUB_ACTIONS": "true"})
        self.assertEqual(result["state"], "AUTHENTIC_RELAY_INPUT_NOT_MATERIALIZED")
        self.assertFalse(result["input_materialized"])
        self.assertFalse(result["hosted_execution_attempted"])
        self.assertEqual(result["authority_effect"], "NONE_WAIT_STATE")

    def test_exact_relay_artifacts_materialize_hash_bound_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            result = MOD.materialize(runtime, env=authentic_env(runtime))
            pointer = json.loads((runtime / MOD.OUTPUT_REL).read_text(encoding="utf-8"))
        self.assertEqual(result["state"], "INPUT_MATERIALIZED")
        self.assertTrue(result["input_materialized"])
        self.assertFalse(result["tvc_authorization_created"])
        self.assertFalse(result["listener_created"])
        self.assertEqual(pointer["state"], "READY")
        self.assertEqual(pointer["transport_origin"], "TVC_RELAY_EGRESS")
        self.assertEqual(pointer["tvc_relay_authorization_id"], "RELAY-EGRESS-AUTH-1")
        self.assertEqual(pointer["authority_effect"], "NONE_INPUT_ONLY")

    def test_hosted_environment_with_materialized_relay_artifacts_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            env = authentic_env(runtime)
            env["GITHUB_ACTIONS"] = "true"
            with self.assertRaisesRegex(RuntimeError, "hosted_environment_forbidden"):
                MOD.materialize(runtime, env=env)

    def test_payload_hash_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            with self.assertRaisesRegex(RuntimeError, "authorization_payload_hash_mismatch"):
                MOD.materialize(runtime, env=authentic_env(runtime, corrupt_hash=True))

    def test_non_loopback_authorized_endpoint_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            with self.assertRaisesRegex(RuntimeError, "ingress_url_must_be_loopback"):
                MOD.materialize(runtime, env=authentic_env(runtime, endpoint="https://example.com/intr/materialization"))

    def test_transition_authority_expansion_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            with self.assertRaisesRegex(RuntimeError, "authorization_transition_authority_forbidden"):
                MOD.materialize(runtime, env=authentic_env(runtime, transition_authority=True))


if __name__ == "__main__":
    unittest.main()
