#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, os
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

def supplied_ledger(variable:str)->Path|None:
    """A ledger location as this organization's materializer supplies it, or None.

    The same interface the repository and organization emitters read. The
    kernel never reads it; the cycle passes what it was given explicitly.
    """
    value=os.environ.get(variable)
    return Path(value).expanduser().resolve() if value else None

def organization_ledger()->object:
    """The kernel's own Organization ledger module: the one crossing custody appends through."""
    return K._own_module("crossing_organization_ledger","resident-runtime/aggregate_repo_transition.py")

def store_refusal(exc)->dict:
    """The declared Organization ledger was not admitted: FAIL_CLOSED before anything is read (OL-3).

    An explicit POSIX root under a declared non-posix store is
    ORGANIZATION_LEDGER_STORE_KIND_MISMATCH; a declared store this node was
    not materialized with keeps the store's own predicate.
    """
    return {"schema_version":"stegverse.org-federation-cycle-refusal.v1",
            "organization":K.load_registry(ROOT)["organization"],
            "disposition":"FAIL_CLOSED","failed_predicate":exc.failed_predicate,
            "required_evidence_or_repair":getattr(exc,"repair",None) or "materialize this node with "+exc.variable,
            "retry_entrypoint":"resident-runtime/federation_cycle.py::main",
            "consequence_committed":False,"authority_effect":"NONE_REFUSAL_ONLY"}

def declared_organization_ledger(org_ledger_root:Path|None)->Path|object|None:
    """The Organization ledger this cycle appends to, as the manifest declares it.

    An explicit root is a POSIX root, admitted only under a declared
    {store: posix}; under any other declaration it raises
    LedgerStoreKindMismatch before anything is read or appended (OL-3).
    Without one, a declared {store: posix} keeps the materializer's
    STEGVERSE_ORG_LEDGER_ROOT; any other declaration is the store
    organization_store() selects; one it cannot select raises its own
    LedgerLocationRequired.
    """
    org=organization_ledger()
    if org_ledger_root is not None:
        org.refuse_explicit_posix_root()
        return org_ledger_root
    locus=org.C.get(org.LEDGER_LOCUS_KEY)
    if not isinstance(locus,dict) or locus.get("store") in (None,"posix"):
        return supplied_ledger("STEGVERSE_ORG_LEDGER_ROOT")
    return org.organization_store()

def cycle(*, mesh_root:Path|None, node_state_root:Path|None,
          repo_ledger_root:Path|None=None, org_ledger_root:Path|None=None)->dict:
    if node_state_root is None:
        return location_refusal("NODE_STATE_LOCATION_REQUIRED_FROM_MATERIALIZER","--node-state-root")
    if mesh_root is None:
        return location_refusal("MESH_LOCATION_REQUIRED_FROM_MATERIALIZER","--mesh-root")
    repo_ledger_root=repo_ledger_root or supplied_ledger("STEGVERSE_REPO_LEDGER_ROOT")
    try:
        org_ledger_root=declared_organization_ledger(org_ledger_root)
    except organization_ledger().LedgerLocationRequired as exc:
        return store_refusal(exc)
    # Consuming a crossing is a transition within the organization, so it is
    # recorded on both ledgers before it is answered or marked. Without both
    # locations nothing is consumed: the frames stay in the mesh, which is the
    # durable queue, and the cycle says why.
    if repo_ledger_root is None or org_ledger_root is None:
        return location_refusal("LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER",
                                "--repo-ledger-root and --org-ledger-root")
    results=K.consume_and_respond(ROOT,mesh_root=mesh_root,node_state_root=node_state_root,
                                  repo_ledger_root=repo_ledger_root,org_ledger_root=org_ledger_root)
    consumed=sum(1 for x in results if (x.get("result") or {}).get("status")=="CONSUMED")
    responses=sum(1 for x in results if x.get("response_publication"))
    receipt={
      "schema_version":"stegverse.org-federation-cycle.v1",
      "organization":K.load_registry(ROOT)["organization"],
      "heartbeat_reference":K.hb_reference(),
      "frames_seen":len(results),
      "frames_consumed":consumed,
      "frames_refused":sum(1 for x in results if (x.get("result") or {}).get("status")=="REFUSED"),
      "organization_receipts_recorded":sum(1 for x in results if x.get("organization_record")),
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
    ap.add_argument("--repo-ledger-root",type=Path,default=None,
                    help="repository ledger root (else STEGVERSE_REPO_LEDGER_ROOT)")
    ap.add_argument("--org-ledger-root",type=Path,default=None,
                    help="organization ledger root, only under a declared {store: posix} "
                         "(else STEGVERSE_ORG_LEDGER_ROOT there, or the declared store)")
    args=ap.parse_args(argv)
    out=cycle(mesh_root=args.mesh_root,node_state_root=args.node_state_root,
              repo_ledger_root=args.repo_ledger_root,org_ledger_root=args.org_ledger_root)
    print(json.dumps(out,sort_keys=True))
    return 1 if out.get("disposition")=="FAIL_CLOSED" else 0

if __name__=="__main__":
    raise SystemExit(main())
