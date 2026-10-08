#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("org_kernel",ROOT/"org-kernel"/"kernel.py")
K=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(K)

def mesh_refusal(org:str, cmd:str)->dict:
    """The command's own disposition when its materializer supplied no mesh.

    Nothing is published or read: the mesh is supplied, never derived from the
    host this happens to run on.
    """
    return {"organization":org,"command":cmd,"disposition":"FAIL_CLOSED",
            "failed_predicate":"MESH_LOCATION_REQUIRED_FROM_MATERIALIZER",
            "required_evidence_or_repair":"materialize this node with --mesh-root",
            "retry_entrypoint":"resident-runtime/ecosystem_control.py::main",
            "consequence_committed":False,"authority_effect":"NONE_REFUSAL_ONLY"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mesh-root",type=Path,default=None,help="federation mesh this node was materialized with")
    sub=ap.add_subparsers(dest="cmd",required=True)
    for name,cls in (("send-monitor","ecosystem.monitor.request"),("send-work","ecosystem.work.request"),("send-message","ecosystem.communication")):
        p=sub.add_parser(name)
        p.add_argument("--subject",required=True)
        p.add_argument("--body-json",required=True)
        p.add_argument("--requested-action")
        p.add_argument("--communication-id")
        # Declared, never defaulted: every ingress class requires canonical
        # node standing, and a default would be a caller-editable claim.
        p.add_argument("--standing",type=Path,required=True,help="JSON file declaring mode, node_ref and the predecessor key")
        p.set_defaults(message_class=cls)
    p=sub.add_parser("collect")
    p.add_argument("--communication-id",required=True)
    sub.add_parser("status")
    args=ap.parse_args()
    reg=K.load_registry(ROOT)
    org=reg["organization"]
    if args.cmd=="status":
        print(json.dumps(K.resident_status(ROOT),indent=2,sort_keys=True))
        return
    # The kernel's publish over the supplied mesh is the only carrier; there is
    # no hosted gateway path whose reachability a crossing would depend on.
    if args.mesh_root is None:
        print(json.dumps(mesh_refusal(org,args.cmd),indent=2,sort_keys=True))
        raise SystemExit(1)
    if args.cmd=="collect":
        result=K.collect_ecosystem_responses(org,args.communication_id,mesh_root=args.mesh_root)
        print(json.dumps(result,indent=2,sort_keys=True))
        return
    body=json.loads(args.body_json)
    out=K.publish_ecosystem_from_directory(
        ROOT,
        standing=json.loads(args.standing.read_text()),
        message_class=args.message_class,
        subject=args.subject,
        body=body,
        requested_action=args.requested_action,
        communication_id=args.communication_id,
        mesh_root=args.mesh_root
    )
    print(json.dumps({
      "status":"PUBLISHED",
      "organization":org,
      "communication_id":out["communication_id"],
      "published_count":out["published_count"]
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
