"""The kernel's mesh and node state are supplied, never derived from the host.

StegOS lives on the network and a node materializes wherever it is needed, so
nothing the kernel writes may be located by a property of the machine it runs
on. Every test here runs with HOME and XDG_STATE_HOME pointed at empty scratch
directories, and the retired federation variable pointed at a third, and
proves all three stay empty.

Also held here: the heartbeat reference is validated when a frame is
recovered, the epoch can be supplied rather than read from a clock, and the
on-disk frame layout is unchanged so existing meshes and peers keep working.

Source validation only. No authority effect is claimed.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
# OL-3: the child supplies a POSIX Organization ledger root, so it declares the
# POSIX locus exactly as tests/posix_ledger_locus documents.
POSIX_LEDGER_LOCUS = str(ROOT / "tests" / "posix_ledger_locus")
CONTRACT = "docs/CANONICAL_NODE_INGRESS_CONTRACT_001.json"
STANDING = {"mode": "ESTABLISH_GENESIS", "node_ref": "supplied-mesh-test-node", "predecessor": None}
HOST_VARIABLES = ("HOME", "XDG_STATE_HOME", "STEGVERSE_ORG_FEDERATION_ROOT",
                  "STEGVERSE_ORG_FEDERATION_GATEWAY_URL")


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


K = _load("org_kernel_supplied_mesh", "org-kernel/kernel.py")
# A peer consumes through its own kernel into its own ledgers: this
# organization's kernel refuses a dispatch root that is not its repository.
peers = _load("peer_organization", "tests/peer_organization.py")


def provision(root, org):
    """A dispatch root with this organization's real standing surfaces."""
    (root / "org-boundary/registry").mkdir(parents=True)
    (root / "org-boundary/runtime").mkdir(parents=True)
    shutil.copy2(ROOT / "org-boundary/runtime/node_standing.py", root / "org-boundary/runtime/node_standing.py")
    (root / "docs").mkdir(parents=True)
    shutil.copy2(ROOT / CONTRACT, root / CONTRACT)
    slug = K.organization_slug(org)
    (root / "org-boundary/registry/services.json").write_text(json.dumps({
        "organization": org,
        "services": [{"service_id": slug + ".boundary-diagnostic", "repository": org + "/.github",
                      "boundary_role": "BOUNDARY_LOCAL_DIAGNOSTIC"}]}))


def packet(packet_id="supplied-mesh-001"):
    return K.build_packet(origin_org="Org-A", origin_service="org-a.boundary-diagnostic",
                          destination_org="Org-B", destination_service="org-b.boundary-diagnostic",
                          payload={"probe": "supplied"}, standing=STANDING, packet_id=packet_id)


