import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_exact_component010_source_projection():
    registry = json.loads((ROOT / 'data/canonical-task-registry.json').read_text())
    shard = json.loads((ROOT / 'data/canonical-task-records/ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json').read_text())
    rows = [row for row in registry['tasks'] if row.get('task_id') == shard['task_id']]
    assert rows == [shard]
