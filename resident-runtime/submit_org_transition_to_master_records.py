#!/usr/bin/env python3
import argparse,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("org_kernel",ROOT/"org-kernel/kernel.py")
K=importlib.util.module_from_spec(spec);spec.loader.exec_module(K)
RETRY="resident-runtime/submit_org_transition_to_master_records.py (--org-receipt, --standing)"
def load(p,argument="input"):return K.cli_input_json(p,argument,retry_entrypoint=RETRY)
def org_ledger():return K._own_module("submit_organization_ledger","resident-runtime/aggregate_repo_transition.py")
def main():
 p=argparse.ArgumentParser();p.add_argument("--org-receipt",required=True);p.add_argument("--predecessor-ecosystem-state-sha256",required=True);p.add_argument("--successor-ecosystem-state-sha256",required=True);p.add_argument("--relation-evidence-json",default="{}")
 # Standing is declared, never derived here. The ecosystem-state digests above
 # chain this lane; the contract's own finding refuses to equate lane-local
 # chaining with cross-lane predecessor standing, so they are not reused as a
 # predecessor binding. There is no default: a silent one would be the
 # defaulting the contract forbids.
 p.add_argument("--standing",required=True,help="JSON file declaring mode, node_ref and the predecessor key")
 # The mesh is supplied by whatever materialized this node, never derived from
 # the host: a frame published under one host's home is lost with it.
 p.add_argument("--mesh-root",type=Path,default=None,help="federation mesh this node was materialized with")
 a=p.parse_args()
 if a.mesh_root is None:
  print(json.dumps({"status":"NOT_PUBLISHED","disposition":"FAIL_CLOSED","failed_predicate":"MESH_LOCATION_REQUIRED_FROM_MATERIALIZER","required_evidence_or_repair":"materialize this node with --mesh-root","retry_entrypoint":"resident-runtime/submit_org_transition_to_master_records.py::main","consequence_committed":False,"authority_effect":"NONE_REFUSAL_ONLY"},sort_keys=True));raise SystemExit(1)
 receipt=load(a.org_receipt,"--org-receipt")
 if receipt.get("schema")!="stegverse.organization-transition-receipt/v1":raise SystemExit("organization receipt schema mismatch")
 if receipt.get("organization")!="StegVerse-Labs":raise SystemExit("organization receipt owner mismatch")
 # Before anything is built or published (VALIDATOR row 4): the receipt is this
 # organization ledger's own -- its self-hash holds and it is, byte-for-byte,
 # the receipt reachable from the ledger's HEAD -- and its reference is not a
 # CARRIED or incoherent one (kernel.refuse_reference). A refusal publishes 0 frames.
 refused=org_ledger().organization_receipt_ledger_refusal(receipt,retry_entrypoint=RETRY)
 if refused is not None:print(json.dumps(refused,sort_keys=True));return 1
 K.refuse_reference(receipt.get("hb_reference"))
 payload={"operation":"ORGANIZATION_RECORD_ORGANIZATION_TRANSITION","organization_receipt":receipt,"predecessor_ecosystem_state_sha256":a.predecessor_ecosystem_state_sha256,"successor_ecosystem_state_sha256":a.successor_ecosystem_state_sha256,"relation_evidence":K.cli_json_text(a.relation_evidence_json,"--relation-evidence-json",retry_entrypoint="resident-runtime/submit_org_transition_to_master_records.py (--org-receipt, --standing)"),"authority_transfer":False}
 standing=load(a.standing,"--standing")
 if not isinstance(standing,dict) or "predecessor" not in standing:raise SystemExit("standing must declare the predecessor key; null is explicit genesis")
 # Stamped with the epoch of the receipt it carries when that epoch is CARRIED
 # (derived_from_clock false and passing the shared rule), so submitting the
 # same receipt again publishes the same frame -- a write-once no-op. A
 # clock-derived receipt epoch is never re-stamped as supplied: the frame then
 # takes the kernel's marked default (derived_from_clock true).
 ref=receipt.get("hb_reference") if isinstance(receipt.get("hb_reference"),dict) else {}
 carried=ref.get("derived_from_clock") is False and K.supplied_epoch_failure(ref.get("epoch"),ref) is None
 if carried:payload["hb_provenance"]={"source":"CARRIED:ORGANIZATION_RECEIPT","receipt_sha256":receipt.get("receipt_sha256"),"derived_from_clock":False}
 packet=K.build_packet(origin_org="StegVerse-Labs",origin_service="stegverse-labs.org-control",destination_org="master-records",destination_service="organization.ecosystem-transition-ledger",payload=payload,standing=standing,transition_reference="ecosystem.transition.organization-record.v1",authority_effect="NONE")
 published=K.publish_packet(packet,root=a.mesh_root,epoch=int(str(ref["epoch"])) if carried else None)
 print(json.dumps({"status":"PUBLISHED_FOR_ORGANIZATION_RECORD","packet_id":packet["packet_id"],"frame_sha256":published["frame"]["frame_sha256"],"authority_effect":"NONE"},sort_keys=True))
if __name__=="__main__":raise SystemExit(K.run_writer_cli(lambda:main() or 0,retry_entrypoint=RETRY))
