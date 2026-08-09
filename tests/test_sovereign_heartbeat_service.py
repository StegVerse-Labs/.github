from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "install_sovereign_heartbeat_service",
    ROOT / "scripts" / "install_sovereign_heartbeat_service.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_materialization_is_network_independent(tmp_path: Path) -> None:
    target = tmp_path / "heartbeat"
    receipt = mod.materialize(ROOT, target)
    assert receipt["network_fetch_required"] is False
    assert receipt["third_party_deployment_required"] is False
    assert receipt["third_party_scheduler_required"] is False
    assert (target / "heartbeat_runtime" / "engine_v8.py").is_file()
    assert (target / "control" / "heartbeat-state.json").is_file()
    assert (target / "control" / "worker-registry.json").is_file()
    assert (target / "scripts" / "run_heartbeat_runtime.py").is_file()


def test_linux_service_runs_continuous_runtime_directly(tmp_path: Path) -> None:
    root = tmp_path / "heartbeat"
    mod.materialize(ROOT, root)
    receipt = mod.materialize_service(
        root,
        system="linux",
        env={"XDG_CONFIG_HOME": str(tmp_path / "config")},
    )
    text = Path(receipt["registration_path"]).read_text(encoding="utf-8")
    assert receipt["registration_kind"] == "systemd-user"
    assert "run_heartbeat_runtime.py" in text
    assert "--continuous" in text
    assert "Restart=always" in text
    assert "github" not in text.lower()
    assert "render" not in text.lower()


def test_install_records_native_activation_without_granting_authority(tmp_path: Path) -> None:
    calls = []

    def runner(command, **_kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    target = tmp_path / "heartbeat"
    receipt = mod.install(
        ROOT,
        target,
        runner=runner,
        system="linux",
        env={"XDG_CONFIG_HOME": str(tmp_path / "config")},
    )
    assert receipt["active"] is True
    assert receipt["execution_authority_effect"] == "NONE"
    assert receipt["third_party_deployment_required"] is False
    assert receipt["third_party_scheduler_required"] is False
    assert len(calls) == 2
    assert (target / "receipts" / "sovereign-host" / "activation.latest.json").is_file()
