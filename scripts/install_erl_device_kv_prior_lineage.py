#!/usr/bin/env python3
"""Install ERL terminal identity/receipt continuity into DEVICE_KV observation.

This is a fail-closed source transformation of the existing worker. It does not
create a worker, listener, claim, fence, credential, provider operation, or
transport authority. Non-ERL DEVICE_KV behavior remains unchanged.
"""
from __future__ import annotations

import argparse
from pathlib import Path

OLD = '"prior_receipt_hash":sha256_uri(ingress),'
NEW = '"prior_receipt_hash": request.get("prior_transport_receipt_hash") or sha256_uri(ingress),'
GUARD_OLD = 'source_ref = ingress.get("node_id") or ingress.get("interlock_id") or request.get("transport_intent_hash")\n'
GUARD_NEW = '''upstream_prior = request.get("prior_transport_receipt_hash")\n    if upstream_prior is not None:\n        if not isinstance(upstream_prior,str) or len(upstream_prior)!=71 or not upstream_prior.startswith("sha256:"):\n            return None\n        erl_hashes=request.get("erl_upstream_receipt_hashes")\n        if erl_hashes is not None and (not isinstance(erl_hashes,list) or len(erl_hashes)!=2 or erl_hashes[-1]!=upstream_prior):\n            return None\n    source_ref = ingress.get("node_id") or ingress.get("interlock_id") or request.get("transport_intent_hash")\n'''
BASIS_OLD = '        "queued_payload_hash":request.get("payload_hash"),\n    }\n'
BASIS_NEW = '''        "queued_payload_hash":request.get("payload_hash"),\n        "materialization_request":request,\n        "ingress_receipt":ingress,\n    }\n'''
LOAD_OLD = '        connector = load_canonical_device_kv_connector(stegos_root)\n'
LOAD_NEW = '''        connector = load_canonical_device_kv_connector(stegos_root)\n        erl_terminal_mod = load_module(ROOT / "workers/erl_device_kv_terminal.py", "erl_device_kv_terminal")\n'''
BRANCH_ANCHOR = '''    if parent_valid:\n        continuity_id = str(continuity["continuity_id"]); state_root = str(continuity["node_kv_state_root"])\n'''
BRANCH_INSERT = '''    if event_basis is not None and erl_terminal_mod.is_erl_terminal_request(event_basis.get("materialization_request")):\n        try:\n            erl_terminal_result = erl_terminal_mod.execute(\n                runtime_root=ROOT,\n                stegos_root=stegos_root,\n                request=event_basis["materialization_request"],\n                ingress=event_basis["ingress_receipt"],\n                boundary_identity_ref=str(event_basis["next_boundary_identity_ref"]),\n            )\n        except Exception as exc:\n            return write_blocked(base, "ERL_DEVICE_KV_TERMINAL_REPAIR_REQUIRED",\n                f"ERL exact terminal DEVICE_SYSTEM->KV transport failed closed: {type(exc).__name__}: {exc}",\n                "Repair exact full-intent/envelope/receipt continuity and retry under a fresh WorkerCoordinator fence.",\n                "original ERL packet identity and exact envelope bytes traverse DEVICE_SYSTEM->KV and complete the three-hop receipt chain", epoch)\n        observation = {\n            **base,\n            "state":"OBSERVED",\n            "transition_id":"DEVICE_KV_INTR_OBSERVED",\n            "observed_at":now_iso(),\n            "event_materialization_ingress_verified":True,\n            "event_materialization_id":event_basis.get("materialization_id"),\n            "event_transport_intent_hash":event_basis.get("transport_intent_hash"),\n            "event_queued_payload_hash":event_basis.get("queued_payload_hash"),\n            "boundary_identity_source":"ERL_EVENT_MATERIALIZATION_INGRESS",\n            "erl_terminal_transport":erl_terminal_result,\n            "request_exact_bytes_transported":True,\n            "device_to_kv_receipt_verified":True,\n            "durable_receipt_readback_verified":True,\n            "same_execution_reconstructed":True,\n            "transport_grants_execution_authority":False,\n            "secret_plaintext_present":False,\n        }\n        atomic_write(RECEIPT, observation)\n        if load_json(RECEIPT) != observation:\n            return 5\n        json.dump(worker_response("COMPLETED", "DEVICE_KV_INTR_OBSERVED", epoch), sys.stdout)\n        print()\n        return 0\n\n''' + BRANCH_ANCHOR


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def transform(source: str) -> str:
    result = source
    if NEW not in result:
        require(result.count(OLD) == 1, "prior receipt anchor drift")
        result = result.replace(OLD, NEW, 1)
    if 'upstream_prior = request.get("prior_transport_receipt_hash")' not in result:
        require(result.count(GUARD_OLD) == 1, "event source-ref anchor drift")
        result = result.replace(GUARD_OLD, GUARD_NEW, 1)
    if '"materialization_request":request' not in result:
        require(result.count(BASIS_OLD) == 1, "event basis anchor drift")
        result = result.replace(BASIS_OLD, BASIS_NEW, 1)
    if 'erl_terminal_mod = load_module' not in result:
        require(result.count(LOAD_OLD) == 1, "terminal helper load anchor drift")
        result = result.replace(LOAD_OLD, LOAD_NEW, 1)
    if 'ERL_DEVICE_KV_TERMINAL_REPAIR_REQUIRED' not in result:
        require(result.count(BRANCH_ANCHOR) == 1, "terminal execution branch anchor drift")
        result = result.replace(BRANCH_ANCHOR, BRANCH_INSERT, 1)
    require(NEW in result, "ERL terminal prior lineage not installed")
    require('erl_upstream_receipt_hashes' in result, "ERL upstream lineage guard not installed")
    require('"materialization_request":request' in result, "ERL terminal request projection missing from event basis")
    require('erl_terminal_mod = load_module' in result, "ERL terminal helper load missing")
    require('ERL_DEVICE_KV_TERMINAL_REPAIR_REQUIRED' in result, "ERL terminal exact-identity path missing")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", default="workers/device_kv_intr_observation_worker.py")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = Path(args.worker)
    source = path.read_text(encoding="utf-8")
    transformed = transform(source)
    if args.check:
        require(transformed == source, "ERL DEVICE_KV terminal identity repair is not installed")
        print("PASS: ERL DEVICE_KV terminal identity/receipt continuity already installed")
        return 0
    if transformed != source:
        path.write_text(transformed, encoding="utf-8")
        print("INSTALLED: ERL exact full-intent terminal path installed into existing DEVICE_KV worker")
    else:
        print("NOOP: ERL DEVICE_KV terminal identity/receipt continuity already installed")
    print("NONCLAIM: source repair does not prove terminal DEVICE_SYSTEM -> KV runtime execution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
