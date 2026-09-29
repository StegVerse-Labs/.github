#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from workers.shwp_manifest_intr_event_bootstrap import ROOT, run_cycle

def main() -> int:
    p=argparse.ArgumentParser(description="Invoke canonical SHWP through one event-ephemeral shared Universal InTr cycle.")
    p.add_argument("--source-root",type=Path,default=ROOT)
    p.add_argument("--runtime-root",type=Path,required=True)
    a=p.parse_args()
    result=run_cycle(a.source_root,a.runtime_root)
    print(json.dumps(result,sort_keys=True))
    return 0 if result.get("disposition")=="ALLOW" else 1

if __name__=="__main__":
    raise SystemExit(main())
