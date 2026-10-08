"""Replayed effects reproduce rather than repeat, and every adapter declares its effect.

Correctness rests on two things instead of an exactly-once promise across
separate stores: every effect is either pure or written once under a
deterministic key, and the bytes of a replayed effect are identical. These
cases hold both for this organization's kernel.

- Every registered endpoint adapter declares `endpoint_adapter_effect`. A pure
  adapter writes nothing but its result file; a node-state adapter writes only
  through the write-once store at the supplied node-state root. The kernel
  hands the node-state location only to an adapter declared to write it.
- A kernel answer is stamped with the epoch of the frame it answers, so
  consuming that frame again builds the same answer frame and publishing it is a
  no-op, not a second answer stamped by the host clock.
- The Master Records submitter stamps its frame with the epoch of the receipt
  it carries, when that receipt carries one.

Source validation only. No authority effect is claimed.
"""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))
GENESIS = {"mode": "ESTABLISH_GENESIS", "node_ref": "test-node", "predecessor": None}
EFFECTS = {"PURE", "NODE_STATE_WRITE_ONCE"}
SUBMITTER = ROOT / "resident-runtime/submit_org_transition_to_master_records.py"
ROUTE = "stegverse.route.ecosystem-diagnostic.v1"
# Records the arguments it was run with, so the test can see what it was handed.
ARGV_ADAPTER = ("import argparse, json, sys\nfrom pathlib import Path\n"
                "ap=argparse.ArgumentParser(); ap.add_argument('--packet'); ap.add_argument('--out')\n"
                "ap.add_argument('--node-state-root', default=None)\n"
                "a=ap.parse_args(); Path(a.out).write_text(json.dumps({'argv': sys.argv[1:]}))\n")

spec = importlib.util.spec_from_file_location("kernel", ROOT / "org-kernel/kernel.py")
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)

_peer_spec = importlib.util.spec_from_file_location("peer_organization", ROOT / "tests/peer_organization.py")
peers = importlib.util.module_from_spec(_peer_spec)
_peer_spec.loader.exec_module(peers)


def scratch(case):
    path = Path(tempfile.mkdtemp())
    case.addCleanup(shutil.rmtree, path, True)
    return path


class AdapterEffectClassificationTests(unittest.TestCase):
    def adapters(self):
        return [s for s in REGISTRY["services"] if s.get("endpoint_adapter")]

    def test_every_registered_endpoint_adapter_declares_its_effect(self):
        self.assertTrue(self.adapters())
        for service in self.adapters():
            with self.subTest(service=service["service_id"]):
                self.assertIn(service.get("endpoint_adapter_effect"), EFFECTS)

    def test_a_pure_adapter_writes_only_its_result_file(self):
        for service in self.adapters():
            if service["endpoint_adapter_effect"] != "PURE":
                continue
            with self.subTest(service=service["service_id"]):
                source = (ROOT / service["endpoint_adapter"]).read_text(encoding="utf-8")
                self.assertNotIn("put_once", source)
                self.assertNotIn("--node-state-root", source)
                for line in source.splitlines():
                    if "write_text(" in line or "write_bytes(" in line:
                        self.assertRegex(line, r"\b(args|a)\.out\.write_")
                self.assertIsNone(re.search(r"open\([^)]*['\"][wa]", source))

    def test_a_node_state_adapter_writes_through_the_write_once_store(self):
        for service in self.adapters():
            if service["endpoint_adapter_effect"] != "NODE_STATE_WRITE_ONCE":
                continue
            with self.subTest(service=service["service_id"]):
                source = (ROOT / service["endpoint_adapter"]).read_text(encoding="utf-8")
                self.assertIn("put_once", source)
                self.assertIn("node_state_location_required_from_materializer", source)


