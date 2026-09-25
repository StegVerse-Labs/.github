import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_exact_component010_source_projection():
    registry = json.loads((ROOT / 'data/canonical-task-registry.json').read_text())
    shard = json.loads((ROOT / 'data/canonical-task-records/ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json').read_text())
    rows = [row for row in registry['tasks'] if row.get('task_id') == shard['task_id']]
    assert rows == [shard]


def test_existing_event_history_and_kv_shards_match_projection():
    registry = json.loads((ROOT / 'data/canonical-task-registry.json').read_text())
    for name in ('TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001', 'TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001'):
        shard = json.loads((ROOT / 'data/canonical-task-records' / (name + '.json')).read_text())
        rows = [row for row in registry['tasks'] if row.get('task_id') == name]
        assert rows == [shard]
