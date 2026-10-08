#!/usr/bin/env python3
import atexit, importlib.util, json, shutil, tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location("kernel","org-kernel/kernel.py"); k=importlib.util.module_from_spec(spec); spec.loader.exec_module(k)

TREE=Path("org-kernel/kernel.py").resolve().parents[1]
CONTRACT="docs/CANONICAL_NODE_INGRESS_CONTRACT_001.json"
#: A synthetic root is a dispatch root like any other, so it has to carry the
#: standing surfaces the kernel resolves from it. Copied rather than stubbed:
#: a test root that admits a crossing this organization's real root would refuse
#: proves nothing about the real root.
def provision_standing(root:Path)->None:
    (root/"org-boundary/runtime").mkdir(parents=True,exist_ok=True)
    shutil.copy2(TREE/"org-boundary/runtime/node_standing.py",root/"org-boundary/runtime/node_standing.py")
    # A boundary that cannot state how processing was selected fails closed.
    shutil.copy2(TREE/"org-boundary/runtime/manifest_selection.py",root/"org-boundary/runtime/manifest_selection.py")
    (root/"docs").mkdir(parents=True,exist_ok=True)
    shutil.copy2(TREE/CONTRACT,root/CONTRACT)

#: A root that consumes records each crossing on its own organization's
#: ledgers through its own kernel and emitters, so it is materialized as that
#: organization rather than handed to this one's kernel.
_peer_spec=importlib.util.spec_from_file_location("peer_organization",TREE/"tests/peer_organization.py")
peers=importlib.util.module_from_spec(_peer_spec); _peer_spec.loader.exec_module(peers)
def materialize(org:str, service:str, role:str):
    peer=peers.materialize(None,org,[{"service_id":service,"repository":org+"/.github","boundary_role":role}])
    atexit.register(shutil.rmtree,peer.root,True)
    atexit.register(shutil.rmtree,peer.repo_ledger.parent,True)
    return peer
def node_state_in(root:Path)->list[str]:
    """Markers or intake written under a checkout; its emitters are code, not node state."""
    return [str(p) for prefix in ("resident-runtime/federation","resident-runtime/control")
            for p in (root/prefix).rglob("*") if p.is_file()]

STANDING={"mode":"ESTABLISH_GENESIS","node_ref":"kernel-test-node","predecessor":None}
with tempfile.TemporaryDirectory() as td:
 root=Path(td); (root/"org-boundary/registry").mkdir(parents=True); provision_standing(root)
 reg={"organization":"Kernel-Test","services":[{"service_id":"kernel-test.boundary-diagnostic","repository":"Kernel-Test/.github","boundary_role":"BOUNDARY_LOCAL_DIAGNOSTIC"}]}
 (root/"org-boundary/registry/services.json").write_text(json.dumps(reg))
 packet={"schema_version":"stegverse.intr.org-boundary.v1","packet_id":"kernel-test-001","direction":"INGRESS",
 "origin":{"org":"Peer","service":"peer.boundary-diagnostic"},"destination":{"org":"Kernel-Test","service":"kernel-test.boundary-diagnostic"},
 "carrier":{"kind":"HB_DERIVED","reference":"canonical"},"intr_profile":"stegverse.intr.org-boundary.v1",
 "transition":{"reference":"diagnostic","authority_effect":"NONE"},"payload":{"probe":"ping"},"standing":STANDING,
 "evidence":{"ingress_receipt":None,"dispatch_receipt":None,"consumption_receipt":None,"egress_receipt":None,"reconstruction_reference":None}}
 frame=k.carrier_frame(packet,now_ns=k.HB_ANCHOR_UNIX_NS+1_000_000_000)
 recovered=k.recover_packet(frame); assert recovered==packet
 out=k.ingest_frame(root,frame); assert out["status"]=="CONSUMED"; assert out["execution_result"]["reconstruction"]["status"]=="RECONSTRUCTED"
 assert [x["kind"] for x in out["execution_result"]["receipts"]]==["INGRESS_ACCEPTED","DISPATCHED","CONSUMED","RESULT_BOUND","EGRESS_EMITTED"]
 print("PASS")


