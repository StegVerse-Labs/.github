from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


consumer = load("sv002_consumer", "workers/sv002_intr_materialization_consumer.py")
ingress = load("universal_ingress", "workers/universal_intr_profiled_ingress.py")
hil_profile = load("hil_profile", "workers/hil_intr_profiled_ingress.py")


class SV002EventEphemeralTests(unittest.TestCase):
    def request(self):
        body = {
            "schema": consumer.REQUEST_SCHEMA,
            "materialization_id": "INTR-MAT-" + "a" * 24,
            "state": consumer.REQUEST_STATE,
            "transport_schema": "stegverse.universal-intr-transport/v1",
            "transport_protocol": "InTr",
            "transport_intent_hash": "sha256:" + "1" * 64,
            "operation_id": "SV002-PUBLIC-OBSERVE-test",
            "packet_id": "INTR-" + "2" * 24,
            "payload_hash": "sha256:" + "3" * 64,
            "payload_ref": "browser:SV002_PUBLIC_OBSERVE",
            "destination": consumer.DESTINATION,
            "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
            "downstream_owner_ref": consumer.DOWNSTREAM_OWNER,
            "event_triggered": True,
            "always_on_receiver_required": False,
            "second_user_device_required": False,
            "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
            "exact_packet_transport_retry_allowed": True,
            "blind_consequence_retry_allowed": False,
            "interlock_required": True,
            "request_grants_execution_authority": False,
            "claim_or_fence_minted": False,
            "transport_grants_execution_authority": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_transfer": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        }
        body["request_hash"] = consumer.digest_uri(body)
        return body

    def test_request_is_g18_independent_and_non_authorizing(self):
        request = self.request()
        consumer.validate_request(request)
        self.assertFalse(request["always_on_receiver_required"])
        self.assertFalse(request["request_grants_execution_authority"])
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(consumer.DOWNSTREAM_OWNER, "StegVerse-Labs/.github#493")

    def test_profile_preserves_hil_and_advertises_sv002(self):
        profile = ingress.profile(False)
        self.assertEqual(profile["profiles"], ["HIL:Ingress", "SV002:PublicObservation", "KV:KnowledgeVaultInterlock", "Publisher:ArtifactTransfer", "KV:PublisherArtifactImport"])
        self.assertFalse(profile["g18_required"])
        legacy = hil_profile.build_profile(tls_enabled=False)
        self.assertEqual(legacy["schema"], "stegverse.hil-intr-materialization-ingress-profile/v1")
        self.assertIn("SV002:PublicObservation", legacy["additional_materialization_profiles"])

    def test_sv002_ingress_writes_distinct_receipt_and_dispatches_without_authority(self):
        request = self.request()
        payload = request
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        headers = {
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": "TVC_RELAY_EGRESS",
            "X-StegVerse-Authorization-Id": "TEST-BOUND-AUTH",
            "X-StegVerse-Payload-SHA256": ingress.hashlib.sha256(raw).hexdigest(),
            "Content-Type": "application/json",
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(ingress, "_dispatch_sv002_consumer") as dispatch:
            dispatch.return_value = {"consumer_dispatch_attempted": True, "authority_effect": "NONE_DISPATCH_ONLY"}
            receipt = ingress.admit_sv002(runtime_root=Path(tmp), body=raw, headers=headers)
            self.assertEqual(receipt["schema"], ingress.SV002_RECEIPT_SCHEMA)
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertFalse(receipt["g18_required"])
            self.assertFalse(receipt["observer_direct_relation_to_stegverse_002"])
            self.assertFalse(receipt["round_trip_claimed"])
            self.assertFalse(receipt["observation_round_trip_claimed"])
            self.assertFalse(receipt["claim_or_fence_minted"])
            dispatch.assert_called_once()

    def test_sv002_bridge_advances_canonical_lease_to_public_verifying(self):
        text = (ROOT / "workers/sv002_observation_esrl_runtime_bridge.py").read_text(encoding="utf-8")
        self.assertIn("machine.open_after_local_verification()", text)
        self.assertIn("LeaseState.PUBLIC_VERIFYING", text)
        self.assertIn("machine.snapshot()", text)
        self.assertIn("canonical-runtime-lease.snapshot.json", text)
        self.assertNotIn('"state": "LOCAL_READY", "lease_id": lease_id', text)

    def test_consumer_requires_persisted_canonical_public_verifying_snapshot(self):
        request = self.request()
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            source = Path(td) / "source"
            source.mkdir()
            request_path = runtime / consumer.REQUEST_DIR_REL / f"{request['materialization_id']}.json"
            request_path.parent.mkdir(parents=True)
            request_path.write_text(json.dumps(request), encoding="utf-8")
            ingress_receipt = {
                "schema": "stegverse.sv002-intr-materialization-ingress/v1",
                "state": "INGRESS_ADMITTED",
                "materialization_id": request["materialization_id"],
                "request_hash": request["request_hash"],
                "transport_intent_hash": request["transport_intent_hash"],
                "payload_hash": request["payload_hash"],
                "operation_id": request["operation_id"],
                "packet_id": request["packet_id"],
                "credential_authority": "TV/TVC",
                "claim_or_fence_minted": False,
            }
            ingress_path = runtime / consumer.INGRESS_RECEIPT_DIR_REL / f"{request['materialization_id']}.json"
            ingress_path.parent.mkdir(parents=True)
            ingress_path.write_text(json.dumps(ingress_receipt), encoding="utf-8")

            execution = Path(td) / "execution"
            entrypoint = execution / consumer.TARGET_ENTRYPOINT
            entrypoint.parent.mkdir(parents=True)
            entrypoint.write_text("# fixture\n", encoding="utf-8")
            snapshot = {
                "schema": "stegverse.esrl.lease-machine-snapshot/v1",
                "request": {"lease_id": "SV002-OBS-ESRL-fixture"},
                "state": "PUBLIC_VERIFYING",
                "history": ["ABSENT", "REQUESTED", "ADMITTED", "PROVISIONING", "LOCAL_READY", "PUBLIC_VERIFYING"],
                "credential_authority": "TV/TVC",
                "authority_effect": "NONE",
            }
            snapshot_path = execution / "receipts/sovereign-network/sv002-public-observation/canonical-runtime-lease.snapshot.json"
            snapshot_path.parent.mkdir(parents=True)
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            evidence = {
                "state": "PUBLIC_VERIFYING",
                "lease_state": "PUBLIC_VERIFYING",
                "runtime_instantiated": True,
                "local_identity_verified": True,
                "canonical_runtime_lease_snapshot_ref": str(snapshot_path),
                "canonical_runtime_lease_snapshot_sha256": consumer.digest_uri(snapshot),
                "g18_completion_required": False,
                "observer_direct_relation_to_stegverse_002": False,
            }
            def materializer(**_kwargs):
                return {"runtime_root": execution, "evidence": evidence}
            def runner(*_args, **_kwargs):
                return subprocess.CompletedProcess([], 0, stdout="{}", stderr="")

            receipt = consumer.consume_one(
                source,
                runtime,
                request["materialization_id"],
                runner=runner,
                env={},
                runtime_materializer=materializer,
            )
            self.assertEqual(receipt["canonical_runtime_lease_state"], "PUBLIC_VERIFYING")
            self.assertTrue(receipt["canonical_runtime_lease_resume_required"])
            self.assertEqual(receipt["canonical_runtime_lease_snapshot_sha256"], consumer.digest_uri(snapshot))

            snapshot["history"] = ["ABSENT", "LEASE_OPEN"]
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            evidence["canonical_runtime_lease_snapshot_sha256"] = consumer.digest_uri(snapshot)
            with self.assertRaisesRegex(
                consumer.SV002InTrMaterializationError,
                "snapshot_history_invalid",
            ):
                consumer.consume_one(
                    source,
                    runtime,
                    request["materialization_id"],
                    runner=runner,
                    env={},
                    runtime_materializer=materializer,
                )

    def test_superseded_script_materialization_path_absent(self):
        self.assertFalse((ROOT / "scripts/consume_sv002_intr_materialization_request.py").exists())
        self.assertFalse((ROOT / "scripts/serve_sv002_intr_materialization_ingress.py").exists())
        bootstrap=(ROOT / "scripts/bootstrap_sovereign_runtime.py").read_text(encoding="utf-8")
        refresh=(ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
        installer=(ROOT / "scripts/install_sovereign_worker_source_refresh_service.py").read_text(encoding="utf-8")
        for text in (bootstrap,refresh,installer):
            self.assertNotIn("consume_sv002_intr_materialization_request.py",text)
            self.assertNotIn("serve_sv002_intr_materialization_ingress.py",text)
        self.assertNotIn("sv002-intr-materialization",installer)


if __name__ == "__main__":
    unittest.main()
