#!/usr/bin/env python3
"""Install StegBrowser materialization routing into the existing shared InTr listener.

Source transformation only: no listener, runtime, scheduler, WorkerCoordinator,
device, or authority path is created. Idempotent and composition-safe with the
other shared-listener profile installers.
"""
from __future__ import annotations

import argparse
from pathlib import Path

IMPORT_BLOCK = '''from workers.stegbrowser_intr_materialization_ingress import (  # noqa: E402\n    admit as admit_stegbrowser,\n    is_stegbrowser,\n)\n'''
PROFILE_TOKEN = '"StegBrowser:ManifestIngress"'
ROUTE_MARKER = "is_stegbrowser(payload)"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def transform(source: str) -> str:
    result = source
    if IMPORT_BLOCK not in result:
        anchor = 'PROFILE_PATH = "/intr/profile"\n'
        require(anchor in result, "shared-router import anchor drift")
        result = result.replace(anchor, IMPORT_BLOCK + "\n" + anchor, 1)

    if PROFILE_TOKEN not in result:
        lines = result.splitlines(keepends=True)
        candidates = [i for i, line in enumerate(lines) if '"profiles": [' in line and '],' in line]
        require(len(candidates) == 1, "profile-list anchor drift")
        i = candidates[0]
        pos = lines[i].rfind('],')
        require(pos >= 0, "profile-list anchor drift")
        lines[i] = lines[i][:pos] + ', ' + PROFILE_TOKEN + lines[i][pos:]
        result = ''.join(lines)

    if ROUTE_MARKER not in result:
        lines = result.splitlines(keepends=True)
        candidates = []
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("receipt = ") and "payload" in stripped and "admit_" in stripped:
                candidates.append(i)
        require(len(candidates) == 1, "router expression anchor drift")
        i = candidates[0]
        line = lines[i]
        indent = line[:len(line)-len(line.lstrip())]
        newline = "\n" if line.endswith("\n") else ""
        expr = line.strip()[len("receipt = "):]
        lines[i] = indent + "receipt = admit_stegbrowser(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if is_stegbrowser(payload) else (" + expr + ")" + newline
        result = ''.join(lines)

    require(IMPORT_BLOCK in result, "stegbrowser import not installed")
    require(PROFILE_TOKEN in result, "stegbrowser profile not installed")
    require(ROUTE_MARKER in result, "stegbrowser route not installed")
    require(result.count("ThreadingHTTPServer") >= 1, "existing shared listener anchor missing")
    require("class Server" in result or "ThreadingHTTPServer" in result, "shared listener implementation missing")
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
    print("NONCLAIM: source routing does not prove authentic InTr admission or runtime execution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