# federation mesh source-level proof
with tempfile.TemporaryDirectory() as td:
    mesh=Path(td)/"mesh"
    a,b=(materialize(org,org.lower()+".boundary-diagnostic","BOUNDARY_LOCAL_DIAGNOSTIC") for org in ("Org-A","Org-B"))
    packet=k.build_packet(origin_org="Org-A",origin_service="org-a.boundary-diagnostic",
                          destination_org="Org-B",destination_service="org-b.boundary-diagnostic",
                          payload={"probe":"mesh"},standing=STANDING,packet_id="mesh-a-to-b-001")
    pub=k.publish_packet(packet,root=mesh,now_ns=k.HB_ANCHOR_UNIX_NS+2_000_000_000)
    assert Path(pub["path"]).exists()
    assert a.consume_addressed(mesh_root=mesh)==[]
    consumed=b.consume_addressed(mesh_root=mesh)
    assert len(consumed)==1
    assert consumed[0]["organization_record"] is not None and len(b.receipts("org"))==1
    assert consumed[0]["result"]["status"]=="CONSUMED"
    assert consumed[0]["result"]["execution_result"]["reconstruction"]["status"]=="RECONSTRUCTED"
print("FEDERATION_PASS")


# 14-node ecosystem-wide communication fanout / aggregation proof
with tempfile.TemporaryDirectory() as td:
    mesh=Path(td)/"mesh"
    orgs=["AaCT-E","Admissible-Existence","AdmittedCode","Data-Continuation","ECAT-ICAT-Formal",
          "formalism-tests","GCAT-BCAT-Engine","Infrastructure-Continuity-Ventures","master-records",
          "StegGhost","StegVerse-002","StegVerse-Labs","StegVerse-org","Triad-Test"]
    roots={org:materialize(org,k.organization_slug(org)+".org-control","BOUNDARY_LOCAL_CONTROL") for org in orgs}
    pub=k.publish_ecosystem_message(
        origin_org="StegVerse-Labs",
        origin_service="stegverse-labs.org-control",
        organizations=orgs,
        standing=STANDING,
        message_class="ecosystem.monitor.request",
        subject="ecosystem-broadcast-001",
        body={"monitor":"runtime-status"},
        requested_action="REPORT_STATUS",
        communication_id="ecosystem-broadcast-001",
        root=mesh,
        now_ns=k.HB_ANCHOR_UNIX_NS+3_000_000_000
    )
    assert pub["published_count"]==14
    results={org:peer.consume_addressed(mesh_root=mesh) for org,peer in roots.items()}
    rollup=k.aggregate_ecosystem_results("ecosystem-broadcast-001",results)
    assert rollup["complete"] is True
    assert rollup["consumed_count"]==14
    assert rollup["pending_count"]==0
print("ECOSYSTEM_BROADCAST_PASS")


# 14-node monitor request -> response roll-up proof
with tempfile.TemporaryDirectory() as td:
    mesh=Path(td)/"mesh"
    orgs=["AaCT-E","Admissible-Existence","AdmittedCode","Data-Continuation","ECAT-ICAT-Formal",
          "formalism-tests","GCAT-BCAT-Engine","Infrastructure-Continuity-Ventures","master-records",
          "StegGhost","StegVerse-002","StegVerse-Labs","StegVerse-org","Triad-Test"]
    roots={}
    directory={"denominator":14,"organizations":[{"organization":org} for org in orgs]}
    for org in orgs:
        peer=materialize(org,k.organization_slug(org)+".org-control","BOUNDARY_LOCAL_CONTROL")
        (peer.root/"org-boundary/registry/federation.json").write_text(json.dumps(directory))
        (peer.root/"resident-runtime/activation-manifest.json").write_text(json.dumps({"state":"TEST_ACTIVE","kernel":{"version":"1.3.0"}}))
        roots[org]=peer
    origin=roots["StegVerse-Labs"].root
    pub=k.publish_ecosystem_from_directory(
        origin,
        standing=STANDING,
        message_class="ecosystem.monitor.request",
        subject="ecosystem-monitor-response-001",
        body={"monitor":"resident-status"},
        requested_action="REPORT_STATUS",
        communication_id="ecosystem-monitor-response-001",
        mesh_root=mesh,
        now_ns=k.HB_ANCHOR_UNIX_NS+4_000_000_000
    )
    assert pub["published_count"]==14
    for org,peer in roots.items():
        peer.consume(mesh_root=mesh,node_state_root=Path(td)/"node-state"/org,now_ns=k.HB_ANCHOR_UNIX_NS+4_100_000_000)
    roll=k.collect_ecosystem_responses("StegVerse-Labs","ecosystem-monitor-response-001",mesh_root=mesh)
    assert roll["response_count"]==14
    assert {x["organization"] for x in roll["organizations"]}==set(orgs)

