import copy
import json
import unittest
from pathlib import Path

from scripts.validate_session_assistance_scope import validate_inventory


class SessionAssistanceScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(Path('control/session-assistance-scope-policy.json').read_text())
        cls.inventory = Path('control/session-goal-inventory-2026-08-14-admissible-existence-core-local-runtime-v3.json')

    def test_current_inventory_passes(self):
        self.assertGreaterEqual(validate_inventory(self.inventory, self.policy), 1)

    def test_trade_shared_directive_is_not_archive_dependency(self):
        data = json.loads(self.inventory.read_text())
        trade = next(x for x in data['shared_directives'] if x['directive'] == 'make this trade ready')
        self.assertEqual(trade['scope_decision'], 'OUT_OF_SCOPE_SHARED_DIRECTIVE')
        self.assertFalse(trade['archive_dependency'])

    def test_in_scope_binding_must_intersect_originating_goal(self):
        data = json.loads(self.inventory.read_text())
        binding = copy.deepcopy(data['worker_assistance_bindings'][0])
        binding['session_goal_id'] = 'NOT-AN-ORIGINATING-GOAL'
        self.assertNotIn(binding['session_goal_id'], set(data['originating_goal_ids']))


if __name__ == '__main__':
    unittest.main()
