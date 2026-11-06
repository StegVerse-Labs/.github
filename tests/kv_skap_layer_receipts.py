"""Shape-faithful cvk layer-1 KV-access and layer-2 SKAP-access receipts for the device-kv round-trip tests.

The fields follow StegVerse-Labs/continuity-vault-kit runtime/kv_interlock_endpoint.py (_mint_kv_access_receipt) and
runtime/kv_skap_layer2.py (SkapLayer2Gate.admit). Each receipt_hash is the sha256 of the canonical body, as cvk mints it.
Ruling C, StegVerse-org/.github#167 c6393756343 (C1, C2).
"""
import hashlib
import json


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def seal(body):
    body = {k: v for k, v in body.items() if k != "receipt_hash"}
    return {**body, "receipt_hash": "sha256:" + hashlib.sha256(_canonical(body)).hexdigest()}


def layer1(device_kv_terminal, *, node="node://test/healthy-1"):
    return seal({"schema": "stegverse.kv-access-receipt/v1", "boundary": "INTR_DEVICE_KV", "layer": 1, "hop_index": 0,
                 "from_role": "DEVICE", "to_role": "KV", "minted_by": "KVInterlockRuntime.handle", "endpoint_kind": "KV",
                 "request_id": "kv-request-1", "operation": "SKAP_SEALED_CREDENTIAL_APPEND", "packet_id": "INTR-test",
                 "intr_receipt_ref": device_kv_terminal, "requester_node_ref": node,
                 "healthy_node_receipt": {"healthy_node_established": True}, "prior_receipt_hash": None,
                 "authority_effect": "NONE"})


def layer2(kv_access, *, operation="SKAP_SEALED_CREDENTIAL_APPEND", subject="skap://APIs/coinbase/owner/1"):
    return seal({"schema": "stegverse.skap-access-receipt/v1", "boundary": "KV_INTERNAL_SKAP_GATE", "layer": 2,
                 "hop_index": 1, "from_role": "KV", "to_role": "SKAP_VAULT", "minted_by": "SkapLayer2Gate.admit",
                 "endpoint_kind": "SKAP_VAULT", "principal_ref": "principal://owner/1", "operation": operation,
                 "subject_ref": subject, "prior_receipt_hash": kv_access["receipt_hash"],
                 "layer1_intr_receipt_ref": kv_access["intr_receipt_ref"],
                 "layer1_requester_node_ref": kv_access["requester_node_ref"], "sequence": 0, "authority_effect": "NONE"})


def pair(device_kv_terminal):
    kv_access = layer1(device_kv_terminal)
    return kv_access, layer2(kv_access)
