#!/usr/bin/env python3
"""Install CanonicalWork routing into the existing Universal InTr ingress source.

This is a source transformation only. It MUST NOT start a second listener,
heartbeat, oscillator, scheduler, or WorkerCoordinator. The transformation is
idempotent and fails closed if the expected existing router anchors drift.
"""
from __future__ import annotations

import argparse
from pathlib import Path

IMPORT_BLOCK = '''from workers.canonical_work_intr_ingress import (  # noqa: E402\n    admit as admit_canonical_work,\n    is_canonical_work,\n)\n'''

SV002_IMPORT_END = '''from workers.sv002_intr_materialization_consumer import (  # noqa: E402\n    DESTINATION as SV002_DESTINATION,\n    DOWNSTREAM_OWNER as SV002_OWNER,\n    scrubbed_env as sv002_scrubbed_env,\n    validate_request as validate_sv002_request,\n)\n'''

OLD_PROFILES = '"profiles": ["HIL:Ingress", "SV002:PublicObservation", "KV:KnowledgeVaultInterlock", "KV:SKAPCiphertextCustody", "Publisher:ArtifactTransfer", "KV:PublisherArtifactImport"],'
NEW_PROFILES = '"profiles": ["HIL:Ingress", "SV002:PublicObservation", "KV:KnowledgeVaultInterlock", "KV:SKAPCiphertextCustody", "Publisher:ArtifactTransfer", "KV:PublisherArtifactImport", "CanonicalWork:Coordination"],'

OLD_ROUTE = '''receipt = admit_kv_publisher_return(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_kv_publisher_return(payload) else (admit_publisher(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_publisher(payload) else (admit_kv_skap(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_kv_skap(payload) else (admit_device_kv(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_device_kv(payload) else (admit_sv002(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_sv002(payload) else hil.admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers)))))'''
NEW_ROUTE = '''receipt = admit_canonical_work(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if is_canonical_work(payload) else (admit_kv_publisher_return(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_kv_publisher_return(payload) else (admit_publisher(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_publisher(payload) else (admit_kv_skap(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_kv_skap(payload) else (admit_device_kv(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_device_kv(payload) else (admit_sv002(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_sv002(payload) else hil.admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers))))))'''


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def transform(source: str) -> str:
    already_import = IMPORT_BLOCK in source
    already_profile = NEW_PROFILES in source
    already_route = NEW_ROUTE in source
    if already_import and already_profile and already_route:
        return source

    result = source
    if not already_import:
        require(SV002_IMPORT_END in result, "sv002 import anchor drift")
        result = result.replace(SV002_IMPORT_END, SV002_IMPORT_END + IMPORT_BLOCK, 1)
    if not already_profile:
        require(OLD_PROFILES in result, "profile-list anchor drift")
        result = result.replace(OLD_PROFILES, NEW_PROFILES, 1)
    if not already_route:
        require(OLD_ROUTE in result, "router expression anchor drift")
        result = result.replace(OLD_ROUTE, NEW_ROUTE, 1)

    require(IMPORT_BLOCK in result, "canonical-work import not installed")
    require(NEW_PROFILES in result, "canonical-work profile not installed")
    require(NEW_ROUTE in result, "canonical-work route not installed")
    require(result.count("ThreadingHTTPServer") >= 1, "existing shared listener anchor missing")
    require("canonical_work_intr_ingress" in result, "canonical-work adapter binding missing")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--router", default="workers/universal_intr_profiled_ingress.py")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = Path(args.router)
    source = path.read_text(encoding="utf-8")
    transformed = transform(source)
    if args.check:
        require(transformed == source, "canonical-work route is not installed")
        print("PASS: canonical-work route already installed in shared Universal InTr ingress")
        return 0
    if transformed != source:
        path.write_text(transformed, encoding="utf-8")
        print("INSTALLED: canonical-work route into existing Universal InTr ingress")
    else:
        print("NOOP: canonical-work route already installed")
    print("NONCLAIM: source routing does not prove authentic InTr ingress or runtime execution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
