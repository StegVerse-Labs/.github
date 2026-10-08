#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("org_kernel",ROOT/"org-kernel"/"kernel.py")
K=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(K)
# The carrier is the kernel's publish over the mesh this node was materialized
# with (org-runtime/interlock-intr.json). There is no hosted gateway path: a
# service that must be reachable for a frame to cross would make its liveness
# a transition predicate.
CARRIER="org-kernel/kernel.py::publish_packet"

def location_refusal(failed_predicate:str, option:str)->dict:
    """The cycle's own disposition when its materializer supplied no location.

    Nothing is consumed, published or recorded: the mesh and this node's state
    are supplied, never derived from the host this happens to run on.
    """
    return {"schema_version":"stegverse.org-federation-cycle-refusal.v1",
            "organization":K.load_registry(ROOT)["organization"],
            "disposition":"FAIL_CLOSED","failed_predicate":failed_predicate,
            "required_evidence_or_repair":"materialize this node with "+option,
            "retry_entrypoint":"resident-runtime/federation_cycle.py::main",
            "consequence_committed":False,"authority_effect":"NONE_REFUSAL_ONLY"}

def cycle(*, mesh_root:Path|None, node_state_root:Path|None)->dict:
    if node_state_root is None:
        return location_refusal("NODE_STATE_LOCATION_REQUIRED_FROM_MATERIALIZER","--node-state-root")
    if mesh_root is None:
        return location_refusal("MESH_LOCATION_REQUIRED_FROM_MATERIALIZER","--mesh-root")
    results=K.consume_and_respond(ROOT,mesh_root=mesh_root,node_state_root=node_state_root)
    consumed=sum(1 for x in results if (x.get("result") or {}).get("status")=="CONSUMED")
    responses=sum(1 for x in results if x.get("response_publication"))
    receipt={
      "schema_version":"stegverse.org-federation-cycle.v1",
      "organization":K.load_registry(ROOT)["organization"],
      "heartbeat_reference":K.hb_reference(),
      "frames_seen":len(results),
      "frames_consumed":consumed,
      "responses_emitted":responses,
      "authority_effect":"NONE_CARRIER_ONLY",
      "transport":"FEDERATION_MESH",
      "carrier":CARRIER
    }
    # Recorded in this node's own supplied state rather than the checkout, so a
    # run does not mutate committed space and every pass is kept.
    recorded=K.record_federation_cycle(receipt,root=node_state_root)
    return {**receipt,"recorded_at":str(recorded)}

def main(argv:list[str]|None=None)->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mesh-root",type=Path,default=None,help="federation mesh this node was materialized with")
    ap.add_argument("--node-state-root",type=Path,default=None,help="this node's own state root")
    args=ap.parse_args(argv)
    out=cycle(mesh_root=args.mesh_root,node_state_root=args.node_state_root)
    print(json.dumps(out,sort_keys=True))
    return 1 if out.get("disposition")=="FAIL_CLOSED" else 0

if __name__=="__main__":
    raise SystemExit(main())
