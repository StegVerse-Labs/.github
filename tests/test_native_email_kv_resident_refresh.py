from pathlib import Path

from scripts import refresh_sovereign_worker_runtime_source as refresh


REQUIRED = {
    Path("scripts/consume_native_email_action_monitor_request_kv.py"),
    Path("scripts/run_native_email_action_monitor_kv_guard.py"),
    Path("scripts/persist_native_email_incidents_to_kv.py"),
}


def test_native_email_kv_enforcement_chain_is_refreshed_into_resident_runtime():
    assert REQUIRED <= set(refresh.STATIC_FILES)


def test_native_email_kv_enforcement_files_are_static_source_not_runtime_state():
    for rel in REQUIRED:
        refresh._assert_static_path(rel)
