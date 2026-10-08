"""The declared carrier is the only federation path.

The kernel's `publish_packet` over the materializer-supplied mesh is the
carrier the boundary declares (org-runtime/interlock-intr.json). The resident
cycle and the ecosystem control command used to switch to an outbound HTTPS
service gateway whenever STEGVERSE_ORG_FEDERATION_GATEWAY_URL was set, which
made a hosted service a transition path and its reachability a predicate. With
the variable set to an address that cannot answer, both still use the mesh,
and nothing in the resident runtime loads the gateway module.

Source validation only. No authority effect is claimed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDING = {"mode": "ESTABLISH_GENESIS", "node_ref": "declared-carrier-test-node", "predecessor": None}
# Reserved for documentation (RFC 5737); a request to it never completes.
UNANSWERABLE = "https://192.0.2.1/federation"


class DeclaredCarrierOnlyTests(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.scratch, True)
        home = self.scratch / "home"
        home.mkdir()
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("STEGVERSE_ORG_FEDERATION_ROOT", "XDG_STATE_HOME")}
        self.env.update({"HOME": str(home), "XDG_STATE_HOME": str(home / "state"),
                         "STEGVERSE_ORG_FEDERATION_GATEWAY_URL": UNANSWERABLE,
                         "STEGVERSE_ORG_FEDERATION_GATEWAY_TIMEOUT_SECONDS": "1"})
        self.mesh = self.scratch / "mesh"

    def run_cli(self, *argv):
        return subprocess.run([sys.executable, "-B", *map(str, argv)], capture_output=True, text=True,
                              env=self.env, cwd=self.scratch, timeout=120)

    def test_the_resident_cycle_uses_the_supplied_mesh_whatever_the_gateway_variable_says(self):
        done = self.run_cli(ROOT / "resident-runtime/federation_cycle.py", "--mesh-root", self.mesh,
                            "--node-state-root", self.scratch / "node",
                            "--repo-ledger-root", self.scratch / "ledgers/repo",
                            "--org-ledger-root", self.scratch / "ledgers/org")
        self.assertEqual(done.returncode, 0, done.stderr)
        receipt = json.loads(done.stdout)
        self.assertEqual(receipt["transport"], "FEDERATION_MESH")
        self.assertEqual(receipt["carrier"], "org-kernel/kernel.py::publish_packet")

    def test_the_resident_cycle_refuses_an_unsupplied_mesh_rather_than_reaching_a_gateway(self):
        done = self.run_cli(ROOT / "resident-runtime/federation_cycle.py",
                            "--node-state-root", self.scratch / "node")
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertEqual(json.loads(done.stdout)["failed_predicate"], "MESH_LOCATION_REQUIRED_FROM_MATERIALIZER")

    def test_ecosystem_control_publishes_and_collects_on_the_mesh_whatever_the_gateway_variable_says(self):
        standing = self.scratch / "standing.json"
        standing.write_text(json.dumps(STANDING))
        control = ROOT / "resident-runtime/ecosystem_control.py"
        sent = self.run_cli(control, "--mesh-root", self.mesh, "send-message", "--subject", "s",
                            "--body-json", "{}", "--communication-id", "declared-carrier",
                            "--standing", standing)
        self.assertEqual(sent.returncode, 0, sent.stderr)
        self.assertTrue(any((self.mesh / "frames.d").iterdir()))
        refused = self.run_cli(control, "collect", "--communication-id", "declared-carrier")
        self.assertEqual(refused.returncode, 1, refused.stderr)
        self.assertEqual(json.loads(refused.stdout)["failed_predicate"], "MESH_LOCATION_REQUIRED_FROM_MATERIALIZER")

    def test_nothing_in_the_resident_runtime_loads_the_gateway_module(self):
        self.assertFalse((ROOT / "resident-runtime/federation_gateway_transport.py").exists())
        for path in list((ROOT / "resident-runtime").glob("*.py")) + list((ROOT / "org-kernel").glob("*.py")):
            source = path.read_text()
            self.assertNotIn("federation_gateway_transport", source, path.name)
            self.assertNotIn("STEGVERSE_ORG_FEDERATION_GATEWAY_URL", source, path.name)

    def test_the_activation_manifest_declares_the_kernel_carrier_and_no_gateway(self):
        manifest = json.loads((ROOT / "resident-runtime/activation-manifest.json").read_text())
        self.assertFalse(any("gateway" in key for key in manifest), manifest)
        self.assertEqual(manifest["federation_carrier"], "org-kernel/kernel.py::publish_packet")
        self.assertEqual(manifest["federation_mesh_location"], "SUPPLIED_BY_NODE_MATERIALIZER")
        self.assertIs(manifest["hosted_service_required"], False)


if __name__ == "__main__":
    unittest.main()
