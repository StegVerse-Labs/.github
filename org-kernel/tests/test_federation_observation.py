#!/usr/bin/env python3
import importlib.util
import json
import tempfile
from pathlib import Path

KERNEL_PATH = Path("org-kernel/kernel.py")
OBS_PATH = Path("org-kernel/federation_observation.py")

kspec = importlib.util.spec_from_file_location("kernel", KERNEL_PATH)
k = importlib.util.module_from_spec(kspec)
assert kspec.loader is not None
kspec.loader.exec_module(k)

ospec = importlib.util.spec_from_file_location("federation_observation", OBS_PATH)
o = importlib.util.module_from_spec(ospec)
assert ospec.loader is not None
ospec.loader.exec_module(o)

with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    mesh = base / "mesh"
    origin = base / "origin"
    target = base / "target"

    for root, org in ((origin, "Peer-Org"), (target, "StegVerse-Labs")):
        (root / "org-boundary/registry").mkdir(parents=True)
        service = k.organization_slug(org) + ".org-control"
        registry = {
            "organization": org,
            "services": [
                {
                    "service_id": service,
                    "repository": org + "/.github",
                    "boundary_role": "BOUNDARY_LOCAL_CONTROL",
                }
            ],
        }
        (root / "org-boundary/registry/services.json").write_text(json.dumps(registry))

    packet = k.build_packet(
        origin_org="Peer-Org",
        origin_service="peer-org.org-control",
        destination_org="StegVerse-Labs",
        destination_service="stegverse-labs.org-control",
        payload={"task_id": "ORG-FED-STEGVERSE-LABS-001", "probe": "retain-authentic-observation"},
        transition_reference="org-federation-observation-test",
        authority_effect="NONE",
        packet_id="org-fed-stegverse-labs-observation-test-001",
    )
    k.publish_packet(packet, root=mesh, now_ns=k.HB_ANCHOR_UNIX_NS + 7_000_000_000)

    retained = o.consume_and_retain(target, mesh_root=mesh)
    assert len(retained) == 1

    evidence = retained[0]["observation"]
    assert evidence["schema"] == "stegverse.org-federation-observation/v1"
    assert evidence["organization"] == "StegVerse-Labs"
    assert evidence["packet_id"] == "org-fed-stegverse-labs-observation-test-001"
    assert evidence["activation_inferred"] is False
    assert evidence["task_completion_inferred"] is False
    assert evidence["authenticity_claim"] == "OBSERVED_FROM_CONSUMED_CANONICAL_FRAME"
    assert [r["kind"] for r in evidence["receipt_chain"]] == [
        "INGRESS_ACCEPTED",
        "DISPATCHED",
        "CONSUMED",
        "RESULT_BOUND",
        "EGRESS_EMITTED",
    ]
    assert evidence["reconstruction"]["status"] == "RECONSTRUCTED"
    assert Path(retained[0]["path"]).exists()

    # Re-retention is idempotent/write-once for the same canonical result.
    consumed = k.consume_addressed_frames(target, mesh_root=mesh)
    second = o.retain_consumed_observation(target, consumed[0])
    assert second["observation"] == evidence

print("FEDERATION_OBSERVATION_RETENTION_PASS")
