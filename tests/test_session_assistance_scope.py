import copy
import json
import unittest
from pathlib import Path

from scripts.validate_session_assistance_scope import latest_inventory_paths, validate_inventory


class SessionAssistanceScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(Path('control/session-assistance-scope-policy.json').read_text())
        paths = latest_inventory_paths()
        cls.assert_inventory_paths = paths
        cls.inventory = next(
            p for p in paths
            if 'admissible-existence-core-local-runtime' in p.name
        )

    def test_newest_inventory_is_selected(self):
        self.assertTrue(self.inventory.name.endswith('-v4.json'), self.inventory)
        self.assertNotIn(
            Path('control/session-goal-inventory-2026-08-14-admissible-existence-core-local-runtime-v3.json'),
            self.assert_inventory_paths,
        )

    def test_current_inventory_passes(self):
        self.assertGreaterEqual(validate_inventory(self.inventory, self.policy), 1)

    def test_trade_is_current_user_explicit_goal_not_shared_directive_only(self):
        data = json.loads(self.inventory.read_text())
        self.assertIn('G08-STEGFIN-TRADE-READY', data['originating_goal_ids'])
        trade_goal = next(x for x in data['goals'] if x['goal_id'] == 'G08-STEGFIN-TRADE-READY')
        self.assertEqual(trade_goal['origin'], 'CURRENT_USER_EXPLICIT_GOAL')
        self.assertTrue(trade_goal['archive_dependency'])
        declaration = data['explicit_goal_declarations'][0]
        self.assertEqual(declaration['goal_id'], 'G08-STEGFIN-TRADE-READY')

    def test_trade_worker_is_in_scope_without_manual_execution_authority(self):
        data = json.loads(self.inventory.read_text())
        binding = next(
            x for x in data['worker_assistance_bindings']
            if x['worker_or_task_id'] == 'STEGFIN-CONTINUITY-CARRIER-007'
        )
        self.assertEqual(binding['session_goal_id'], 'G08-STEGFIN-TRADE-READY')
        self.assertEqual(binding['scope_decision'], 'IN_SCOPE_ASSIST')
        self.assertEqual(data['collision_boundaries']['stegfin_live_execution'], 'MACHINE_OWNED_DO_NOT_MANUALLY_START')

    def test_shared_trade_directive_uses_explicit_goal_lineage(self):
        data = json.loads(self.inventory.read_text())
        trade = next(x for x in data['shared_directives'] if x['directive'] == 'make this trade ready')
        self.assertEqual(trade['scope_decision'], 'IN_SCOPE_ASSIST')
        self.assertFalse(trade['creates_originating_goal'])
        self.assertTrue(trade['archive_dependency'])
        self.assertIn('G08-STEGFIN-TRADE-READY', trade['lineage_evidence_ref'])

    def test_in_scope_binding_must_intersect_originating_goal(self):
        data = json.loads(self.inventory.read_text())
        binding = copy.deepcopy(data['worker_assistance_bindings'][0])
        binding['session_goal_id'] = 'NOT-AN-ORIGINATING-GOAL'
        self.assertNotIn(binding['session_goal_id'], set(data['originating_goal_ids']))


if __name__ == '__main__':
    unittest.main()