# 14-node work request -> local admission queue proof
with tempfile.TemporaryDirectory() as td:
    mesh=Path(td)/"mesh"
    orgs=["AaCT-E","Admissible-Existence","AdmittedCode","Data-Continuation","ECAT-ICAT-Formal",
          "formalism-tests","GCAT-BCAT-Engine","Infrastructure-Continuity-Ventures","master-records",
          "StegGhost","StegVerse-002","StegVerse-Labs","StegVerse-org","Triad-Test"]
    roots={}
    directory={"denominator":14,"organizations":[{"organization":org} for org in orgs]}
    for org in orgs:
        peer=materialize(org,k.organization_slug(org)+".org-control","BOUNDARY_LOCAL_CONTROL")
        (peer.root/"org-boundary/registry/federation.json").write_text(json.dumps(directory))
        roots[org]=peer
    origin=roots["StegVerse-Labs"].root
    pub=k.publish_ecosystem_from_directory(
        origin,
        standing=STANDING,
        message_class="ecosystem.work.request",
        subject="ecosystem-work-intake-001",
        body={"goal":"perform local status reconciliation"},
        requested_action="RECONCILE_LOCAL_STATUS",
        communication_id="ecosystem-work-intake-001",
        mesh_root=mesh,
        now_ns=k.HB_ANCHOR_UNIX_NS+5_000_000_000
    )
    assert pub["published_count"]==14
    for org,peer in roots.items():
        state=Path(td)/"node-state"/org
        peer.consume(mesh_root=mesh,node_state_root=state,now_ns=k.HB_ANCHOR_UNIX_NS+5_100_000_000)
        # Intake is node state, recorded where the materializer said, never in the source root.
        assert node_state_in(peer.root)==[]
        inbox=list((state/"control/inbox").glob("*.json"))
        assert len(inbox)==1
        record=json.loads(inbox[0].read_text())
        assert record["state"]=="QUEUED_FOR_LOCAL_ADMISSION_EVALUATION"
        assert record["execution_authority_inferred"] is False
    roll=k.collect_ecosystem_responses("StegVerse-Labs","ecosystem-work-intake-001",mesh_root=mesh)
    assert roll["response_count"]==14
print("ECOSYSTEM_CONTROL_RESPONSE_PASS")


# durable federation replay/dedup proof
with tempfile.TemporaryDirectory() as td:
    mesh=Path(td)/"mesh"
    org="Replay-Test"
    node=materialize(org,"replay-test.org-control","BOUNDARY_LOCAL_CONTROL"); root=node.root
    directory={"denominator":1,"organizations":[{"organization":org}]}
    (root/"org-boundary/registry/federation.json").write_text(json.dumps(directory))
    (root/"resident-runtime/activation-manifest.json").write_text(json.dumps({"state":"TEST","kernel":{"version":"1.3.1"}}))
    pub=k.publish_ecosystem_from_directory(
        root,
        standing=STANDING,
        message_class="ecosystem.communication",
        subject="dedup",
        body={"value":1},
        communication_id="ecosystem-dedup-001",
        mesh_root=mesh,
        now_ns=k.HB_ANCHOR_UNIX_NS+6_000_000_000
    )
    state=Path(td)/"node-state"
    first=node.consume(mesh_root=mesh,node_state_root=state,now_ns=k.HB_ANCHOR_UNIX_NS+6_100_000_000)
    second=node.consume(mesh_root=mesh,node_state_root=state,now_ns=k.HB_ANCHOR_UNIX_NS+6_200_000_000)
    assert not (root/"resident-runtime/federation").exists()
    assert len(first)==1
    assert len(second)==1 or len(second)==0
    # second cycle may see only the response addressed to self; it must not reconsume the original request.
    originals=[x for x in second if ((x.get("result") or {}).get("packet") or {}).get("packet_id")=="ecosystem-dedup-001:replay-test"]
    assert originals==[]
