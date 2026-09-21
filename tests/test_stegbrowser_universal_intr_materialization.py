from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


consumer = load("stegbrowser_intr_consumer", "workers/stegbrowser_intr_materialization_consumer.py")
ingress = load("stegbrowser_intr_ingress", "workers/stegbrowser_intr_materialization_ingress.py")
installer = load("stegbrowser_intr_installer", "scripts/install_stegbrowser_universal_intr_route.py")
executor = load("stegbrowser_intr_executor", "scripts/run_stegbrowser_universal_intr_materialization.py")


def request(binding_path: str, payload_hash: str) -> dict:
    body = {
        "schema": consumer.REQUEST_SCHEMA,
        "materialization_id": "INTR-MAT-" + "a" * 24,
        "state": consumer.REQUEST_STATE,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": "sha256:" + "1" * 64,
        "operation_id": "STEGBROWSER:TEST",
        "packet_id": "INTR-" + "2" * 24,
        "payload_hash": payload_hash,
        "payload_ref": binding_path,
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
    return {**body, "request_hash": consumer.digest_uri(body)}


def trigger(req: dict, node_id: str = "SV-NODE-" + "a" * 24, interlock_id: str = "SV-IL-" + "b" * 24) -> dict:
    entry_body = {
        "schema": "stegos.node_intr_outbox_entry.v1",
        "state": "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
        "node_id": node_id,
        "interlock_id": interlock_id,
        "materialization_id": req["materialization_id"],
        "request_hash": req["request_hash"],
        "transport_intent_hash": req["transport_intent_hash"],
        "payload_hash": req["payload_hash"],
        "response_sha256": "3" * 64,
        "provenance_sha256": "sha256:" + "4" * 64,
        "destination": req["destination"],
        "downstream_owner_ref": req["downstream_owner_ref"],
        "materialization_request": req,
        "network_delivery_observed": False,
        "runtime_materialization_observed": False,
        "receiver_receipt_observed": False,
        "tvc_receipt_observed": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_LOCAL_CONTINUITY_ONLY",
    }
    entry = {**entry_body, "outbox_entry_hash": ingress.sha_uri(entry_body)}
    trigger_body = {
        "schema": ingress.hil.NODE_TRIGGER_SCHEMA,
        "transport_origin": ingress.hil.ORIGIN_NODE,
        "node_id": node_id,
        "interlock_id": interlock_id,
        "outbox_entry_hash": entry["outbox_entry_hash"],
        "node_outbox_entry": entry,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_TRIGGER_ONLY",
    }
    return {**trigger_body, "trigger_sha256": ingress.sha_uri(trigger_body)}


def test_installer_reuses_shared_listener_and_is_idempotent():
    source = (ROOT / "workers/universal_intr_profiled_ingress.py").read_text(encoding="utf-8")
    once = installer.transform(source)
    twice = installer.transform(once)
    assert once == twice
    assert '"StegBrowser:ManifestInvocation"' in once
    assert "is_stegbrowser(payload)" in once
    assert once.count("ThreadingHTTPServer") >= 1
    assert "class Server(ThreadingHTTPServer)" in once


def test_node_trigger_is_admitted_write_once_without_authority():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td)
        binding = {"fixture": True}
        binding_path = runtime / "binding.json"
        binding_path.write_text(json.dumps(binding), encoding="utf-8")
        req = request(str(binding_path), consumer.digest_uri(binding))
        packet = trigger(req)
        raw = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
        headers = {
            "Content-Type": "application/json",
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": ingress.hil.ORIGIN_NODE,
            "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
        }
        with patch.object(ingress, "_dispatch") as dispatch:
            dispatch.return_value = {"consumer_dispatch_attempted": True, "authority_effect": "NONE_DISPATCH_ONLY"}
            receipt = ingress.admit(runtime_root=runtime, body=raw, headers=headers)
        assert receipt["state"] == "INGRESS_ADMITTED"
        assert receipt["node_id"] == packet["node_id"]
        assert receipt["interlock_id"] == packet["interlock_id"]
        assert receipt["claim_or_fence_minted"] is False
        assert receipt["credential_authority"] == "TV/TVC"
        assert receipt["github_token_runtime_authority"] == "NONE"
        assert (runtime / consumer.REQUEST_DIR_REL / f"{req['materialization_id']}.json").is_file()


