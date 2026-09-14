#!/usr/bin/env python3
"""Prepare existing resident source for KV AI memory Universal InTr admission.

This helper applies only the idempotent shared-listener route transform. It does
not create or start a listener, scheduler, worker, claim/fence, credential path,
transport event, provider operation, model call, KV write, or runtime receipt.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from scripts import install_kv_ai_memory_universal_intr_route as installer

ROOT = Path(__file__).resolve().parents[1]
ROUTER_REL = Path("workers/universal_intr_profiled_ingress.py")


def prepare(source_root: Path, *, check: bool = False) -> dict[str, object]:
    source = source_root.expanduser().resolve()
    router = source / ROUTER_REL
    if not router.is_file():
        raise RuntimeError("shared_universal_intr_router_missing")
    before = router.read_text(encoding="utf-8")
    after = installer.transform(before)
    changed = after != before
    if check:
        if changed:
            raise RuntimeError("kv_ai_memory_route_not_installed")
        state = "ROUTE_ALREADY_INSTALLED"
    else:
        if changed:
            router.write_text(after, encoding="utf-8")
            if router.read_text(encoding="utf-8") != after:
                raise RuntimeError("kv_ai_memory_route_readback_mismatch")
            state = "ROUTE_INSTALLED_LOCAL_SOURCE"
        else:
            state = "ROUTE_ALREADY_INSTALLED"
    return {
        "schema": "stegverse.kv.ai-memory-intr-runtime-source-preparation/v1",
        "state": state,
        "task_id": "SV-KV-AI-PERSISTENCE-001",
        "router_ref": ROUTER_REL.as_posix(),
        "source_changed": changed and not check,
        "listener_started": False,
        "transport_event_observed": False,
        "intr_admission_observed": False,
        "worker_claim_or_fence_minted": False,
        "provider_execution_observed": False,
        "kv_writeback_observed": False,
        "credential_material_present": False,
        "authority_effect": "NONE_SOURCE_PREPARATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    import json
    print(json.dumps(prepare(args.source_root, check=args.check), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