print("ECOSYSTEM_DEDUP_PASS")


# node-standing gate proof: kernel_required 1.3.0 declares this gate, so the
# gate is proven here rather than implied by the declared version.
with tempfile.TemporaryDirectory() as td:
    root=Path(td)/"gate"
    (root/"org-boundary/registry").mkdir(parents=True); provision_standing(root)
    org="Gate-Test"
    reg={"organization":org,"services":[{"service_id":"gate-test.org-control","repository":"Gate-Test/.github","boundary_role":"BOUNDARY_LOCAL_CONTROL"}]}
    (root/"org-boundary/registry/services.json").write_text(json.dumps(reg))

    # A standing-less packet cannot be constructed: `standing` has no default.
    try:
        k.build_packet(origin_org="Anyone-At-All",origin_service="anyone.org-control",
                       destination_org=org,destination_service="gate-test.org-control",
                       payload={"probe":"unstanding"})
        raise AssertionError("build_packet accepted a packet with no standing")
    except TypeError as expected:
        assert "standing" in str(expected)

    # A hand-forged envelope that skips the constructor is refused fail-closed,
    # as the contract's own disposition rather than a bare error.
    forged={"schema_version":k.PACKET_SCHEMA,"packet_id":"gate-test-001","direction":"INGRESS",
            "origin":{"org":"Anyone-At-All","service":"anyone.org-control"},
            "destination":{"org":org,"service":"gate-test.org-control"},
            "carrier":{"kind":"HB_DERIVED","reference":"org-federation"},
            "intr_profile":"stegverse.intr.org-boundary.v1",
            "transition":{"reference":"federation.v1","authority_effect":"NONE","conditions":[]},
            "payload":{"probe":"unstanding"},
            "evidence":{"ingress_receipt":None,"dispatch_receipt":None,"consumption_receipt":None,"egress_receipt":None,"reconstruction_reference":None}}
    try:
        k.dispatch(root,forged)
        raise AssertionError("dispatch consumed a crossing with no standing")
    except ValueError as refused:
        assert str(refused).startswith("node_standing_refused:"), refused
        assert "no-standing-declared" in str(refused), refused

    # The same crossing, carrying standing, is admitted and the resolved
    # standing travels on the result.
    admitted=k.dispatch(root,{**forged,"standing":STANDING})
    assert admitted["consumed"] is True
    assert admitted["application_result"]["execution_authority_inferred"] is False
    assert admitted["node_standing_disposition"]=="ALLOW"
    assert admitted["standing_mode"]=="ESTABLISH_GENESIS"
    assert admitted["standing_node_ref"]=="kernel-test-node"
    assert admitted["standing_generation"]==1
    # The gate makes the crossing provable by node chain. It does not validate
    # the caller-written origin string, and the result says so rather than
    # letting a reader of the chain assume otherwise -- the origin above is
    # still "Anyone-At-All" and the crossing is admitted on its standing.
    assert admitted["caller_editable_origin_established_identity"] is False
    assert admitted["structural_standing_only"] is True
    assert admitted["structural_standing_is_authenticated_standing"] is False
    assert admitted["standing_authority_effect"]=="NONE_STANDING_ONLY"
print("NODE_STANDING_GATE_PASS")
