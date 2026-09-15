#!/usr/bin/env python3
"""Install StegBrowser routing into the existing shared Universal InTr ingress.

Source transformation only. It must not create another listener, runtime,
scheduler, dispatcher, materializer, WorkerCoordinator, transport, or authority.
"""
from __future__ import annotations

import argparse
from pathlib import Path

IMPORT_BLOCK = '''from workers.stegbrowser_intr_materialization_ingress import (  # noqa: E402\n    admit as admit_stegbrowser,\n    is_stegbrowser,\n)\n'''
SV002_IMPORT_END = '''from workers.sv002_intr_materialization_consumer import (  # noqa: E402\n    DESTINATION as SV002_DESTINATION,\n    DOWNSTREAM_OWNER as SV002_OWNER,\n    scrubbed_env as sv002_scrubbed_env,\n    validate_request as validate_sv002_request,\n)\n'''
PROFILE_TOKEN = '"StegBrowser:ManifestInvocation"'
ROUTE_MARKER = "is_stegbrowser(payload)"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def _add_profile(source: str) -> str:
    if PROFILE_TOKEN in source:
        return source
    lines = source.splitlines(keepends=True)
    candidates = [i for i, line in enumerate(lines) if '"profiles": [' in line and '],' in line]
    require(len(candidates) == 1, "profile-list anchor drift")
    i = candidates[0]
    line = lines[i]
    pos = line.rfind('],')
    require(pos >= 0, "profile-list anchor drift")
    lines[i] = line[:pos] + ', ' + PROFILE_TOKEN + line[pos:]
    return ''.join(lines)


def _add_route(source: str) -> str:
    if ROUTE_MARKER in source:
        return source
    lines = source.splitlines(keepends=True)
    candidates = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("receipt = ") and "payload" in stripped and "admit_" in stripped:
            candidates.append(i)
    require(len(candidates) == 1, "router expression anchor drift")
    i = candidates[0]
    line = lines[i]
    indent = line[: len(line) - len(line.lstrip())]
    newline = "\n" if line.endswith("\n") else ""
    expr = line.strip()[len("receipt = "):]
    lines[i] = indent + "receipt = admit_stegbrowser(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if is_stegbrowser(payload) else (" + expr + ")" + newline
    return ''.join(lines)


def transform(source: str) -> str:
    result = source
    if IMPORT_BLOCK not in result:
        require(SV002_IMPORT_END in result, "sv002 import anchor drift")
        result = result.replace(SV002_IMPORT_END, SV002_IMPORT_END + IMPORT_BLOCK, 1)
    result = _add_profile(result)
    result = _add_route(result)
    require(IMPORT_BLOCK in result, "stegbrowser import not installed")
    require(PROFILE_TOKEN in result, "stegbrowser profile not installed")
    require(ROUTE_MARKER in result, "stegbrowser route not installed")
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
        require(transformed == source, "stegbrowser route is not installed")
        print("PASS: StegBrowser route already installed in shared Universal InTr ingress")
        return 0
    if transformed != source:
        path.write_text(transformed, encoding="utf-8")
        print("INSTALLED: StegBrowser route into existing shared Universal InTr ingress")
    else:
        print("NOOP: StegBrowser route already installed")
    print("NONCLAIM: source routing does not prove authentic InTr ingress or runtime execution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
