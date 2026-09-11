#!/usr/bin/env python3
"""Install ERL upstream receipt-lineage preservation into DEVICE_KV observation.

This is a fail-closed source transformation of the existing worker. It does not
create a worker, listener, claim, fence, credential, or transport receipt.
"""
from __future__ import annotations

import argparse
from pathlib import Path

OLD = '"prior_receipt_hash":sha256_uri(ingress),'
NEW = '"prior_receipt_hash": request.get("prior_transport_receipt_hash") or sha256_uri(ingress),'
GUARD_OLD = 'source_ref = ingress.get("node_id") or ingress.get("interlock_id") or request.get("transport_intent_hash")\n'
GUARD_NEW = '''upstream_prior = request.get("prior_transport_receipt_hash")\n    if upstream_prior is not None:\n        if not isinstance(upstream_prior,str) or len(upstream_prior)!=71 or not upstream_prior.startswith("sha256:"):\n            return None\n        erl_hashes=request.get("erl_upstream_receipt_hashes")\n        if erl_hashes is not None and (not isinstance(erl_hashes,list) or len(erl_hashes)!=2 or erl_hashes[-1]!=upstream_prior):\n            return None\n    source_ref = ingress.get("node_id") or ingress.get("interlock_id") or request.get("transport_intent_hash")\n'''


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
    require(NEW in result, "ERL terminal prior lineage not installed")
    require('erl_upstream_receipt_hashes' in result, "ERL upstream lineage guard not installed")
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
        require(transformed == source, "ERL DEVICE_KV prior-lineage repair is not installed")
        print("PASS: ERL DEVICE_KV prior-lineage repair already installed")
        return 0
    if transformed != source:
        path.write_text(transformed, encoding="utf-8")
        print("INSTALLED: ERL upstream prior receipt preserved into existing DEVICE_KV worker")
    else:
        print("NOOP: ERL DEVICE_KV prior-lineage repair already installed")
    print("NONCLAIM: source repair does not prove terminal DEVICE_SYSTEM -> KV runtime execution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
