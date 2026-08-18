#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / 'capsules' / 'iphone-hb30-inline-capsule.js'
CONTRACT = ROOT / 'management' / 'SHWP_IPHONE_TRANSITION_CAPSULE_CONTRACT.json'
REQUIRED = (
    'SHWP-IPHONE-HB30-TRANSITION-CAPSULE-001','d18d57d83cf19b7799cde1a1b4487e496eca7f76','https://stegverse.org','CURRENT_USER_IPHONE',
    'stegverse.iphone-heartbeat-transition-receipt/v1','StegVerse-Labs/.github','control/heartbeat-state.json','stegverse.heartbeat-carrier-runtime-state/v1',
    'heartbeat_epoch:30',"credential_authority: 'TV/TVC'","credential_requirement: 'NONE'","github_token_runtime_authority: 'NONE'",
    'non_tv_tvc_secret_or_token_used: false','worker_authority: false','claim_or_fence_mutation: false','route_authority: false','wallet_authority: false',
    "model_output_authority: 'NONE'","hosted_runtime_production_authority: 'NONE'",'another_physical_machine_required: false',
    'navigator.maxTouchPoints','iphone_class_evidence','screen_width_css','screen_height_css','window.isSecureContext !== true',"crypto.subtle.digest('SHA-256'",'localStorage.setItem(STORAGE_KEY, serialized)',
    "typeof completion === 'function'",
)
FORBIDDEN = ('fetch(','XMLHttpRequest','WebSocket','EventSource','Authorization','Bearer ','GITHUB_TOKEN','GH_TOKEN','TVC_TOKEN','private_key','seed_phrase','eth_sendTransaction','eth_sendRawTransaction','personal_sign','window.ethereum','api.github.com','RENDER','VERCEL','CLOUDFLARE')
def main() -> int:
    failures=[]
    if not CAPSULE.is_file(): failures.append('capsule missing')
    if not CONTRACT.is_file(): failures.append('contract missing')
    if failures:
        [print(f'IPHONE_HB30_INLINE_CAPSULE_FAIL:{x}') for x in failures]; return 1
    source=CAPSULE.read_text(encoding='utf-8'); contract=json.loads(CONTRACT.read_text(encoding='utf-8'))
    failures += [f'missing marker: {m}' for m in REQUIRED if m not in source]
    failures += [f'prohibited marker: {m}' for m in FORBIDDEN if m in source]
    if 'epoch: 29' not in source or 'generation: 29' not in source: failures.append('seed must remain exactly HB29/generation29')
    if 'epoch: 30' not in source or 'generation: 30' not in source: failures.append('successor must remain exactly HB30/generation30')
    if "ua.includes('iPhone') || (touch >= 2" not in source: failures.append('reduced-UA fallback must remain bounded to touch + iPhone-size evidence')
    if contract.get('credential_authority') != 'TV/TVC': failures.append('contract credential authority drift')
    if contract.get('credential_requirement') != 'NONE': failures.append('contract unexpectedly requires credential')
    if contract.get('github_token_runtime_authority') != 'NONE': failures.append('contract GitHub token authority drift')
    if 'STEGVERSE_INLINE_SAFARI_CAPSULE' not in (contract.get('physical_execution_transports') or []): failures.append('contract does not admit inline Safari capsule')
    if contract.get('physical_execution_surface') != 'CURRENT_USER_IPHONE': failures.append('physical execution surface drift')
    if failures:
        [print(f'IPHONE_HB30_INLINE_CAPSULE_FAIL:{x}') for x in failures]; return 1
    print('IPHONE_HB30_INLINE_CAPSULE_PASS surface=CURRENT_USER_IPHONE transport=STEGVERSE_INLINE_SAFARI_CAPSULE authority_effect=NONE credential_authority=TV/TVC github_token_runtime_authority=NONE reduced_ua_iphone_evidence=true hosted_publication_required=false')
    return 0
if __name__ == '__main__': raise SystemExit(main())
