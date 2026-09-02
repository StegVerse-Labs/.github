#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("runtime_observability",ROOT/"org-kernel/runtime_observability.py")
obs=importlib.util.module_from_spec(spec); spec.loader.exec_module(obs)

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--runtime-root",type=Path,required=True)
    p.add_argument("--home",type=Path,default=Path.home())
    a=p.parse_args()
    bindings={
      "sv001_request_consumption":"receipts/sovereign-host/stegverse001-bounded-autonomy-request-consumption.latest.json",
      "sv001_autonomy_cycle":str(a.home/".stegverse/state/stegverse001-bounded-autonomy/receipts/latest.json"),
      "master_records_reconstruction":str(a.home/".stegverse/master-records/stegverse001-bounded-autonomy/receipts/stegverse001-bounded-autonomy/reconstruction.latest.json"),
      "sv002_disposition":str(a.home/".stegverse/state/sv002-adversarial-observation/receipts/stegverse001.latest.json")
    }
    snap=obs.snapshot(a.runtime_root,evidence_bindings=bindings)
    bound=obs.bind_lane(snap,lane_id="STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001",predicates={
      "resident_request_consumption":"sv001_request_consumption",
      "runtime_execution_completed":"sv001_autonomy_cycle",
      "reconstruction_proven":"master_records_reconstruction",
      "sv002_adversarial_disposition":"sv002_disposition"
    })
    print(json.dumps(bound,indent=2,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
