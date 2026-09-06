from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_dispatcher_registers_native_email_consumer():
    dispatcher = load(ROOT / "scripts/dispatch_resident_execution_requests.py", "resident_dispatch_native_email")
    assert ("native_email_action_monitor", "scripts/consume_native_email_action_monitor_request.py") in dispatcher.CONSUMERS


def test_runtime_refresh_materializes_native_email_runtime_files():
    source = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
    assert 'Path("scripts/consume_native_email_action_monitor_request.py")' in source
    assert 'Path("scripts/run_native_email_action_monitor.py")' in source
    assert 'Path("scripts/normalize_github_failure_email_events.py")' in source


def test_monitor_scope_is_operational_mail_only_and_nested_command_is_supported():
    monitor = load(ROOT / "scripts/run_native_email_action_monitor.py", "native_mail_scope")
    assert "notifications@github.com" in monitor.INBOX_QUERY
    assert "noreply@github.com" in monitor.INBOX_QUERY
    assert "[Task Update]" in monitor.INBOX_QUERY
    assert monitor.INBOX_QUERY != "-in:spam -in:trash"


def test_standing_request_binds_existing_hb_resident_path():
    import json
    request = json.loads((ROOT / "control/resident-execution-request.d/native-email-action-monitor-001.json").read_text(encoding="utf-8"))
    assert request["standing_request"] is True
    assert request["heartbeat_grants_execution_authority"] is False
    assert request["oscillator_grants_execution_authority"] is False
    assert request["entrypoint"] == "scripts/consume_native_email_action_monitor_request.py"
