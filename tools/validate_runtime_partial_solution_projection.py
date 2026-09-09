#!/usr/bin/env python3
import json
from pathlib import Path

p = Path('control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json')
data = json.loads(p.read_text())
assert data['schema'] == 'stegverse.runtime-partial-solution-projection/v1'
assert data['goal_task_id'] == 'GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001'
policy = data['policy']
assert policy['resume_at_first_unresolved_stage'] is True
assert policy['mechanism_reuse_allowed'] is True
assert policy['cross_task_receipt_reuse_requires_exact_subject_binding'] is True
assert policy['generic_runtime_restart_for_later_stage_lane'] is False
solutions = set(data['solution_catalog'])
members = data['members']
assert len(members) == 18
seen = set()
for member in members:
    task_id = member['task_id']
    assert task_id not in seen
    seen.add(task_id)
    assert member['resume_stage']
    assert member['adopt']
    assert set(member['adopt']) <= solutions
print('RUNTIME_PARTIAL_SOLUTION_PROJECTION=PASS')
