#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

projection_path = Path('control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json')
overlay_path = Path('control/global-runtime-failure-frontier-overlay.json')

data = json.loads(projection_path.read_text())
assert data['schema'] == 'stegverse.runtime-partial-solution-projection/v1'
assert data['goal_task_id'] == 'GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001'
policy = data['policy']
assert policy['resume_at_first_unresolved_stage'] is True
assert policy['mechanism_reuse_allowed'] is True
assert policy['cross_task_receipt_reuse_requires_exact_subject_binding'] is True
assert policy['generic_runtime_restart_for_later_stage_lane'] is False
solutions = set(data['solution_catalog'])
assert 'PERSISTENT_NODE_EPHEMERAL_EXECUTION' in solutions
assert 'STEGOS_RETAINED_NODE_CONTINUITY' not in solutions
assert 'STEGBROWSER_EPHEMERAL_EXECUTION' not in solutions
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
    assert 'PERSISTENT_NODE_EPHEMERAL_EXECUTION' in member['adopt']

overlay = json.loads(overlay_path.read_text())
assert overlay['schema'] == 'stegverse.global-runtime-failure-frontier-overlay/v1'
assert overlay['goal_task_id'] == data['goal_task_id']
assert overlay['cosv'] == data['cosv']
assert overlay['mode'] == 'PROJECTED_AFTER_AUTHENTIC_PERSISTENT_NODE_CONTINUITY_AND_VACC_BRIDGE'
assert overlay['observed_runtime_receipt_present'] is False
assert overlay['projection_assumptions']['persistent_node_continuity_authentically_observed'] is True
assert overlay['projection_assumptions']['vacc_exact_resident_bridge_wired'] is True
assert overlay['projection_assumptions']['all_intr_calls_ephemeral'] is True
assert overlay['projection_assumptions']['all_data_transport_ephemeral'] is True
assert overlay['projection_assumptions']['task_execution_process_persistence_not_required'] is True
assert overlay['projection_assumptions']['subject_binding_uses_persistent_node_identity'] is True

overlay_members = overlay['members']
assert len(overlay_members) == 18
assert {row['task_id'] for row in overlay_members} == seen
counts = Counter(row['frontier_stage'] for row in overlay_members)
assert counts == Counter({3: 5, 4: 2, 5: 1, 6: 2, 7: 8})
assert overlay['frontier_counts']['2:PERSISTENT_NODE_CONTINUITY_OBSERVED'] == 0
assert overlay['frontier_counts']['3:EPHEMERAL_REQUEST_BOUND_AND_CONSUMED'] == 5
assert overlay['frontier_counts']['4:WORKERCOORDINATOR_CLAIM_FENCE'] == 2
assert overlay['frontier_counts']['5:EPHEMERAL_INTERLOCK_INTR_ADMISSION'] == 1
assert overlay['frontier_counts']['6:EPHEMERAL_TRANSPORT_PROVIDER_OR_LEASE_BINDING'] == 2
assert overlay['frontier_counts']['7:COMPONENT_EXECUTION_OR_REEXECUTION'] == 8
assert overlay['interpretation']['resident_process_persistence_wall_removed_in_projection'] is True
assert overlay['interpretation']['largest_projected_frontier'] == 'COMPONENT_EXECUTION_OR_REEXECUTION'
assert overlay['interpretation']['largest_projected_frontier_count'] == 8
assert overlay['interpretation']['second_largest_projected_frontier'] == 'EPHEMERAL_REQUEST_BOUND_AND_CONSUMED'
assert overlay['interpretation']['second_largest_projected_frontier_count'] == 5
print('RUNTIME_PARTIAL_SOLUTION_PROJECTION=PASS')
print('GLOBAL_RUNTIME_FAILURE_FRONTIER_OVERLAY=PASS')
