#!/usr/bin/env python3
"""Install ERL active-research routing into the existing Universal InTr ingress."""
from __future__ import annotations

import argparse
from pathlib import Path

IMPORT_BLOCK = 'from workers import erl_active_research_intr_profile as erl_active_research  # noqa: E402\n'
TRANSPORT_IMPORT = 'from workers import erl_active_research_transport as erl_active_research_transport  # noqa: E402\n'
IMPORT_ANCHOR = '''from workers.sv002_intr_materialization_consumer import (  # noqa: E402\n    DESTINATION as SV002_DESTINATION,\n    DOWNSTREAM_OWNER as SV002_OWNER,\n    scrubbed_env as sv002_scrubbed_env,\n    validate_request as validate_sv002_request,\n)\n'''
PROFILE_TOKEN = '"ERL:ActiveResearch"'
FALLBACK_ROUTE = 'hil.admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers)'
OLD_HASH_EXPR = 'transport_payload_sha256=hil.validate_transport_headers(self.headers, body)["payload_sha256"]'
LEGACY_RELAY_HASH_EXPR = 'transport_payload_sha256="sha256:"+hil.validate_transport_headers(self.headers, body)["payload_sha256"]'
PROFILE_HASH_EXPR = 'transport_payload_sha256=erl_active_research_transport.validate_headers(self.headers, body)["payload_sha256_uri"]'
OLD_ERL_ROUTE = 'erl_active_research.admit(runtime_root=self.server.runtime_root, payload=payload, ' + OLD_HASH_EXPR + ') if erl_active_research.is_erl_active_research(payload) else ' + FALLBACK_ROUTE
LEGACY_RELAY_ROUTE = 'erl_active_research.admit(runtime_root=self.server.runtime_root, payload=payload, ' + LEGACY_RELAY_HASH_EXPR + ') if erl_active_research.is_erl_active_research(payload) else ' + FALLBACK_ROUTE
ERL_ROUTE = 'erl_active_research.admit(runtime_root=self.server.runtime_root, payload=payload, ' + PROFILE_HASH_EXPR + ') if erl_active_research.is_erl_active_research(payload) else ' + FALLBACK_ROUTE


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def transform(source: str) -> str:
    result = source
    if IMPORT_BLOCK not in result:
        require(IMPORT_ANCHOR in result, "sv002 import anchor drift")
        result = result.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_BLOCK, 1)
    if TRANSPORT_IMPORT not in result:
        require(IMPORT_BLOCK in result, "erl import anchor missing")
        result = result.replace(IMPORT_BLOCK, IMPORT_BLOCK + TRANSPORT_IMPORT, 1)
    if PROFILE_TOKEN not in result:
        marker = '"profiles": ['
        start = result.find(marker)
        require(start >= 0, "profile-list anchor missing")
        end = result.find('],', start)
        require(end >= 0, "profile-list terminator missing")
        segment = result[start:end]
        require('"HIL:Ingress"' in segment and '"SV002:PublicObservation"' in segment, "shared profile invariants missing")
        result = result[:end] + ', ' + PROFILE_TOKEN + result[end:]
    if OLD_HASH_EXPR in result:
        require(result.count(OLD_HASH_EXPR) == 1, "legacy ERL payload digest anchor drift")
        result = result.replace(OLD_HASH_EXPR, PROFILE_HASH_EXPR, 1)
    elif LEGACY_RELAY_HASH_EXPR in result:
        require(result.count(LEGACY_RELAY_HASH_EXPR) == 1, "legacy relay ERL digest anchor drift")
        result = result.replace(LEGACY_RELAY_HASH_EXPR, PROFILE_HASH_EXPR, 1)
    elif 'erl_active_research.admit(' not in result:
        require(result.count(FALLBACK_ROUTE) == 1, "shared router fallback anchor drift")
        result = result.replace(FALLBACK_ROUTE, '(' + ERL_ROUTE + ')', 1)
    require(IMPORT_BLOCK in result, "erl import not installed")
    require(TRANSPORT_IMPORT in result, "erl transport import not installed")
    require(PROFILE_TOKEN in result, "erl profile token not installed")
    require('erl_active_research.admit(' in result, "erl route not installed")
    require(PROFILE_HASH_EXPR in result, "erl resident-local transport validator not installed")
    require(OLD_HASH_EXPR not in result and LEGACY_RELAY_HASH_EXPR not in result, "legacy ERL transport validation retained")
    require(result.count("ThreadingHTTPServer") >= 1, "existing shared listener anchor missing")
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
        require(transformed == source, "ERL active-research route is not installed/normalized")
        print("PASS: ERL active-research resident-local route already installed in shared Universal InTr ingress")
        return 0
    if transformed != source:
        path.write_text(transformed, encoding="utf-8")
        print("INSTALLED: ERL active-research resident-local route into existing Universal InTr ingress")
    else:
        print("NOOP: ERL active-research resident-local route already installed")
    print("NONCLAIM: source routing does not prove authentic three-hop runtime traversal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
