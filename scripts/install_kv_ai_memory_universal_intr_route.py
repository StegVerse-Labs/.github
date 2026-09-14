#!/usr/bin/env python3
"""Install KV AI memory routing into the existing shared Universal InTr ingress."""
from __future__ import annotations

import argparse
from pathlib import Path

PROFILE_IMPORT = 'from workers import kv_ai_memory_intr_profile as kv_ai_memory_intr  # noqa: E402\n'
TRANSPORT_IMPORT = 'from workers import kv_ai_memory_intr_transport as kv_ai_memory_intr_transport  # noqa: E402\n'
IMPORT_ANCHOR = 'from workers import erl_active_research_intr_profile as erl_active_research  # noqa: E402\n'
PROFILE_TOKEN = '"KV:AI-MemoryPacketAdmission"'
ROUTE_ANCHOR = 'hil.admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers)'
ROUTE = 'kv_ai_memory_intr.admit(runtime_root=self.server.runtime_root, payload=payload, transport_payload_sha256=kv_ai_memory_intr_transport.validate_headers(self.headers, body)["payload_sha256_uri"]) if kv_ai_memory_intr.is_kv_ai_memory_submission(payload) else ' + ROUTE_ANCHOR


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def transform(source: str) -> str:
    result = source
    if PROFILE_IMPORT not in result:
        require(IMPORT_ANCHOR in result, "shared ERL import anchor missing")
        result = result.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + PROFILE_IMPORT + TRANSPORT_IMPORT, 1)
    elif TRANSPORT_IMPORT not in result:
        result = result.replace(PROFILE_IMPORT, PROFILE_IMPORT + TRANSPORT_IMPORT, 1)

    if PROFILE_TOKEN not in result:
        marker = '"profiles": ['
        start = result.find(marker)
        require(start >= 0, "profile list anchor missing")
        end = result.find('],', start)
        require(end >= 0, "profile list terminator missing")
        segment = result[start:end]
        require('"KV:KnowledgeVaultInterlock"' in segment, "KV shared profile invariant missing")
        result = result[:end] + ', ' + PROFILE_TOKEN + result[end:]

    if 'kv_ai_memory_intr.admit(' not in result:
        require(result.count(ROUTE_ANCHOR) == 1, "shared fallback route anchor drift")
        result = result.replace(ROUTE_ANCHOR, '(' + ROUTE + ')', 1)

    require(PROFILE_IMPORT in result, "memory profile import not installed")
    require(TRANSPORT_IMPORT in result, "memory transport import not installed")
    require(PROFILE_TOKEN in result, "memory profile token not installed")
    require('kv_ai_memory_intr.admit(' in result, "memory route not installed")
    require('ThreadingHTTPServer' in result, "shared listener invariant missing")
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
        require(transformed == source, "KV AI memory route is not installed/normalized")
        print("PASS: KV AI memory route already installed in shared Universal InTr ingress")
        return 0
    if transformed != source:
        path.write_text(transformed, encoding="utf-8")
        print("INSTALLED: KV AI memory route into existing shared Universal InTr ingress")
    else:
        print("NOOP: KV AI memory route already installed")
    print("NONCLAIM: route installation does not prove live packet admission")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