class AdapterNodeStateForwardingTests(unittest.TestCase):
    """Only an adapter declared to write node state is told where node state is."""

    def run_declared(self, effect):
        row = {"service_id": "target.endpoint", "boundary_role": "INTERNAL_ENDPOINT",
               "endpoint_adapter": "adapter.py", "endpoint_adapter_disposition": "ALLOW_DECLARED_ADAPTER",
               "admits_processing": [{"capability": "ecosystem_diagnostic", "route_id": ROUTE}]}
        if effect is not None:
            row["endpoint_adapter_effect"] = effect
        root = scratch(self)
        (root / "adapter.py").write_text(ARGV_ADAPTER)
        state = kernel.addressed_node_state_store(scratch(self))
        packet = kernel.build_packet(origin_org="Origin", origin_service="origin.org-control",
                                     destination_org="Target", destination_service="target.endpoint",
                                     payload={"processing": {"capability": "ecosystem_diagnostic",
                                                             "route_id": ROUTE}},
                                     standing=GENESIS)
        result = kernel.run_endpoint_adapter(root, root / "adapter.py", packet, service=row, node_state=state)
        return result["argv"], state

    def test_a_node_state_adapter_is_handed_the_supplied_location(self):
        argv, state = self.run_declared("NODE_STATE_WRITE_ONCE")
        self.assertIn("--node-state-root", argv)
        self.assertEqual(argv[argv.index("--node-state-root") + 1], str(state.root))

    def test_a_pure_or_undeclared_adapter_is_handed_nothing_to_write_to(self):
        for effect in ("PURE", None):
            with self.subTest(effect=effect):
                argv, _ = self.run_declared(effect)
                self.assertNotIn("--node-state-root", argv)


class AnswerEpochTests(unittest.TestCase):
    ORG = "Epoch-Test"
    CONTROL = "epoch-test.org-control"

    def peer(self):
        return peers.materialize(self, self.ORG, [
            {"service_id": self.CONTROL, "repository": self.ORG + "/.github",
             "boundary_role": "BOUNDARY_LOCAL_CONTROL"}])

    def frames(self, mesh):
        return sorted((mesh / "frames.d").glob("*.json"))

    def test_an_answer_carries_the_epoch_of_the_frame_it_answers_and_replays_as_a_no_op(self):
        mesh, peer = scratch(self), self.peer()
        request = kernel.build_packet(
            origin_org="Origin", origin_service="origin.org-control",
            destination_org=self.ORG, destination_service=self.CONTROL,
            payload={"communication_id": "epoch-1", "message_class": "ecosystem.communication",
                     "subject": "s", "body": {}},
            standing=GENESIS)
        epoch = kernel.HB_ANCHOR_EPOCH + 1234
        kernel.publish_packet(request, root=mesh, epoch=epoch)
        first = peer.consume(mesh_root=mesh, node_state_root=scratch(self))
        answer = first[0]["response_publication"]["frame"]
        self.assertEqual(answer["heartbeat_reference"]["epoch"], epoch)
        self.assertIs(answer["heartbeat_reference"].get("derived_from_clock"), False)
        before = self.frames(mesh)
        # A node that lost its consumption marker consumes the frame again.
        again = peer.consume(mesh_root=mesh, node_state_root=scratch(self))
        self.assertEqual(again[0]["response_publication"]["frame"], answer)
        self.assertEqual(self.frames(mesh), before)


class MasterRecordsSubmitterTests(unittest.TestCase):
    def receipt(self, work):
        receipt = {"schema": "stegverse.organization-transition-receipt/v1",
                   "organization": "StegVerse-Labs",
                   "hb_reference": kernel.hb_reference(epoch=kernel.HB_ANCHOR_EPOCH + 77),
                   "receipt_sha256": "sha256:" + "e" * 64}
        path = work / "receipt.json"
        path.write_text(json.dumps(receipt))
        standing = work / "standing.json"
        standing.write_text(json.dumps(GENESIS))
        return path, standing

    def submit(self, receipt, standing, mesh):
        command = [sys.executable, "-B", str(SUBMITTER), "--org-receipt", str(receipt),
                   "--predecessor-ecosystem-state-sha256", "sha256:" + "1" * 64,
                   "--successor-ecosystem-state-sha256", "sha256:" + "2" * 64,
                   "--standing", str(standing), "--mesh-root", str(mesh)]
        return subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True)

    def test_the_same_receipt_submitted_twice_publishes_one_frame_at_its_epoch(self):
        work, mesh = scratch(self), scratch(self)
        receipt, standing = self.receipt(work)
        first = self.submit(receipt, standing, mesh)
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.submit(receipt, standing, mesh)
        self.assertEqual(second.returncode, 0, second.stderr)
        frames = list((mesh / "frames.d").glob("*.json"))
        self.assertEqual(len(frames), 1)
        frame = json.loads(frames[0].read_text())
        self.assertEqual(frame["heartbeat_reference"]["epoch"], kernel.HB_ANCHOR_EPOCH + 77)


if __name__ == "__main__":
    unittest.main()
