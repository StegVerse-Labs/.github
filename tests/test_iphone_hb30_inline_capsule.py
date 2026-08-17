from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / 'capsules' / 'iphone-hb30-inline-capsule.js'
CONTRACT = ROOT / 'management' / 'SHWP_IPHONE_TRANSITION_CAPSULE_CONTRACT.json'


def test_inline_capsule_is_publication_independent_and_non_authorizing():
    source = CAPSULE.read_text(encoding='utf-8')
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    assert contract['inline_capsule_requires_new_publication'] is False
    assert contract['physical_execution_surface'] == 'CURRENT_USER_IPHONE'
    assert 'STEGVERSE_INLINE_SAFARI_CAPSULE' in contract['physical_execution_transports']
    assert contract['credential_authority'] == 'TV/TVC'
    assert contract['credential_requirement'] == 'NONE'
    assert contract['github_token_runtime_authority'] == 'NONE'
    assert contract['hosted_runtime_production_authority'] == 'NONE'
    assert 'fetch(' not in source
    assert 'XMLHttpRequest' not in source
    assert 'WebSocket' not in source
    assert 'window.ethereum' not in source
    assert "location.origin !== EXPECTED_ORIGIN" in source
    assert "navigator.userAgent.includes('iPhone')" in source
    assert "receipt.receipt_sha256 = await sha256Hex(canonicalize(receipt))" in source
    assert "localStorage.setItem(STORAGE_KEY, serialized)" in source


def test_inline_capsule_matches_first_v12_successor():
    source = CAPSULE.read_text(encoding='utf-8')
    assert 'epoch: 29' in source
    assert 'generation: 29' in source
    assert 'epoch: 30' in source
    assert 'generation: 30' in source
    assert 'legacy_hb29_immutable: true' in source
    assert 'worker_authority: false' in source
    assert 'claim_or_fence_mutation: false' in source
    assert 'wallet_authority: false' in source


def main() -> int:
    test_inline_capsule_is_publication_independent_and_non_authorizing()
    test_inline_capsule_matches_first_v12_successor()
    print('IPHONE_HB30_INLINE_TESTS_PASS cases=2')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
