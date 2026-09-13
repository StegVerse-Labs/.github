from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "install_sovereign_heartbeat_service_source_continuity",
    ROOT / "scripts" / "install_sovereign_heartbeat_service.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_carrier_service_retains_canonical_source_locator_for_worker_self_heal() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        runtime = base / "heartbeat"
        source = base / "canonical-source"
        source.mkdir()
        mod.materialize(ROOT, runtime)
        receipt = mod.materialize_service(
            runtime,
            system="linux",
            env={
                "XDG_CONFIG_HOME": str(base / "config"),
                "STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(source),
            },
        )
        carrier = Path(receipt["carrier_registration_path"]).read_text(encoding="utf-8")
        worker = Path(receipt["worker_registration_path"]).read_text(encoding="utf-8")
        expected = "STEGVERSE_HEARTBEAT_SOURCE_ROOT=" + str(source.resolve())

        # The worker needs the locator for normal local source refresh. The carrier
        # also needs the same non-secret locator because carrier-side self-heal
        # starts/recycles the canonical WorkerCoordinator from the carrier process
        # environment. Without it, a repaired worker can be alive yet unable to
        # refresh newly merged resident requests such as StegBrowser runtime
        # consumption.
        assert expected in worker
        assert expected in carrier
        assert receipt["native_local_source_refresh_configured"] is True
        assert receipt["canonical_local_source_root"] == str(source.resolve())
        assert receipt["heartbeat_grants_execution_authority"] is False
