from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "scripts/consume_native_email_action_monitor_request.py"
VECTOR = ROOT / "control/task-vectors/STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001.json"


def load_module():
    spec = importlib.util.spec_from_file_location("native_email_consumer_handoff", CONSUMER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_canonical_task_cosv_pointer_is_resolved_not_invented():
    module = load_module()
    vector = json.loads(VECTOR.read_text(encoding="utf-8"))
    assert module.TASK_ID == "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001"
    assert vector["vector"] == "10100000100000"
    assert module.resolve_task_vector(ROOT, ROOT) == "10100000100000"


def test_consumer_encodes_repeat_until_empty_semantics():
    source = CONSUMER.read_text(encoding="utf-8")
    assert 'state = "HANDOFF_READY"' in source
    assert 'state = "COMPLETED"' in source
    assert 'processed == 0' in source
    assert 'processed > 0' in source
    assert '"handoff_task_id": None if inbox_empty_of_github else TASK_ID' in source
    assert '"handoff_cosv_task_vector": None if inbox_empty_of_github else cosv_vector' in source
    assert '"handoff_action": None if inbox_empty_of_github else "RESOLVE_POINTER_AND_INITIATE_TASK_AGAIN"' in source
    assert '"terminal_predicate": "GITHUB_INBOX_MATCHING_OPERATIONAL_QUERY_EMPTY"' in source


def test_completion_does_not_follow_nonempty_successful_pass():
    source = CONSUMER.read_text(encoding="utf-8")
    empty_branch = source.index('if inbox_empty_of_github:')
    handoff_branch = source.index('elif continue_required:')
    completed = source.index('state = "COMPLETED"', empty_branch)
    handoff = source.index('state = "HANDOFF_READY"', handoff_branch)
    assert completed < handoff
    assert 'continue_required = bool(pass_result and isinstance(processed, int) and processed > 0)' in source
