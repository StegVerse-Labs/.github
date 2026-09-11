#!/usr/bin/env python3
"""Install StegSocials bounded-event routing into the existing Universal InTr listener.

This transforms only the existing shared listener source. It starts no second
listener/runtime/scheduler/heartbeat and is idempotent. It supports a runtime
copy that may already contain other route extensions such as CanonicalWork.
"""
from __future__ import annotations

import argparse
from pathlib import Path

IMPORT_BLOCK = '''from workers.stegsocials_bounded_intr_ingress import (  # noqa: E402\n    PROFILE as STEGSOCIALS_BOUNDED_PROFILE,\n    admit as admit_stegsocials_bounded,\n    is_stegsocials_bounded,\n)\n'''
IMPORT_ANCHOR = 'PROFILE_PATH = "/intr/profile"\n'
PROFILE_TOKEN = '"StegSocials:BoundedSocialIngress"'
ROUTE_MARKER = 'is_stegsocials_bounded(payload)'


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def add_profile(source: str) -> str:
    if PROFILE_TOKEN in source:
        return source
    lines = source.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if '"profiles": [' not in line:
            continue
        pos = line.rfind('],')
        require(pos >= 0, "profile-list anchor drift")
        lines[index] = line[:pos] + ', ' + PROFILE_TOKEN + line[pos:]
        return ''.join(lines)
    raise SystemExit("FAIL_CLOSED: profile-list anchor missing")


def add_route(source: str) -> str:
    if ROUTE_MARKER in source:
        return source
    lines = source.splitlines(keepends=True)
    candidates = []
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith('receipt = ') and 'admit_' in stripped and 'payload' in stripped:
            candidates.append(index)
    require(len(candidates) == 1, "router expression anchor drift")
    index = candidates[0]
    line = lines[index]
    indent = line[: len(line) - len(line.lstrip())]
    newline = '\n' if line.endswith('\n') else ''
    expr = line.strip()[len('receipt = '):]
    lines[index] = (
        indent
        + 'receipt = admit_stegsocials_bounded(runtime_root=self.server.runtime_root, body=body, headers=self.headers, transport_validator=hil.validate_transport_headers) '
        + 'if is_stegsocials_bounded(payload) else ('
        + expr
        + ')'
        + newline
    )
    return ''.join(lines)


def transform(source: str) -> str:
    result = source
    if IMPORT_BLOCK not in result:
        require(IMPORT_ANCHOR in result, "import anchor drift")
        result = result.replace(IMPORT_ANCHOR, IMPORT_BLOCK + "\n" + IMPORT_ANCHOR, 1)
    result = add_profile(result)
    result = add_route(result)
    require(IMPORT_BLOCK in result, "stegsocials bounded import not installed")
    require(PROFILE_TOKEN in result, "stegsocials bounded profile not installed")
    require(ROUTE_MARKER in result, "stegsocials bounded route not installed")
    require(result.count("ThreadingHTTPServer") >= 1, "existing shared listener anchor missing")
    require("admit_stegsocials_bounded" in result, "stegsocials bounded adapter binding missing")
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
        require(transformed == source, "StegSocials bounded route is not installed")
        print("PASS: StegSocials bounded route already installed in shared Universal InTr ingress")
        return 0
    if transformed != source:
        path.write_text(transformed, encoding="utf-8")
        print("INSTALLED: StegSocials bounded route into existing Universal InTr ingress")
    else:
        print("NOOP: StegSocials bounded route already installed")
    print("NONCLAIM: source routing does not prove authentic InTr ingress, SKAP materialization, provider publication, or KV mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
