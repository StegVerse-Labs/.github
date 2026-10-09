"""A resident cycle writes its own state where it was supplied, never into the checkout.

`consume_and_respond` wrote consumption markers and work intake under
`<repo_root>/resident-runtime`, so running the resident cycle mutated the
organization's committed source. Node state is now written only under the
`node_state_root` the materializer supplied, and a node supplied none refuses
before it consumes anything. Marker keys and the frame-name dedup identity are
unchanged, so markers written under the old location are honoured when that
location is supplied as node state.

Source validation only. No authority effect is claimed.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# OL-3: the child supplies a POSIX Organization ledger root, so it declares the
# POSIX locus exactly as tests/posix_ledger_locus documents.
POSIX_LEDGER_LOCUS = str(ROOT / "tests" / "posix_ledger_locus")
CONTRACT = "docs/CANONICAL_NODE_INGRESS_CONTRACT_001.json"
STANDING = {"mode": "ESTABLISH_GENESIS", "node_ref": "node-state-test-node", "predecessor": None}

spec = importlib.util.spec_from_file_location("org_kernel_node_state", ROOT / "org-kernel/kernel.py")
K = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K)

# The kernel records every crossing it consumes on its own organization's
# ledgers and refuses a dispatch root that is not its own repository, so the
# source here is a peer materialized as its own organization.
_peer_spec = importlib.util.spec_from_file_location("peer_organization", ROOT / "tests/peer_organization.py")
peers = importlib.util.module_from_spec(_peer_spec)
_peer_spec.loader.exec_module(peers)


def snapshot(root):
    """Every file under `root`, with its bytes, so any write shows up."""
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


class NodeStateIsSuppliedTests(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.scratch, True)
        self.mesh = self.scratch / "mesh"
        self.node = peers.materialize(self, "Node-State-Test", [
            {"service_id": "node-state-test.org-control", "repository": "Node-State-Test/.github",
             "boundary_role": "BOUNDARY_LOCAL_CONTROL"}])
        self.source = self.node.root

    def send(self, message_class, communication_id):
        packet = K.build_ecosystem_packets(
            origin_org="Peer", origin_service="peer.org-control", organizations=["Node-State-Test"],
            standing=STANDING, message_class=message_class, subject="s", body={"x": 1},
            communication_id=communication_id)["packets"][0]
        return K.publish_packet(packet, root=self.mesh, epoch=40)

    def test_an_unsupplied_node_state_refuses_before_consuming_anything(self):
        self.send("ecosystem.communication", "unsupplied")
        source, mesh = snapshot(self.source), snapshot(self.mesh)
        with self.assertRaisesRegex(ValueError, "node_state_location_required_from_materializer"):
            K.consume_and_respond(self.source, mesh_root=self.mesh)
        self.assertEqual(snapshot(self.source), source)
        self.assertEqual(snapshot(self.mesh), mesh)

    def test_markers_and_intake_go_to_supplied_node_state_and_the_source_is_untouched(self):
        self.send("ecosystem.communication", "supplied-communication")
        self.send("ecosystem.work.request", "supplied-work")
        before = snapshot(self.source)
        state = self.scratch / "node-state"
        consumed = self.node.consume(mesh_root=self.mesh, node_state_root=state)
        self.assertEqual(len(consumed), 2)
        self.assertEqual(snapshot(self.source), before)
        self.assertEqual(len(list((state / "federation/seen.d").glob("*.json"))), 2)
        intake = list((state / "control/inbox").glob("*.json"))
        self.assertEqual(len(intake), 1)
        self.assertEqual(json.loads(intake[0].read_text())["state"], "QUEUED_FOR_LOCAL_ADMISSION_EVALUATION")
        for item in consumed:
            self.assertTrue(Path(item["seen_marker"]).is_relative_to(state.resolve()))
        self.assertEqual(self.node.consume(mesh_root=self.mesh, node_state_root=state), [])

    def test_markers_written_at_the_old_location_keep_their_dedup_identity(self):
        self.send("ecosystem.communication", "legacy-marker")
        frame_key = K.scan_addressed_frames("Node-State-Test", root=self.mesh)[0]["key"]
        name = K.node_store_module.frame_name(frame_key)
        # The marker exactly as the kernel wrote it under the checkout before.
        legacy = self.source / "resident-runtime"
        K.PosixStateStore(legacy).put_once(K.node_store_module.seen_key(name), {
            "schema_version": "stegverse.federation-frame-consumption.v1", "frame_name": name,
            "status": "CONSUMED", "authority_effect": "NONE_CARRIER_ONLY"})
        self.assertEqual(self.node.consume(mesh_root=self.mesh, node_state_root=legacy), [])

    def test_a_work_request_without_node_state_is_refused_before_any_receipt(self):
        self.send("ecosystem.work.request", "dispatch-without-state")
        frame = K.scan_addressed_frames("Node-State-Test", root=self.mesh)[0]["frame"]
        before = snapshot(self.source)
        with self.assertRaisesRegex(ValueError, "node_state_location_required_from_materializer"):
            K.dispatch(self.source, K.recover_packet(frame))
        with self.assertRaisesRegex(ValueError, "node_state_location_required_from_materializer"):
            K.persist_work_request(self.source, K.recover_packet(frame))
        self.assertEqual(snapshot(self.source), before)

    def test_the_resident_cycle_leaves_this_checkout_untouched(self):
        packet = K.build_ecosystem_packets(
            origin_org="Peer", origin_service="peer.org-control", organizations=["StegVerse-Labs"],
            standing=STANDING, message_class="ecosystem.communication", subject="s", body={},
            communication_id="node-state-cycle")["packets"][0]
        K.publish_packet(packet, root=self.mesh, epoch=40)
        before = snapshot(ROOT / "resident-runtime")
        state = self.scratch / "cycle-state"
        home = self.scratch / "home"
        home.mkdir()
        env = {k: v for k, v in os.environ.items() if k != "XDG_STATE_HOME"}
        env.update({"HOME": str(home), "XDG_STATE_HOME": str(home / "state")})
        ledgers = self.scratch / "ledgers"
        done = subprocess.run([sys.executable, "-B", str(ROOT / "resident-runtime/federation_cycle.py"),
                               "--mesh-root", str(self.mesh), "--node-state-root", str(state),
                               "--repo-ledger-root", str(ledgers / "repo"),
                               "--org-ledger-root", str(ledgers / "org")],
                              capture_output=True, text=True, env={**env, "PYTHONPATH": os.pathsep.join(filter(None, (POSIX_LEDGER_LOCUS, env.get("PYTHONPATH"))))}, cwd=self.scratch, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["frames_consumed"], 1)
        self.assertEqual(snapshot(ROOT / "resident-runtime"), before)
        self.assertEqual(len(list((state / "federation/seen.d").glob("*.json"))), 1)
        self.assertEqual(len(list((ledgers / "org/receipts").glob("*.json"))), 1)
        self.assertEqual(list(home.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
