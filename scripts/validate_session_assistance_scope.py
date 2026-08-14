#!/usr/bin/env python3
import json
from pathlib import Path

POLICY_PATH = Path('control/session-assistance-scope-policy.json')
INVENTORY_GLOB = 'control/session-goal-inventory-*-v3.json'


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def fail(message: str):
    raise SystemExit(f'SESSION_ASSISTANCE_SCOPE_FAIL: {message}')


def validate_inventory(path: Path, policy: dict):
    data = load(path)
    required = policy['required_session_inventory_fields']
    for field in required:
        if field not in data:
            fail(f'{path}: missing required field {field}')

    origin_ids = set(data['originating_goal_ids'])
    if not origin_ids:
        fail(f'{path}: originating_goal_ids must not be empty')

    shared = data['shared_directives']
    for directive in shared:
        if directive.get('creates_originating_goal') is True:
            fail(f"{path}: shared directive may not create originating goal: {directive.get('directive')}")
        if directive.get('scope_decision') == 'IN_SCOPE_ASSIST' and not directive.get('lineage_evidence_ref'):
            fail(f"{path}: in-scope shared directive lacks lineage evidence: {directive.get('directive')}")
        if directive.get('archive_dependency') is True and directive.get('scope_decision') != 'IN_SCOPE_ASSIST':
            fail(f"{path}: out-of-scope shared directive may not be archive dependency: {directive.get('directive')}")

    allowed_lineage = set(policy['allowed_lineage_types'])
    allowed_decisions = set(policy['allowed_scope_decisions'])
    for binding in data['worker_assistance_bindings']:
        for field in policy['required_binding_fields']:
            if field not in binding:
                fail(f'{path}: binding missing {field}')
        decision = binding['scope_decision']
        if decision not in allowed_decisions:
            fail(f'{path}: invalid scope_decision {decision}')
        if decision == 'IN_SCOPE_ASSIST':
            if binding['session_goal_id'] not in origin_ids:
                fail(f"{path}: in-scope worker {binding['worker_or_task_id']} does not intersect originating goals")
            if binding['lineage_type'] not in allowed_lineage:
                fail(f"{path}: invalid lineage_type {binding['lineage_type']}")
            if not binding['lineage_evidence_ref']:
                fail(f"{path}: in-scope worker {binding['worker_or_task_id']} lacks lineage evidence")
        elif binding.get('archive_dependency') is True:
            fail(f"{path}: out-of-scope worker {binding['worker_or_task_id']} may not be archive dependency")

    for goal in data.get('goals', []):
        if goal.get('origin') == 'SHARED_DIRECTIVE_ONLY' and goal.get('status') not in {
            'OUT_OF_SCOPE_SHARED_DIRECTIVE', 'MERGED_INTO_CANONICAL_WORKSTREAM', 'SUPERSEDED'
        }:
            fail(f"{path}: shared-directive-only goal promoted into active session scope: {goal.get('goal_id')}")
        if goal.get('origin') == 'SHARED_DIRECTIVE_ONLY' and goal.get('archive_dependency') is True:
            fail(f"{path}: shared-directive-only goal cannot block archive: {goal.get('goal_id')}")

    return len(data['worker_assistance_bindings'])


def main():
    policy = load(POLICY_PATH)
    paths = sorted(Path('.').glob(INVENTORY_GLOB))
    if not paths:
        fail(f'no v3 inventories found for {INVENTORY_GLOB}')
    bindings = 0
    for path in paths:
        bindings += validate_inventory(path, policy)
    print(f'SESSION_ASSISTANCE_SCOPE_PASS inventories={len(paths)} bindings={bindings}')


if __name__ == '__main__':
    main()
