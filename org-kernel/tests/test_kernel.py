#!/usr/bin/env python3
import importlib.util, json, tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location("kernel","org-kernel/kernel.py"); k=importlib.util.module_from_spec(spec); spec.loader.exec_module(k)
with tempfile.TemporaryDirectory() as td:
 root=Path(td); (root/"org-boundary/registry").mkdir(parents=True)
 reg={"organization":"Kernel-Test","services":[{"service_id":"kernel-test.boundary-diagnostic","repository":"Kernel-Test/.github","boundary_role":"BOUNDARY_LOCAL_DIAGNOSTIC"}]}
 (root/"org-boundary/registry/services.json").write_text(json.dumps(reg))
 packet={"schema_version":"stegverse.intr.org-boundary.v1","packet_id":"kernel-test-001","direction":"INGRESS",
 "origin":{"org":"Peer","service":"peer.boundary-diagnostic"},"destination":{"org":"Kernel-Test","service":"kernel-test.boundary-diagnostic"},
 "carrier":{"kind":"HB_DERIVED","reference":"canonical"},"intr_profile":"stegverse.intr.org-boundary.v1",
 "transition":{"reference":"diagnostic","authority_effect":"NONE"},"payload":{"probe":"ping"},
 "evidence":{"ingress_receipt":None,"dispatch_receipt":None,"consumption_receipt":None,"egress_receipt":None,"reconstruction_reference":None}}
 frame=k.carrier_frame(packet,now_ns=k.HB_ANCHOR_UNIX_NS+1_000_000_000)
 recovered=k.recover_packet(frame); assert recovered==packet
 out=k.ingest_frame(root,frame); assert out["status"]=="CONSUMED"; assert out["execution_result"]["reconstruction"]["status"]=="RECONSTRUCTED"
 assert [x["kind"] for x in out["execution_result"]["receipts"]]==["INGRESS_ACCEPTED","DISPATCHED","CONSUMED","RESULT_BOUND","EGRESS_EMITTED"]
 print("PASS")


# federation mesh source-level proof
with tempfile.TemporaryDirectory() as td:
    mesh=Path(td)/"mesh"
    a=Path(td)/"a"; b=Path(td)/"b"
    for root,org in ((a,"Org-A"),(b,"Org-B")):
        (root/"org-boundary/registry").mkdir(parents=True)
        slug=org.lower()
        reg={"organization":org,"services":[{"service_id":slug+".boundary-diagnostic","repository":org+"/.github","boundary_role":"BOUNDARY_LOCAL_DIAGNOSTIC"}]}
        (root/"org-boundary/registry/services.json").write_text(json.dumps(reg))
    packet=k.build_packet(origin_org="Org-A",origin_service="org-a.boundary-diagnostic",
                          destination_org="Org-B",destination_service="org-b.boundary-diagnostic",
                          payload={"probe":"mesh"},packet_id="mesh-a-to-b-001")
    pub=k.publish_packet(packet,root=mesh,now_ns=k.HB_ANCHOR_UNIX_NS+2_000_000_000)
    assert Path(pub["path"]).exists()
    assert k.consume_addressed_frames(a,mesh_root=mesh)==[]
    consumed=k.consume_addressed_frames(b,mesh_root=mesh)
    assert len(consumed)==1
    assert consumed[0]["result"]["status"]=="CONSUMED"
    assert consumed[0]["result"]["execution_result"]["reconstruction"]["status"]=="RECONSTRUCTED"
print("FEDERATION_PASS")
