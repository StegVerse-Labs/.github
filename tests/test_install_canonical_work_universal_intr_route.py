import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "install_canonical_work_universal_intr_route",
    ROOT / "scripts" / "install_canonical_work_universal_intr_route.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


class CanonicalWorkUniversalInTrRouteInstallerTests(unittest.TestCase):
    def source(self):
        return "\n".join([
            mod.SV002_IMPORT_END.rstrip("\n"),
            "from http.server import ThreadingHTTPServer",
            "def profile():",
            "    return {" + mod.OLD_PROFILES + "}",
            "def route(self, payload, body):",
            "    " + mod.OLD_ROUTE,
            "",
        ])

    def test_transform_installs_route_profile_and_import(self):
        result = mod.transform(self.source())
        self.assertIn(mod.IMPORT_BLOCK, result)
        self.assertIn(mod.NEW_PROFILES, result)
        self.assertIn(mod.NEW_ROUTE, result)
        self.assertIn("canonical_work_intr_ingress", result)

    def test_transform_is_idempotent(self):
        once = mod.transform(self.source())
        self.assertEqual(mod.transform(once), once)

    def test_anchor_drift_fails_closed(self):
        with self.assertRaises(SystemExit):
            mod.transform("from http.server import ThreadingHTTPServer\n")


if __name__ == "__main__":
    unittest.main()
