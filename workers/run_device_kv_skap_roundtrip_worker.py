#!/usr/bin/env python3
"""WorkerCoordinator entrypoint for authentic Device <-> KV <-> SKAP continuation or proof verification."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

from workers.device_kv_skap_roundtrip_verifier import HOSTED_ENV, _load_json, verify_manifest

ROOT = Path(__file__).resolve().parents[1]


def required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_required")
    return Path(value)


def optional_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


def _load_continuation():
    path = ROOT / "scripts" / "continue_device_kv_skap_from_tvc_custody.py"
    spec = importlib.util.spec_from_file_location("device_kv_skap_tvc_continuation", path)
    if spec is None or spec.loader is None:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:continuation_loader_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_once(output: Path, value: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, sort_keys=True, indent=2) + "\n"
    if output.exists() and output.read_text(encoding="utf-8") != raw:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:write_once_collision")
    output.write_text(raw, encoding="utf-8")


def main() -> int:
    if any(os.environ.get(name) for name in HOSTED_ENV):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:hosted_runtime_forbidden")

    runtime_root = required_path("STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT")
    output = required_path("STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT")
    manifest_path = optional_path("STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_MANIFEST")
    gateway_sidecar = optional_path("STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR")
    tvc_drain_receipt = optional_path("STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT")
    stegos_root = optional_path("STEGVERSE_STEGOS_ROOT")

    continuation_inputs = [gateway_sidecar, tvc_drain_receipt, stegos_root]
    if any(continuation_inputs) and not all(continuation_inputs):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:incomplete_tvc_continuation_inputs")

    if all(continuation_inputs):
        continuation = _load_continuation()
        result = continuation.continue_roundtrip(
            runtime_root=runtime_root,
            stegos_root=stegos_root,
            gateway_sidecar_path=gateway_sidecar,
            tvc_drain_receipt_path=tvc_drain_receipt,
        )
        if result.get("state") != "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED":
            raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:continuation_not_verified")
        _write_once(output, result)
        print(json.dumps(result, sort_keys=True))
        return 0

    if manifest_path is None:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:manifest_or_tvc_continuation_required")

    manifest = _load_json(manifest_path, "manifest")
    proof = verify_manifest(manifest, runtime_root=runtime_root)
    _write_once(output, proof)
    print(json.dumps(proof, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