class HostIsolated(unittest.TestCase):
    """HOME, XDG_STATE_HOME and the retired federation variable point at scratch."""

    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.scratch, True)
        self.host = {name: self.scratch / name.lower() for name in ("HOME", "XDG_STATE_HOME", "FEDERATION")}
        for path in self.host.values():
            path.mkdir()
        self.env = {key: value for key, value in os.environ.items() if key not in HOST_VARIABLES}
        self.env.update({"HOME": str(self.host["HOME"]), "XDG_STATE_HOME": str(self.host["XDG_STATE_HOME"]),
                         "STEGVERSE_ORG_FEDERATION_ROOT": str(self.host["FEDERATION"])})
        patcher = mock.patch.dict(os.environ, self.env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assertHostUntouched(self):
        for name, path in self.host.items():
            self.assertEqual(sorted(p.name for p in path.rglob("*")), [], name + " was written")


class MeshIsSuppliedTests(HostIsolated):
    def test_an_unsupplied_mesh_fails_closed_and_nothing_is_derived(self):
        for call in (lambda: K.federation_root(None),
                     lambda: K.mesh_store(),
                     lambda: K.publish_packet(packet(), epoch=40),
                     lambda: K.scan_addressed_frames("Org-B"),
                     lambda: K.collect_ecosystem_responses("Org-B", "c-1")):
            with self.assertRaisesRegex(ValueError, "mesh_location_required_from_materializer"):
                call()
        self.assertHostUntouched()

    def test_a_host_environment_cannot_bind_the_mesh(self):
        with self.assertRaisesRegex(ValueError, "host_environment_mesh_binding_forbidden"):
            K.mesh_store(self.scratch / "mesh", env=dict(os.environ))
        with self.assertRaisesRegex(ValueError, "host_environment_node_state_binding_forbidden"):
            K.addressed_node_state_store(self.scratch / "node", env=dict(os.environ))

    def test_a_supplied_mesh_is_used_as_given_and_reports_its_provenance(self):
        mesh = self.scratch / "mesh"
        self.assertEqual(K.federation_root(mesh), mesh.resolve())
        provenance = K.node_state_provenance(mesh)
        self.assertEqual(provenance["mesh_provenance"], "SUPPLIED")
        self.assertIs(provenance["mesh_portable"], True)
        self.assertHostUntouched()

    def test_frame_layout_is_unchanged_so_existing_meshes_keep_working(self):
        mesh = self.scratch / "mesh"
        published = K.publish_packet(packet(), root=mesh, epoch=40)
        frame = published["frame"]
        expected = hashlib.sha256((frame["packet_id"] + "|" + frame["frame_sha256"]).encode()).hexdigest()
        self.assertEqual(Path(published["path"]), mesh.resolve() / "frames.d" / (expected + ".json"))
        self.assertEqual(json.loads(Path(published["path"]).read_text()), frame)
        # A frame a pre-seam writer left in the mesh is read the same way.
        legacy = K.carrier_frame(packet("legacy-writer-001"), epoch=41)
        legacy_name = hashlib.sha256((legacy["packet_id"] + "|" + legacy["frame_sha256"]).encode()).hexdigest()
        (mesh / "frames.d" / (legacy_name + ".json")).write_text(json.dumps(legacy, indent=2, sort_keys=True) + "\n")
        found = {row["frame"]["packet_id"] for row in K.scan_addressed_frames("Org-B", root=mesh)}
        self.assertEqual(found, {"supplied-mesh-001", "legacy-writer-001"})
        self.assertHostUntouched()

    def test_write_once_holds_and_leaves_no_temporary(self):
        mesh = self.scratch / "mesh"
        first = K.carrier_frame(packet(), epoch=40)
        K.publish_frame(first, root=mesh)
        K.publish_frame(first, root=mesh)
        store = K.mesh_store(mesh)
        key = K.node_store_module.frame_key(first)
        with self.assertRaises(K.node_store_module.WriteOnceCollision):
            store.put_once(key, {**first, "tampered": True})
        self.assertEqual([p.name for p in (mesh / "frames.d").iterdir()], [key.rsplit("/", 1)[-1]])

    def test_a_round_trip_over_a_supplied_mesh_consumes_once_and_answers(self):
        mesh = self.scratch / "mesh"
        peer = peers.materialize(self, "Org-B", [
            {"service_id": "org-b.org-control", "repository": "Org-B/.github",
             "boundary_role": "BOUNDARY_LOCAL_CONTROL"}])
        b = peer.root
        sent = K.publish_ecosystem_message(
            origin_org="Org-A", origin_service="org-a.org-control", organizations=["Org-B"],
            standing=STANDING, message_class="ecosystem.communication", subject="supplied",
            body={"x": 1}, communication_id="supplied-mesh-roundtrip", root=mesh,
            now_ns=K.HB_ANCHOR_UNIX_NS + 1_000_000_000)
        self.assertEqual(sent["published_count"], 1)
        state = self.scratch / "node-b"
        first = peer.consume(mesh_root=mesh, node_state_root=state,
                             now_ns=K.HB_ANCHOR_UNIX_NS + 2_000_000_000)
        second = peer.consume(mesh_root=mesh, node_state_root=state,
                              now_ns=K.HB_ANCHOR_UNIX_NS + 3_000_000_000)
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertTrue((state / "federation/seen.d").is_dir())
        # The peer's checkout carries its emitters, which are code; no node
        # state (markers, intake) is written beside them.
        self.assertFalse((b / "resident-runtime/federation").exists())
        self.assertFalse((b / "resident-runtime/control").exists())
        self.assertEqual(len(peer.receipts("org")), 1)
        rollup = K.collect_ecosystem_responses("Org-A", "supplied-mesh-roundtrip", mesh_root=mesh)
        self.assertEqual([row["organization"] for row in rollup["organizations"]], ["Org-B"])
        self.assertHostUntouched()

    def test_resident_cycles_are_recorded_only_in_supplied_node_state(self):
        with self.assertRaisesRegex(ValueError, "node_state_location_required_from_materializer"):
            K.record_federation_cycle({"cycle": 1})
        node = self.scratch / "node"
        K.record_federation_cycle({"cycle": 1}, root=node)
        K.record_federation_cycle({"cycle": 2}, root=node)
        self.assertEqual(sorted(c["cycle"] for c in K.federation_cycles(root=node)), [1, 2])
        self.assertHostUntouched()


class HeartbeatReferenceTests(unittest.TestCase):
    def test_a_supplied_epoch_is_reproducible_and_not_derived_from_a_clock(self):
        one = K.hb_reference(epoch=40)
        self.assertEqual(one, K.hb_reference(epoch=40))
        self.assertIs(one["derived_from_clock"], False)
        self.assertNotIn("sampled_unix_ns", one)
        self.assertEqual(K.carrier_frame(packet(), epoch=40), K.carrier_frame(packet(), epoch=40))

    def test_a_clock_derived_reference_says_so(self):
        ref = K.hb_reference(K.HB_ANCHOR_UNIX_NS + 25_000_000)
        self.assertIs(ref["derived_from_clock"], True)
        self.assertEqual(ref["epoch"], K.HB_ANCHOR_EPOCH + 2)

    def test_epoch_and_sample_are_exclusive_and_bounded(self):
        with self.assertRaisesRegex(ValueError, "supply_epoch_or_sample_not_both"):
            K.hb_reference(K.HB_ANCHOR_UNIX_NS, epoch=40)
        for bad in (K.HB_ANCHOR_EPOCH - 1, True, "40"):
            with self.assertRaisesRegex(ValueError, "epoch_precedes_hb32_anchor"):
                K.hb_reference(epoch=bad)

    def test_recovery_refuses_an_incoherent_heartbeat_reference(self):
        frame = K.carrier_frame(packet(), epoch=40)
        self.assertEqual(K.recover_packet(frame)["packet_id"], "supplied-mesh-001")
        for field, value, code in (("epoch", 7, "heartbeat_epoch_invalid"),
                                   ("generation", 41, "heartbeat_generation_mismatch"),
                                   ("heartbeat_id", "HB:41", "heartbeat_id_mismatch"),
                                   ("frequency_hz", 50, "heartbeat_frequency_mismatch"),
                                   ("progression_dependency", "WALL_CLOCK", "heartbeat_progression_not_oscillator")):
            body = {k: v for k, v in frame.items() if k != "frame_sha256"}
            body["heartbeat_reference"] = {**frame["heartbeat_reference"], field: value}
            # Re-hashed, so only the reference itself is wrong.
            forged = {**body, "frame_sha256": K.sha(body)}
            with self.assertRaisesRegex(ValueError, code):
                K.recover_packet(forged)

    def test_a_frame_written_before_derived_from_clock_existed_still_recovers(self):
        frame = K.carrier_frame(packet(), epoch=40)
        body = {k: v for k, v in frame.items() if k != "frame_sha256"}
        body["heartbeat_reference"] = {k: v for k, v in body["heartbeat_reference"].items()
                                       if k != "derived_from_clock"}
        self.assertEqual(K.recover_packet({**body, "frame_sha256": K.sha(body)})["packet_id"],
                         "supplied-mesh-001")


class RespondedRequestClassesTests(unittest.TestCase):
    def test_the_kernel_names_the_classes_it_answers(self):
        # org-runtime/interlock-intr.json and organization_egress_boundary
        # .closability_refusal both cite kernel.RESPONDED_REQUEST_CLASSES; the
        # kernel did not define it.
        boundary = json.loads((ROOT / "org-runtime/interlock-intr.json").read_text())
        self.assertIn("org-kernel/kernel.py::RESPONDED_REQUEST_CLASSES", json.dumps(boundary))
        self.assertEqual(set(K.RESPONDED_REQUEST_CLASSES.values()),
                         {"ecosystem.monitor.response", "ecosystem.work.ack", "ecosystem.communication.ack"})
        for request, ack in K.RESPONDED_REQUEST_CLASSES.items():
            self.assertEqual(K.response_message_class(request), ack)


class CallersTakeASuppliedMeshTests(HostIsolated):
    """Each command line that published or consumed on the host-derived mesh."""

    def run_cli(self, *argv):
        return subprocess.run([sys.executable, "-B", *map(str, argv)], capture_output=True, text=True,
                              env={**self.env, "PYTHONPATH": os.pathsep.join(filter(None, (POSIX_LEDGER_LOCUS, self.env.get("PYTHONPATH"))))}, cwd=self.scratch, timeout=120)

    def assertRefused(self, completed, predicate):
        self.assertEqual(completed.returncode, 1, completed.stderr)
        refusal = json.loads(completed.stdout)
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        self.assertEqual(refusal["failed_predicate"], predicate)
        self.assertIs(refusal["consequence_committed"], False)
        self.assertTrue(refusal["retry_entrypoint"])
        self.assertHostUntouched()

    def standing_file(self):
        path = self.scratch / "standing.json"
        path.write_text(json.dumps(STANDING))
        return path

    def test_federation_cycle_refuses_without_a_supplied_mesh_or_node_state(self):
        cycle = ROOT / "resident-runtime/federation_cycle.py"
        self.assertRefused(self.run_cli(cycle), "NODE_STATE_LOCATION_REQUIRED_FROM_MATERIALIZER")
        self.assertRefused(self.run_cli(cycle, "--node-state-root", self.scratch / "node"),
                           "MESH_LOCATION_REQUIRED_FROM_MATERIALIZER")
        self.assertFalse((self.scratch / "node").exists())

    def test_federation_cycle_refuses_without_supplied_ledger_locations(self):
        cycle = ROOT / "resident-runtime/federation_cycle.py"
        self.env = {k: v for k, v in self.env.items()
                    if k not in ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT")}
        self.assertRefused(self.run_cli(cycle, "--mesh-root", self.scratch / "mesh",
                                        "--node-state-root", self.scratch / "node"),
                           "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER")
        self.assertRefused(self.run_cli(cycle, "--mesh-root", self.scratch / "mesh",
                                        "--node-state-root", self.scratch / "node",
                                        "--repo-ledger-root", self.scratch / "ledgers/repo"),
                           "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER")
        self.assertFalse((self.scratch / "node").exists())
        self.assertFalse((self.scratch / "ledgers").exists())

    def test_federation_cycle_runs_on_a_supplied_mesh_and_records_in_node_state(self):
        node = self.scratch / "node"
        mesh = self.scratch / "mesh"
        completed = self.run_cli(ROOT / "resident-runtime/federation_cycle.py",
                                 "--mesh-root", mesh, "--node-state-root", node,
                                 "--repo-ledger-root", self.scratch / "ledgers/repo",
                                 "--org-ledger-root", self.scratch / "ledgers/org")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        receipt = json.loads(completed.stdout)
        self.assertEqual(receipt["frames_seen"], 0)
        self.assertTrue(Path(receipt["recorded_at"]).is_file())
        self.assertTrue(Path(receipt["recorded_at"]).is_relative_to(node.resolve()))
        self.assertHostUntouched()

    def test_ecosystem_control_refuses_without_a_supplied_mesh(self):
        control = ROOT / "resident-runtime/ecosystem_control.py"
        self.assertRefused(self.run_cli(control, "collect", "--communication-id", "c-1"),
                           "MESH_LOCATION_REQUIRED_FROM_MATERIALIZER")
        self.assertRefused(self.run_cli(control, "send-message", "--subject", "s", "--body-json", "{}",
                                        "--standing", self.standing_file()),
                           "MESH_LOCATION_REQUIRED_FROM_MATERIALIZER")

    def test_ecosystem_control_publishes_and_collects_on_a_supplied_mesh(self):
        control = ROOT / "resident-runtime/ecosystem_control.py"
        mesh = self.scratch / "mesh"
        sent = self.run_cli(control, "--mesh-root", mesh, "send-message", "--subject", "s",
                            "--body-json", "{}", "--communication-id", "supplied-cli",
                            "--standing", self.standing_file())
        self.assertEqual(sent.returncode, 0, sent.stderr)
        self.assertEqual(json.loads(sent.stdout)["status"], "PUBLISHED")
        self.assertTrue(any((mesh / "frames.d").iterdir()))
        collected = self.run_cli(control, "--mesh-root", mesh, "collect", "--communication-id", "supplied-cli")
        self.assertEqual(collected.returncode, 0, collected.stderr)
        self.assertEqual(json.loads(collected.stdout)["communication_id"], "supplied-cli")
        self.assertHostUntouched()

    def test_organization_record_submission_refuses_without_a_supplied_mesh(self):
        receipt = self.scratch / "org-receipt.json"
        receipt.write_text(json.dumps({"schema": "stegverse.organization-transition-receipt/v1",
                                       "organization": "StegVerse-Labs"}))
        submit = ROOT / "resident-runtime/submit_org_transition_to_master_records.py"
        common = ("--org-receipt", receipt, "--predecessor-ecosystem-state-sha256", "sha256:" + "a" * 64,
                  "--successor-ecosystem-state-sha256", "sha256:" + "b" * 64, "--standing", self.standing_file())
        self.assertRefused(self.run_cli(submit, *common), "MESH_LOCATION_REQUIRED_FROM_MATERIALIZER")
        mesh = self.scratch / "mesh"
        published = self.run_cli(submit, *common, "--mesh-root", mesh)
        self.assertEqual(published.returncode, 0, published.stderr)
        self.assertEqual(json.loads(published.stdout)["status"], "PUBLISHED_FOR_ORGANIZATION_RECORD")
        self.assertEqual(len(list((mesh / "frames.d").iterdir())), 1)
        self.assertHostUntouched()


if __name__ == "__main__":
    unittest.main()
