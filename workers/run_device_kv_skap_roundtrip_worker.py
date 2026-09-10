#!/usr/bin/env python3
"""WorkerCoordinator entrypoint for the Device <-> KV <-> SKAP roundtrip verifier."""
from __future__ import annotations

import json
import os
from pathlib import Path

from workers.device_kv_skap_roundtrip_verifier import HOSTED_ENV, _load_json, verify_manifest


def required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_required")
    return Path(value)


def main() -> int:
    if any(os.environ.get(name) for name in HOSTED_ENV):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:hosted_runtime_forbidden")
    runtime_root = required_path("STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT")
    manifest_path = required_path("STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_MANIFEST")
    output = required_path("STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT")
    manifest = _load_json(manifest_path, "manifest")
    proof = verify_manifest(manifest, runtime_root=runtime_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(proof, sort_keys=True, indent=2) + "\n"
    if output.exists() and output.read_text(encoding="utf-8") != raw:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:write_once_collision")
    output.write_text(raw, encoding="utf-8")
    print(json.dumps(proof, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
