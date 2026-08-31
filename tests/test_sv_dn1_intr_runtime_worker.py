import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers import sv_dn1_intr_runtime_worker as worker


class _Validator:
    @staticmethod
    def validate_exchange(exchange):
        return []


def _exchange():
    transform = "sha256:" + "a" * 64
    return {
        "schema_version": "stegverse.sv-dn1.interlock-exchange/v1",
        "exchange_id": "sha256:" + "b" * 64,
        "source_system": "huggingface",
        "source_object": {
            "native_ref": "https://huggingface.co/api/models/Qwen/Qwen3-8B",
            "observed_at": "2026-08-28T02:00:00Z",
        },
        "raw_evidence": {
            "preserved_native_fields": {"modelId": "Qwen/Qwen3-8B"},
        },
        "far_side_receipt": {
            "transformation_hash": transform,
            "authority_effect": "NONE",
        },
        "intr": {
            "previous_receipt_hash": transform,
            "authority_effect": "NONE",
        },
    }


class SvDn1IntrRuntimeWorkerTests(unittest.TestCase):
    def test_registry_adapter_and_handoff_preserve_route_authority_boundary(self):
        root = Path(__file__).resolve().parents[1]
        registry = json.loads((root / "control/worker-registry.d/sv-dn1-intr-runtime-001.json").read_text())
        adapter = json.loads((root / "control/process-worker-adapters.d/sv-dn1-intr-runtime-001.json").read_text())
        handoff = json.loads((root / "handoffs/SV-DN1-INTR-RUNTIME-001.json").read_text())

        self.assertEqual(registry["tasks"][0]["state"], "HANDOFF_READY")
        self.assertIsNone(registry["tasks"][0]["claim_id"])
        self.assertFalse(registry["github_token_required"])

        row = adapter["adapters"][0]
        self.assertEqual(row["adapter_ref"], "process:sv-dn1-intr-runtime-v1")
        self.assertNotIn("GITHUB_TOKEN", row["env_allowlist"])
        self.assertNotIn("HF_TOKEN", row["env_allowlist"])

        authority = handoff["authority"]
        self.assertFalse(authority["route_specific_intr_traversal_authority"])
        self.assertTrue(authority["universal_intr_adjacent_hop_traversal_authority"])
        self.assertEqual(handoff["input_contract"]["universal_intr_policy_id"], worker.UNIVERSAL_POLICY_ID)
        self.assertEqual(handoff["input_contract"]["boundary_from"], "EXTERNAL_SYSTEM")
        self.assertEqual(handoff["input_contract"]["boundary_to"], "STEGOS_ECOSYSTEM")
        self.assertTrue(handoff["input_contract"]["canonical_protocol_adopted"])
        self.assertFalse(authority["public_source_acquisition_authority"])
        self.assertFalse(authority["repository_writeback_authority"])
        self.assertFalse(authority["sdk_admission_authority"])
        self.assertFalse(authority["canonical_protocol_adoption_authority"])
        self.assertFalse(authority["heartbeat_grants_execution_authority"])

    def test_upstream_missing_returns_handoff_ready(self):
        with mock.patch.object(worker, "load_upstream", side_effect=worker.UpstreamPending("resident missing")):
            with (
                mock.patch("sys.stdin", io.StringIO(json.dumps({"schema": "x"}) + "\n")),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
                mock.patch.object(worker, "execute", side_effect=worker.UpstreamPending("resident missing")),
            ):
                self.assertEqual(worker.main(), 0)
                result = json.loads(stdout.getvalue())
        self.assertEqual(result["state"], "HANDOFF_READY")
        self.assertEqual(result["transition_id"], "SV_DN1_RESIDENT_OBSERVATION_PENDING")
        self.assertFalse(result["blocker"]["human_action_required"])
        self.assertFalse(result["blocker"]["github_token_required"])

    def test_execute_emits_universal_adjacent_hop_receipt_without_runtime_activation_or_sdk_claim(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            resident = temp / "resident"
            source = temp / "source"
            bound = temp / "intr"
            (resident / "receipts").mkdir(parents=True)
            (resident / "observed").mkdir(parents=True)
            (source / "scripts").mkdir(parents=True)
            (source / "config").mkdir(parents=True)

            exchange = _exchange()
            capture = {
                "schema_version": "stegverse.sv-dn1.source-capture/v1",
                "source_system": "huggingface",
                "final_url": exchange["source_object"]["native_ref"],
                "observed_at": exchange["source_object"]["observed_at"],
                "raw_sha256": "sha256:" + "c" * 64,
                "parsed_json": exchange["raw_evidence"]["preserved_native_fields"],
                "claims": {
                    "credential_used": False,
                    "hugging_face_endorsement_claimed": False,
                },
            }
            resident_receipt = {
                "task_id": worker.UPSTREAM_TASK_ID,
                "state": "COMPLETE",
                "transition_id": worker.UPSTREAM_TRANSITION,
                "claim_id": "resident-claim",
                "runtime_source_pin_verified": True,
                "raw_response_sha256_present": True,
                "raw_response_sha256": capture["raw_sha256"],
                "semantic_exchange_valid": True,
                "semantic_exchange_id": exchange["exchange_id"],
                "credential_used": False,
                "github_token_used": False,
                "repository_writeback_performed": False,
                "sdk_admitted": False,
            }
            (resident / "receipts/latest.json").write_text(json.dumps(resident_receipt))
            (resident / "observed/source-capture.json").write_text(json.dumps(capture))
            (resident / "observed/exchange.json").write_text(json.dumps(exchange))

            (source / "scripts/sv_dn1_stegverse_interlock.py").write_text("# fixture\n")
            (source / "config/sv_dn1_runtime_source_manifest.json").write_text(json.dumps({
                "schema": "stegverse.sv-dn1.runtime-source-manifest/v1",
                "hash_profile": "git-blob-sha1",
                "source_basis_commit": "d" * 40,
                "files": {
                    "scripts/sv_dn1_stegverse_interlock.py": "e" * 40,
                },
            }))

            invocation = {
                "schema": "stegverse.worker-invocation/v0.1",
                "task": {
                    "task_id": worker.TASK_ID,
                    "worker_id": worker.WORKER_ID,
                    "claim_id": "intr-claim",
                    "heartbeat_timing": {"fencing_token": 9},
                },
                "context": {"observed_at": "2026-08-28T02:01:00Z"},
                "handoff": {
                    "authority": {
                        "credential_authority": "TV/TVC",
                        "github_token_required": False,
                        "non_tv_tvc_secret_or_token_allowed": False,
                        "repository_writeback_authority": False,
                        "sdk_admission_authority": False,
                        "canonical_protocol_adoption_authority": False,
                        "heartbeat_grants_execution_authority": False,
                    },
                    "input_contract": {
                        "upstream_task_id": worker.UPSTREAM_TASK_ID,
                        "upstream_transition_id": worker.UPSTREAM_TRANSITION,
                        "route_id": worker.ROUTE_ID,
                        "transport_profile": worker.TRANSPORT_PROFILE,
                        "runtime_receipt_schema": worker.RECEIPT_SCHEMA,
                        "canonical_protocol_adopted": True,
                        "universal_intr_policy_id": worker.UNIVERSAL_POLICY_ID,
                        "boundary_from": worker.BOUNDARY_FROM,
                        "boundary_to": worker.BOUNDARY_TO,
                        "interlock_required_per_hop": True,
                        "receipt_hash_chain_required": True,
                        "runtime_activation_claimed": False,
                        "production_interlock_runtime_activated": False,
                    },
                },
            }

            with (
                mock.patch.object(worker, "resident_state_root", return_value=resident),
                mock.patch.object(worker, "source_root", return_value=source),
                mock.patch.object(worker, "bound_state_root", return_value=bound),
                mock.patch.object(worker, "find_node", return_value=(temp / "node.json", {"declared": True})),
                mock.patch.object(worker, "load_destination_validator", return_value=_Validator),
                mock.patch.dict("os.environ", {}, clear=True),
            ):
                result = worker.execute(invocation)

            self.assertEqual(result["transition_id"], "SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE")
            self.assertEqual(result["destination_validation"], "PASS")
            self.assertTrue(result["lineage_verified"])
            self.assertFalse(result["sdk_admitted"])
            self.assertTrue(result["canonical_protocol_adopted"])
            self.assertEqual(result["universal_intr_policy_id"], worker.UNIVERSAL_POLICY_ID)
            self.assertEqual(result["boundary_from"], "EXTERNAL_SYSTEM")
            self.assertEqual(result["boundary_to"], "STEGOS_ECOSYSTEM")
            self.assertTrue(result["interlock_required_per_hop"])
            self.assertTrue(result["receipt_hash_chain_required"])
            self.assertFalse(result["runtime_activation_claimed"])
            self.assertFalse(result["production_interlock_runtime_activated"])

            receipt = json.loads((bound / "receipts/latest.json").read_text())
            self.assertEqual(receipt["schema_version"], worker.RECEIPT_SCHEMA)
            self.assertEqual(receipt["route_id"], worker.ROUTE_ID)
            self.assertEqual(receipt["transport_profile"], worker.TRANSPORT_PROFILE)
            self.assertEqual(receipt["exchange_id"], exchange["exchange_id"])
            self.assertEqual(receipt["source_transform_hash"], exchange["far_side_receipt"]["transformation_hash"])
            self.assertEqual(receipt["previous_receipt_hash"], exchange["intr"]["previous_receipt_hash"])
            self.assertTrue(receipt["lineage_verified"])
            self.assertTrue(receipt["claims"]["canonical_protocol_adopted"])
            self.assertEqual(receipt["claims"]["universal_intr_policy_id"], worker.UNIVERSAL_POLICY_ID)
            self.assertEqual(receipt["claims"]["boundary_from"], "EXTERNAL_SYSTEM")
            self.assertEqual(receipt["claims"]["boundary_to"], "STEGOS_ECOSYSTEM")
            self.assertTrue(receipt["claims"]["interlock_required_per_hop"])
            self.assertTrue(receipt["claims"]["receipt_hash_chain_required"])
            self.assertFalse(receipt["claims"]["runtime_activation_claimed"])
            self.assertFalse(receipt["claims"]["production_interlock_runtime_activated"])
            self.assertFalse(receipt["claims"]["sdk_admitted"])
            body = {k: v for k, v in receipt.items() if k != "receipt_hash"}
            self.assertEqual(receipt["receipt_hash"], worker.sha256_ref(body))

            carrier_signal = json.loads((bound / "observed/carrier-signal.json").read_text())
            carrier_receipt = json.loads((bound / "receipts/carrier-binding.latest.json").read_text())
            self.assertEqual(carrier_receipt["transition_id"], "SV_DN1_HB_INTR_CARRIER_BOUND")
            self.assertEqual(carrier_receipt["intr_receipt_hash"], receipt["receipt_hash"])
            self.assertEqual(carrier_receipt["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
            self.assertTrue(carrier_receipt["packet_recovery_verified"])
            self.assertFalse(carrier_receipt["heartbeat_grants_authority"])
            self.assertFalse(carrier_receipt["derived_carrier_grants_authority"])
            self.assertEqual(carrier_receipt["authority_effect"], "NONE_CARRIER_ONLY")
            self.assertEqual(carrier_signal["intr"]["packet_sha256"], carrier_receipt["packet_sha256"])
            self.assertEqual(worker.recover_intr_packet_bytes(carrier_signal), worker.canonical(exchange))

    def test_hb_carrier_binding_is_deterministic_for_fixed_reference(self):
        exchange = _exchange()
        body = {"schema_version": worker.RECEIPT_SCHEMA, "route_id": worker.ROUTE_ID}
        receipt = {"receipt_hash": worker.sha256_ref(body), **body}
        now_ns = 1_787_511_600_000_000_000 + (100 * 10_000_000)
        a = worker.build_hb_carrier_binding(exchange, receipt, now_ns=now_ns)
        b = worker.build_hb_carrier_binding(exchange, receipt, now_ns=now_ns)
        self.assertEqual(a, b)
        self.assertEqual(a["receipt"]["heartbeat_epoch"], 132)
        self.assertEqual(a["signal"]["carrier"]["reference_rate_hz"], 100.0)
        self.assertEqual(a["signal"]["carrier"]["phase_slots"], 16)
        self.assertEqual(
            a["signal"]["carrier"]["channel_derivation"],
            "SHA256_PACKET_ID_FIRST32_MOD_16",
        )
        self.assertEqual(
            a["receipt"]["carrier_packet_id"],
            a["signal"]["intr"]["packet_id"],
        )
        self.assertEqual(
            a["receipt"]["carrier_binding_sha256"],
            a["signal"]["carrier"]["carrier_binding_sha256"],
        )
        self.assertTrue(a["receipt"]["packet_recovery_verified"])

    def test_identity_drift_fails_closed(self):
        exchange = _exchange()
        capture = {
            "schema_version": "stegverse.sv-dn1.source-capture/v1",
            "source_system": "huggingface",
            "final_url": exchange["source_object"]["native_ref"],
            "observed_at": exchange["source_object"]["observed_at"],
            "raw_sha256": "sha256:" + "c" * 64,
            "parsed_json": exchange["raw_evidence"]["preserved_native_fields"],
            "claims": {"credential_used": False, "hugging_face_endorsement_claimed": False},
        }
        receipt = {
            "task_id": worker.UPSTREAM_TASK_ID,
            "state": "COMPLETE",
            "transition_id": worker.UPSTREAM_TRANSITION,
            "runtime_source_pin_verified": True,
            "raw_response_sha256_present": True,
            "raw_response_sha256": "sha256:" + "f" * 64,
            "semantic_exchange_valid": True,
            "semantic_exchange_id": exchange["exchange_id"],
            "credential_used": False,
            "github_token_used": False,
            "repository_writeback_performed": False,
            "sdk_admitted": False,
        }
        with self.assertRaisesRegex(RuntimeError, "raw digest mismatch"):
            worker.validate_upstream(receipt, capture, exchange)

    def test_hosted_or_credential_environment_is_rejected(self):
        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "hosted environments"):
                worker.execute({})
        with mock.patch.dict("os.environ", {"HF_TOKEN": "present"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "credential-bearing environment"):
                worker.execute({})


if __name__ == "__main__":
    unittest.main()
