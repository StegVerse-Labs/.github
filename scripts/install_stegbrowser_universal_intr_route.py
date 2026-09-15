#!/usr/bin/env python3
"""Install StegBrowser routing into the existing shared Universal InTr listener.

Source transformation only. It creates no listener, runtime, scheduler,
WorkerCoordinator, device dependency, or authority path.
"""
from __future__ import annotations
import argparse
from pathlib import Path

IMPORT_BLOCK = '''from workers.stegbrowser_intr_materialization_ingress import (  # noqa: E402\n    admit as admit_stegbrowser,\n    is_stegbrowser,\n)\n'''
PROFILE_TOKEN = '"StegBrowser:ManifestIngress"'
ROUTE_MARKER = "is_stegbrowser(payload)"


def require(ok: bool, reason: str) -> None:
    if not ok: raise SystemExit("FAIL_CLOSED: " + reason)


def _add_import(source: str) -> str:
    if IMPORT_BLOCK in source: return source
    anchors = ["from workers.canonical_work_intr_ingress import (", "from workers.sv002_intr_materialization_consumer import ("]
    for anchor in anchors:
        pos = source.find(anchor)
        if pos < 0: continue
        end = source.find(")\n", pos)
        require(end >= 0, "shared ingress import anchor drift")
        end += 2
        return source[:end] + IMPORT_BLOCK + source[end:]
    raise SystemExit("FAIL_CLOSED: shared ingress import anchor drift")


def _add_profile(source: str) -> str:
    if PROFILE_TOKEN in source: return source
    lines = source.splitlines(keepends=True); candidates=[]
    for i,line in enumerate(lines):
        if '"profiles": [' in line and '],' in line: candidates.append(i)
    require(len(candidates)==1, "shared ingress profile-list anchor drift")
    i=candidates[0]; line=lines[i]; pos=line.rfind('],'); require(pos>=0,"shared ingress profile-list anchor drift")
    lines[i]=line[:pos]+', '+PROFILE_TOKEN+line[pos:]
    return ''.join(lines)


def _add_route(source: str) -> str:
    if ROUTE_MARKER in source: return source
    lines=source.splitlines(keepends=True); candidates=[]
    for i,line in enumerate(lines):
        stripped=line.lstrip()
        if stripped.startswith("receipt = ") and "payload" in stripped and "admit_" in stripped: candidates.append(i)
    require(len(candidates)==1, "shared ingress router expression anchor drift")
    i=candidates[0]; line=lines[i]; indent=line[:len(line)-len(line.lstrip())]; newline="\n" if line.endswith("\n") else ""; expr=line.strip()[len("receipt = "):]
    lines[i]=indent+"receipt = admit_stegbrowser(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if is_stegbrowser(payload) else ("+expr+")"+newline
    return ''.join(lines)


def transform(source: str) -> str:
    result=_add_import(source); result=_add_profile(result); result=_add_route(result)
    require(IMPORT_BLOCK in result,"stegbrowser adapter import not installed")
    require(PROFILE_TOKEN in result,"stegbrowser profile not installed")
    require(ROUTE_MARKER in result,"stegbrowser route not installed")
    require(result.count("ThreadingHTTPServer") >= 1,"existing shared listener anchor missing")
    require("stegbrowser_intr_materialization_ingress" in result,"stegbrowser adapter binding missing")
    return result


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--router",default="workers/universal_intr_profiled_ingress.py"); p.add_argument("--check",action="store_true"); args=p.parse_args()
    path=Path(args.router); source=path.read_text(encoding="utf-8"); transformed=transform(source)
    if args.check:
        require(transformed==source,"stegbrowser route is not installed"); print("PASS: StegBrowser route already installed in shared Universal InTr ingress"); return 0
    if transformed!=source: path.write_text(transformed,encoding="utf-8"); print("INSTALLED: StegBrowser route into existing shared Universal InTr ingress")
    else: print("NOOP: StegBrowser route already installed")
    print("NONCLAIM: source routing does not prove authentic InTr admission, runtime materialization, claim/fence, or A4 ingress")
    return 0

if __name__=="__main__": raise SystemExit(main())
