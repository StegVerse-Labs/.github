#!/usr/bin/env python3
"""Dispatch the resident cycle from a committed request (COMMITTED_REQUEST, row 16).

The request is a file committed at REQUEST_PATH. A push that changes it is the
dispatch (.github/workflows/resident-cycle-request.yml), and the cycle's epoch
is the one the request carries. There are no workflow inputs: nothing handed to
a run at dispatch time reaches the cycle, so the epoch is in git before the
cycle reads it. An absent, unreadable or wrongly shaped request is the terminal
six-field CLI_INPUT_INVALID; an epoch the kernel's shared rule refuses is its
six-field FAIL_CLOSED. Either way nothing is consumed.

The request names no location: the mesh, node state and ledgers are supplied by
the node materializer, and federation_cycle reads them as it always has.
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("org_kernel",ROOT/"org-kernel"/"kernel.py")
K=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(K)

REQUEST_PATH=".stegverse/resident-cycle/request.json"
SCHEMA="stegverse.resident-cycle-request/v1"
RETRY_ENTRYPOINT="commit "+REQUEST_PATH+" carrying hb_epoch, then resident-runtime/resident_cycle_request.py"

def _cycle():
    spec=importlib.util.spec_from_file_location("federation_cycle",ROOT/"resident-runtime"/"federation_cycle.py")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def request_epoch(path:Path)->str:
    """The epoch a committed request carries, or CliInputRefused for a malformed request."""
    request=K.cli_input_json(path,"--request",retry_entrypoint=RETRY_ENTRYPOINT)
    if request.get("schema")!=SCHEMA or set(request)!={"schema","hb_epoch"}:
        raise K._cli_input_refused(ValueError("request is not exactly {schema: "+SCHEMA+", hb_epoch}"),
                                   "--request",RETRY_ENTRYPOINT)
    return request["hb_epoch"]

def main(argv:list[str]|None=None)->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--request",type=Path,default=ROOT/REQUEST_PATH,help="the committed resident cycle request")
    args,locations=ap.parse_known_args(argv)
    if any(a=="--hb-epoch" or a.startswith("--hb-epoch=") for a in locations):
        raise K._cli_input_refused(ValueError("the epoch comes from the committed request, not an argument"),
                                   "--hb-epoch",RETRY_ENTRYPOINT)
    epoch=request_epoch(args.request)
    refusal=K.writer_epoch_refusal(epoch,retry_entrypoint=RETRY_ENTRYPOINT)
    if refusal is not None:
        print(json.dumps(refusal,sort_keys=True)); return 1
    return _cycle().main([*locations,"--hb-epoch",str(epoch)])

if __name__=="__main__":
    raise SystemExit(K.run_writer_cli(main,retry_entrypoint="resident-runtime/resident_cycle_request.py"))
