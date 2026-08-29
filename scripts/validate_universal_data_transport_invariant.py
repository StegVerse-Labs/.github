#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/"management"/"UNIVERSAL_DATA_TRANSPORT_INVARIANT.json"

EXPECTED_STACK=["SKAP_VAULT","KV","DEVICE_SYSTEM","STEGOS_ECOSYSTEM","EXTERNAL_SYSTEM"]

def validate(p:dict)->list[str]:
    f=[]
    if p.get("schema")!="stegverse.universal-data-transport-invariant/v1": f.append("schema")
    if p.get("state")!="CANONICAL_POLICY_ADOPTED_RUNTIME_ROLLOUT_ACTIVE": f.append("state")
    if p.get("canonical_boundary_stack")!=EXPECTED_STACK: f.append("boundary_stack")
    expected={
      "directionality":"BIDIRECTIONAL",
      "adjacent_hops_only":True,
      "transport_protocol":"InTr",
      "interlock_required_per_hop":True,
      "receipt_required_per_completed_hop":True,
      "receipt_hash_chain_required":True,
      "payload_plaintext_in_receipts":False,
      "authority_transfer_by_transport":False,
      "credential_authority":"TV/TVC",
      "event_triggered_transport":True,
      "always_on_application_receiver_required":False,
      "second_user_device_required":False,
      "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
      "exact_packet_transport_retry_allowed":True,
      "blind_consequence_retry_allowed":False,
      "direct_non_adjacent_transport":False,
      "direct_cross_boundary_state_mutation":False,
      "transport_availability_grants_execution_authority":False,
      "runtime_activation_claimed":False
    }
    for k,v in expected.items():
        if p.get(k)!=v: f.append(k)
    if not str(p.get("implementation_ref") or "").endswith("universal_intr_transport.py"): f.append("implementation_ref")
    return f

def main()->int:
    p=json.loads(POLICY.read_text(encoding="utf-8"))
    failures=validate(p)
    if failures:
        print("UNIVERSAL_DATA_TRANSPORT_INVARIANT_FAIL")
        for x in failures: print("-",x)
        return 1
    print("UNIVERSAL_DATA_TRANSPORT_INVARIANT_PASS")
    print("BOUNDARY_STACK="+"<->".join(EXPECTED_STACK))
    print("TRANSPORT=InTr")
    print("INTERLOCK_PER_HOP=true")
    print("EVENT_TRIGGERED=true")
    print("ALWAYS_ON_APPLICATION_RECEIVER_REQUIRED=false")
    print("SECOND_USER_DEVICE_REQUIRED=false")
    print("EXACT_PACKET_TRANSPORT_RETRY_ALLOWED=true")
    print("BLIND_CONSEQUENCE_RETRY_ALLOWED=false")
    print("RUNTIME_ACTIVATION_CLAIMED=false")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