def test_tampered_node_trigger_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td)
        binding_path = runtime / "binding.json"
        binding_path.write_text("{}", encoding="utf-8")
        req = request(str(binding_path), consumer.digest_uri({}))
        packet = trigger(req)
        packet["node_outbox_entry"]["interlock_id"] = "SV-IL-" + "f" * 24
        raw = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
        headers = {"Content-Type":"application/json","X-StegVerse-Transport":"InTr","X-StegVerse-Transport-Origin":ingress.hil.ORIGIN_NODE,"X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest()}
        try:
            ingress.admit(runtime_root=runtime, body=raw, headers=headers)
            assert False, "tampered trigger should fail"
        except ValueError as exc:
            assert "node_outbox_entry_hash_mismatch" in str(exc)


def test_consumer_dispatches_existing_manifest_runner_only_after_exact_binding():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source = root / "source"
        runtime = root / "runtime"
        stegos = root / "StegOS"
        source.mkdir(); runtime.mkdir(); (stegos / "stegos").mkdir(parents=True)
        runner_path = source / consumer.RUNNER_REL
        runner_path.parent.mkdir(parents=True, exist_ok=True)
        runner_path.write_text("# fixture\n", encoding="utf-8")
        (stegos / "stegos/network_manifold.py").write_text("# fixture\n", encoding="utf-8")
        node_path = root / "node.json"; node_path.write_text("{}", encoding="utf-8")
        binding = {
            "schema":"stegverse.stegbrowser-universal-intr-invocation-binding/v1","state":"BOUND_FOR_UNIVERSAL_INTR_MATERIALIZATION",
            "goal_task_id":consumer.GOAL_ID,"parent_task_id":consumer.PARENT_TASK_ID,"cosv_task_vector":consumer.COSV,
            "invocation_request_nonce":consumer.NONCE,"manifest_ref":"manifest.json","manifest_sha256":"a"*64,
            "node_genesis_receipt_ref":str(node_path),"node_id":"SV-NODE-"+"a"*24,"interlock_id":"SV-IL-"+"b"*24,
            "registration_receipt_sha256":"c"*64,"stegos_source_root":str(stegos),"request_mutated":False,
            "resident_request_sweep_required":False,"control_plane_source_package_required":False,"credential_authority":"TV/TVC",
            "github_runtime_authority":"NONE","authority_effect":"NONE_BINDING_ONLY",
        }
        binding_path = runtime / "binding.json"; binding_path.write_text(json.dumps(binding), encoding="utf-8")
        req = request(str(binding_path), consumer.digest_uri(binding))
        request_path = runtime / consumer.REQUEST_DIR_REL / f"{req['materialization_id']}.json"; request_path.parent.mkdir(parents=True); request_path.write_text(json.dumps(req), encoding="utf-8")
        ingress_receipt = {
            "schema":consumer.INGRESS_SCHEMA,"state":"INGRESS_ADMITTED","materialization_id":req["materialization_id"],"request_hash":req["request_hash"],
            "transport_intent_hash":req["transport_intent_hash"],"payload_hash":req["payload_hash"],"operation_id":req["operation_id"],"packet_id":req["packet_id"],
            "transport_origin":"STEGOS_NODE_OUTBOX","node_id":binding["node_id"],"interlock_id":binding["interlock_id"],"claim_or_fence_minted":False,
        }
        ingress_path = runtime / consumer.INGRESS_RECEIPT_DIR_REL / f"{req['materialization_id']}.json"; ingress_path.parent.mkdir(parents=True); ingress_path.write_text(json.dumps(ingress_receipt), encoding="utf-8")
        boundary = {"runtime_ingress_projection":{"workercoordinator_claim_fence_observed":True,"authentic_intr_ingress_observed":True}}
        boundary_path = runtime / "receipts/sovereign-host/stegbrowser-runtime-remediation-boundary.latest.json"; boundary_path.parent.mkdir(parents=True); boundary_path.write_text(json.dumps(boundary), encoding="utf-8")
        observed = {}
        def fake_runner(command, **kwargs):
            observed["command"] = command; observed["env"] = kwargs["env"]
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        receipt = consumer.consume_one(source, runtime, req["materialization_id"], runner=fake_runner, env={})
        assert observed["command"][1].endswith("run_stegbrowser_manifest_bound_runtime.py")
        params = json.loads(observed["env"]["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"])
        assert params["node_genesis_receipt"] == str(node_path)
        assert receipt["workercoordinator_claim_fence_observed"] is True
        assert receipt["authentic_intr_ingress_observed"] is True
        assert receipt["round_trip_1_started"] is False


def test_executor_preserves_nonce_and_uses_existing_stegos_builders_and_shared_server():
    source = (ROOT / "scripts/run_stegbrowser_universal_intr_materialization.py").read_text(encoding="utf-8")
    assert executor.NONCE in source
    assert "build_transport_intent" in source
    assert "build_materialization_request" in source
    assert "shared.Server" in source
    assert "shared.INGRESS_PATH" in source
    assert "resident_request_sweep_required\": False" in source
    assert "control_plane_source_package_required\": False" in source
    assert "dispatch_resident_execution_requests" not in source
    assert "control_plane_source_package" not in source.lower().replace('control_plane_source_package_required', '')


def test_browser_carried_opaque_binding_is_persisted_and_resolved_without_filesystem_payload_ref():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td)
        binding = {
            "schema":"stegverse.stegbrowser-universal-intr-invocation-binding/v1",
            "state":"BOUND_FOR_UNIVERSAL_INTR_MATERIALIZATION",
            "goal_task_id":consumer.GOAL_ID,
            "parent_task_id":consumer.PARENT_TASK_ID,
            "cosv_task_vector":consumer.COSV,
            "invocation_request_nonce":consumer.NONCE,
            "manifest_ref":"manifest.json",
            "manifest_sha256":"a"*64,
            "node_genesis_receipt_ref":"indexeddb://stegos-node-v1/meta/registration",
            "node_id":"SV-NODE-"+"a"*24,
            "interlock_id":"SV-IL-"+"b"*24,
            "registration_receipt_sha256":"sha256:"+"c"*64,
            "stegos_source_root":"StegVerse-Labs/Site#SV002_VALIDATED_BROWSER_BASELINE",
            "request_mutated":False,
            "resident_request_sweep_required":False,
            "control_plane_source_package_required":False,
            "credential_authority":"TV/TVC",
            "github_runtime_authority":"NONE",
            "authority_effect":"NONE_BINDING_ONLY",
        }
        payload_hash = consumer.digest_uri(binding)
        req = request("opaque://stegbrowser-manifest-invocation/" + payload_hash[7:], payload_hash)
        packet = trigger(req, node_id=binding["node_id"], interlock_id=binding["interlock_id"])
        packet["node_outbox_entry"]["binding_hash"] = payload_hash
        packet["node_outbox_entry"]["stegbrowser_invocation"] = binding
        entry_body = dict(packet["node_outbox_entry"])
        entry_body.pop("outbox_entry_hash", None)
        packet["node_outbox_entry"]["outbox_entry_hash"] = ingress.sha_uri(entry_body)
        packet["outbox_entry_hash"] = packet["node_outbox_entry"]["outbox_entry_hash"]
        trigger_body = dict(packet)
        trigger_body.pop("trigger_sha256", None)
        packet["trigger_sha256"] = ingress.sha_uri(trigger_body)
        raw = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
        headers = {
            "Content-Type":"application/json",
            "X-StegVerse-Transport":"InTr",
            "X-StegVerse-Transport-Origin":ingress.hil.ORIGIN_NODE,
            "X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest(),
        }
        with patch.object(ingress, "_dispatch") as dispatch:
            dispatch.return_value = {"consumer_dispatch_attempted": True, "authority_effect": "NONE_DISPATCH_ONLY"}
            receipt = ingress.admit(runtime_root=runtime, body=raw, headers=headers)
        digest = payload_hash[7:]
        retained = runtime / ingress.BINDING_DIR_REL / f"{digest}.json"
        assert retained.is_file()
        assert json.loads(retained.read_text(encoding="utf-8")) == binding
        assert receipt["binding_payload_ref"] == req["payload_ref"]
        assert Path(receipt["binding_custody_ref"]) == retained


def test_consumer_maps_opaque_binding_ref_to_ingress_retained_binding_path():
    source = (ROOT / "workers/stegbrowser_intr_materialization_consumer.py").read_text(encoding="utf-8")
    assert 'opaque_prefix = "opaque://stegbrowser-manifest-invocation/"' in source
    assert 'payload_path = runtime / BINDING_DIR_REL / f"{digest}.json"' in source
    assert 'request.get("payload_hash") != "sha256:" + digest' in source
