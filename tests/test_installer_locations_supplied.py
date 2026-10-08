"""The sovereign heartbeat installers write only where they were told.

`materialize_service` wrote the carrier and worker registrations under
`$XDG_CONFIG_HOME` or `Path.home()/.config/systemd/user` (and LaunchAgents or
APPDATA elsewhere), read a node declaration from `~/.stegverse/node.json` or
`/etc/stegverse/node.json`, and the installers' command lines fell back to a
runtime root under the host's state directory. A test that rendered a unit
without naming a location therefore wrote into the HOME of whatever ran it.

Each location is now supplied -- explicitly or by a named variable -- or the
installer fails closed by that name before anything is written. Every test here
runs with HOME and the XDG directories pointed at scratch and proves they stay
empty. The always-on `Restart=always` units themselves are unchanged.

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
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
DECLARATION = {
    "schema": "stegverse.sovereign-node-declaration/v0.4",
    "declared": True,
    "node_id": "SV-NODE-" + "b" * 24,
    "credential_authority": "TV/TVC",
    "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
}
INSTALLERS = ("install_sovereign_heartbeat_service", "install_sovereign_heartbeat_service_base")
LOCATION_VARIABLES = ("STEGVERSE_SERVICE_REGISTRATION_ROOT", "STEGVERSE_HEARTBEAT_ROOT",
                      "STEGVERSE_SOURCE_PACKAGE_ROOT", "STEGVERSE_SOVEREIGN_NODE_MARKER")


def _load(name):
    # The refresh installer imports its sibling scripts by name.
    if str(ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(name + "_locations", ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HostIsolated(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.scratch, True)
        self.home = self.scratch / "home"
        self.home.mkdir()
        # Populated XDG directories that the installers must not read.
        self.env = {k: v for k, v in os.environ.items() if k not in LOCATION_VARIABLES}
        self.env.update({"HOME": str(self.home), "XDG_CONFIG_HOME": str(self.home / ".config"),
                         "XDG_STATE_HOME": str(self.home / ".local/state"),
                         "APPDATA": str(self.home / "AppData")})

    def assertHomeUntouched(self):
        self.assertEqual(sorted(str(p) for p in self.home.rglob("*")), [])


class MaterializeServiceTests(HostIsolated):
    def test_an_unsupplied_registration_root_fails_closed_by_name_on_every_platform(self):
        for name in INSTALLERS:
            installer = _load(name)
            for system in ("linux", "darwin", "windows"):
                with self.assertRaises(installer.LocationRequired) as raised:
                    installer.materialize_service(self.scratch / "runtime", system=system, env=self.env)
                self.assertEqual(raised.exception.variable, "STEGVERSE_SERVICE_REGISTRATION_ROOT")
                self.assertEqual(raised.exception.failed_predicate, "LOCATION_REQUIRED_FROM_MATERIALIZER")
        self.assertHomeUntouched()
        self.assertFalse((self.scratch / "runtime").exists())

    def test_a_supplied_registration_root_receives_the_units(self):
        for name in INSTALLERS:
            installer = _load(name)
            registration = self.scratch / name / "registration"
            for system in ("linux", "darwin", "windows"):
                rendered = installer.materialize_service(
                    self.scratch / "runtime", system=system,
                    env={**self.env, "STEGVERSE_SERVICE_REGISTRATION_ROOT": str(registration / system)})
                for key in ("carrier_registration_path", "worker_registration_path"):
                    self.assertEqual(Path(rendered[key]).parent, (registration / system).resolve())
                    self.assertTrue(Path(rendered[key]).is_file())
            explicit = installer.materialize_service(self.scratch / "runtime", system="linux", env=self.env,
                                                     registration_root=self.scratch / name / "explicit")
            self.assertEqual(Path(explicit["carrier_registration_path"]).parent,
                             (self.scratch / name / "explicit").resolve())
        self.assertHomeUntouched()

    def test_the_always_on_units_are_unchanged(self):
        # Recorded as an always-on surface, not redesigned here.
        installer = _load("install_sovereign_heartbeat_service")
        rendered = installer.materialize_service(self.scratch / "runtime", system="linux",
                                                 registration_root=self.scratch / "registration", env=self.env)
        self.assertIn("Restart=always", Path(rendered["carrier_registration_path"]).read_text())

    def test_a_node_declaration_under_home_or_etc_is_not_read(self):
        (self.home / ".stegverse").mkdir()
        (self.home / ".stegverse/node.json").write_text(json.dumps(DECLARATION))
        # The process HOME too, because Path.home() reads it rather than `env`.
        patcher = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in INSTALLERS:
            installer = _load(name)
            env = {**self.env, "STEGVERSE_RESIDENT_RENDEZVOUS_URL": "https://stegverse.org",
                   "STEGVERSE_SERVICE_REGISTRATION_ROOT": str(self.scratch / name)}
            with self.assertRaisesRegex(RuntimeError, "node ref required"):
                installer.materialize_service(self.scratch / "runtime", system="linux", env=env)
            marker = self.scratch / "declared-node.json"
            marker.write_text(json.dumps(DECLARATION))
            rendered = installer.materialize_service(self.scratch / "runtime", system="linux",
                                                     env={**env, "STEGVERSE_SOVEREIGN_NODE_MARKER": str(marker)})
            self.assertEqual(rendered["resident_rendezvous_node_ref"], DECLARATION["node_id"])

    def test_install_refuses_before_materializing_anything(self):
        for name in INSTALLERS:
            installer = _load(name)
            target = self.scratch / name / "runtime"
            with self.assertRaises(installer.LocationRequired):
                installer.install(ROOT, target, runner=lambda *a, **k: None, system="linux", env=self.env)
            self.assertFalse(target.exists())
        carrier = _load("install_sovereign_heartbeat_carrier")
        with self.assertRaises(carrier.base.LocationRequired):
            carrier.install_carrier(ROOT, self.scratch / "carrier-runtime", runner=lambda *a, **k: None,
                                    system="linux", env=self.env)
        self.assertFalse((self.scratch / "carrier-runtime").exists())
        self.assertHomeUntouched()


class WorkerSourceRefreshTests(HostIsolated):
    def test_package_and_runtime_roots_are_supplied_or_refused_by_name(self):
        refresh = _load("install_sovereign_worker_source_refresh_service")
        with self.assertRaises(refresh.LocationRequired) as raised:
            refresh.default_source_package_root(self.env)
        self.assertEqual(raised.exception.variable, "STEGVERSE_SOURCE_PACKAGE_ROOT")
        with self.assertRaises(refresh.LocationRequired) as raised:
            refresh.default_runtime_root(self.env)
        self.assertEqual(raised.exception.variable, "STEGVERSE_HEARTBEAT_ROOT")
        supplied = {**self.env, "STEGVERSE_SOURCE_PACKAGE_ROOT": str(self.scratch / "packages")}
        self.assertEqual(refresh.default_source_package_root(supplied), (self.scratch / "packages").resolve())
        self.assertHomeUntouched()


class CommandLineRefusalTests(HostIsolated):
    def run_cli(self, script, *argv):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / script), *map(str, argv)],
                              capture_output=True, text=True, env=self.env, cwd=self.scratch, timeout=120)

    def assertRefused(self, completed, variable):
        self.assertEqual(completed.returncode, 1, completed.stderr)
        refusal = json.loads(completed.stdout)
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        self.assertEqual(refusal["failed_predicate"], "LOCATION_REQUIRED_FROM_MATERIALIZER")
        self.assertEqual(refusal["required_evidence_or_repair"], "supply " + variable)
        self.assertIs(refusal["consequence_committed"], False)
        self.assertTrue(refusal["retry_entrypoint"])
        self.assertHomeUntouched()

    def test_each_installer_refuses_an_unsupplied_location_and_commits_nothing(self):
        runtime = self.scratch / "runtime"
        for script in ("install_sovereign_heartbeat_service.py", "install_sovereign_heartbeat_service_base.py",
                       "install_sovereign_heartbeat_carrier.py"):
            self.assertRefused(self.run_cli(script), "STEGVERSE_HEARTBEAT_ROOT")
            self.assertRefused(self.run_cli(script, "--runtime-root", runtime), "STEGVERSE_SERVICE_REGISTRATION_ROOT")
        refresh = "install_sovereign_worker_source_refresh_service.py"
        self.assertRefused(self.run_cli(refresh), "STEGVERSE_HEARTBEAT_ROOT")
        self.assertRefused(self.run_cli(refresh, "--runtime-root", runtime), "STEGVERSE_SOURCE_PACKAGE_ROOT")
        self.assertRefused(self.run_cli(refresh, "--runtime-root", runtime, "--source-package-root",
                                        self.scratch / "packages"), "STEGVERSE_SERVICE_REGISTRATION_ROOT")
        self.assertFalse(runtime.exists())


if __name__ == "__main__":
    unittest.main()
