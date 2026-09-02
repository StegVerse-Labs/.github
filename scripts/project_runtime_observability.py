#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("runtime_observability",ROOT/"org-kernel/runtime_observability.py")
obs=importlib.util.module_from_spec(spec); spec.loader.exec_module(obs)

def main()->int:
    p=argparse.ArgumentParser(description="Project shared HB/runtime observability without inferring runtime activation.")
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--max-observer-age-seconds",type=int,default=30)
    p.add_argument("--write",type=Path,default=None)
    args=p.parse_args()
    value=obs.snapshot(args.root,max_observer_age_seconds=args.max_observer_age_seconds)
    text=json.dumps(value,indent=2,sort_keys=True)+"\n"
    if args.write is not None:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        args.write.write_text(text,encoding="utf-8")
    print(text,end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
