from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / 'capsules' / 'iphone-hb30-inline-capsule.js'
CONTRACT = ROOT / 'management' / 'SHWP_IPHONE_TRANSITION_CAPSULE_CONTRACT.json'
VALIDATOR = ROOT / 'scripts' / 'check_iphone_hb30_inline_capsule.py'


class IphoneHb30InlineCapsuleTests(unittest.TestCase):
    def test_inline_capsule_is_publication_independent_and_non_authorizing(self):
        source = CAPSULE.read_text(encoding='utf-8')
        contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
        self.assertIs(contract['inline_capsule_requires_new_publication'], False)
        self.assertEqual(contract['physical_execution_surface'], 'CURRENT_USER_IPHONE')
        self.assertIn('STEGVERSE_INLINE_SAFARI_CAPSULE', contract['physical_execution_transports'])
        self.assertEqual(contract['credential_authority'], 'TV/TVC')
        self.assertEqual(contract['credential_requirement'], 'NONE')
        self.assertEqual(contract['github_token_runtime_authority'], 'NONE')
        self.assertEqual(contract['hosted_runtime_production_authority'], 'NONE')
        self.assertNotIn('fetch(', source)
        self.assertNotIn('XMLHttpRequest', source)
        self.assertNotIn('WebSocket', source)
        self.assertNotIn('window.ethereum', source)
        self.assertIn("location.origin !== EXPECTED_ORIGIN", source)
        self.assertIn("navigator.userAgent.includes('iPhone')", source)
        self.assertIn("receipt.receipt_sha256 = await sha256Hex(canonicalize(receipt))", source)
        self.assertIn("localStorage.setItem(STORAGE_KEY, serialized)", source)

    def test_inline_capsule_matches_first_v12_successor(self):
        source = CAPSULE.read_text(encoding='utf-8')
        self.assertIn('epoch: 29', source)
        self.assertIn('generation: 29', source)
        self.assertIn('epoch: 30', source)
        self.assertIn('generation: 30', source)
        self.assertIn('legacy_hb29_immutable: true', source)
        self.assertIn('worker_authority: false', source)
        self.assertIn('claim_or_fence_mutation: false', source)
        self.assertIn('wallet_authority: false', source)

    def test_canonical_validator_passes(self):
        result = subprocess.run([sys.executable, str(VALIDATOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('IPHONE_HB30_INLINE_CAPSULE_PASS', result.stdout)
        self.assertIn('credential_authority=TV/TVC', result.stdout)
        self.assertIn('github_token_runtime_authority=NONE', result.stdout)
        self.assertIn('hosted_publication_required=false', result.stdout)


if __name__ == '__main__':
    unittest.main()
