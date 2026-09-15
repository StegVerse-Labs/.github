from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "execution-bundles/stegbrowser-stegos/stegos"
CARRIER = ROOT / "scripts/run_stegbrowser_render_build_carrier.py"


class StegBrowserCallableExecutionTransportTests(unittest.TestCase):
    def test_bounded_bundle_is_provenance_pinned_and_non_authorizing(self) -> None:
        lease = (BUNDLE / "ephemeral_runtime_lease.py").read_text(encoding="utf-8")
        adapter = (BUNDLE / "sovereign_local_event_runtime.py").read_text(encoding="utf-8")
        self.assertIn("edce3ded5d990f5951e2cb0ff95dee07c0e2581e", lease)
        self.assertIn("c3b19e85073b8d8cf8df4e953cb0d347da76d4e1", adapter)
        self.assertIn('"authority_effect":"NONE"', lease)
        self.assertIn('"authority_effect":"NONE"', adapter)

    def test_bundle_preserves_event_ephemeral_no_rendezvous_contract(self) -> None:
        lease = (BUNDLE / "ephemeral_runtime_lease.py").read_text(encoding="utf-8")
        adapter = (BUNDLE / "sovereign_local_event_runtime.py").read_text(encoding="utf-8")
        self.assertIn('EVENT_EPHEMERAL = "EVENT_EPHEMERAL"', lease)
        self.assertIn('NOT_REQUIRED = "NOT_REQUIRED"', lease)
        self.assertIn("local_event_runtime_forbids_rendezvous", adapter)
        self.assertIn("persistent_host_forbidden", adapter)
        self.assertIn('AUTHORITY_EFFECT = False', adapter)

    def test_carrier_invokes_only_manifest_bound_runner(self) -> None:
        source = CARRIER.read_text(encoding="utf-8")
        self.assertIn("run_stegbrowser_manifest_bound_runtime.py", source)
        self.assertIn("RENDER_BUILD_EVENT_EPHEMERAL", source)
        self.assertIn('"carrier_authority_effect": "NONE"', source)
        self.assertIn('"attached_user_device_required": False', source)
        self.assertIn("completed.returncode in (0, 2)", source)
        self.assertNotIn("run_stegbrowser_runtime_consumption_reusable.py\"", source)


if __name__ == "__main__":
    unittest.main()
