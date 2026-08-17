(() => {
  'use strict';

  const CONTRACT_ID = 'SHWP-IPHONE-HB30-TRANSITION-CAPSULE-001';
  const LEGACY_BLOB = 'd18d57d83cf19b7799cde1a1b4487e496eca7f76';
  const STORAGE_KEY = 'stegverse.iphone-heartbeat-transition-receipt.v1';
  const EXPECTED_ORIGIN = 'https://stegverse.org';

  const canonicalize = (value) => {
    if (Array.isArray(value)) return `[${value.map(canonicalize).join(',')}]`;
    if (value && typeof value === 'object') {
      return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`).join(',')}}`;
    }
    return JSON.stringify(value);
  };

  const toHex = (buffer) => Array.from(new Uint8Array(buffer), (byte) => byte.toString(16).padStart(2, '0')).join('');
  const sha256Hex = async (text) => toHex(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)));

  const fail = (message) => {
    const result = JSON.stringify({ state: 'FAIL_CLOSED', reason: message, authority_effect: 'NONE' });
    if (typeof completion === 'function') completion(result);
    else throw new Error(message);
  };

  const run = async () => {
    if (location.origin !== EXPECTED_ORIGIN) return fail(`origin must be ${EXPECTED_ORIGIN}`);
    if (!navigator.userAgent.includes('iPhone')) return fail('CURRENT_USER_IPHONE user agent required');
    if (window.isSecureContext !== true) return fail('secure browser context required');
    if (!globalThis.crypto || !crypto.subtle || typeof crypto.subtle.digest !== 'function') return fail('WebCrypto SHA-256 required');

    const receipt = {
      schema: 'stegverse.iphone-heartbeat-transition-receipt/v1',
      contract_id: CONTRACT_ID,
      physical_execution_surface: 'CURRENT_USER_IPHONE',
      executed_at: new Date().toISOString(),
      seed: {
        repository: 'StegVerse-Labs/.github',
        legacy_state_ref: 'control/heartbeat-state.json',
        legacy_state_git_blob_sha: LEGACY_BLOB,
        epoch: 29,
        generation: 29
      },
      successor: {
        schema: 'stegverse.heartbeat-carrier-runtime-state/v1',
        epoch: 30,
        generation: 30,
        reference_frame: 'heartbeat_epoch:30',
        activation_state: 'ACTIVE',
        authority_effect: 'NONE',
        legacy_hb29_immutable: true
      },
      authority: {
        credential_authority: 'TV/TVC',
        credential_requirement: 'NONE',
        github_token_runtime_authority: 'NONE',
        non_tv_tvc_secret_or_token_used: false,
        worker_authority: false,
        claim_or_fence_mutation: false,
        route_authority: false,
        wallet_authority: false,
        model_output_authority: 'NONE',
        hosted_runtime_production_authority: 'NONE',
        another_physical_machine_required: false
      },
      browser: {
        origin: location.origin,
        user_agent: navigator.userAgent,
        secure_context: window.isSecureContext === true,
        webcrypto: true
      }
    };

    receipt.receipt_sha256 = await sha256Hex(canonicalize(receipt));
    const serialized = JSON.stringify(receipt, null, 2);
    localStorage.setItem(STORAGE_KEY, serialized);

    if (typeof completion === 'function') {
      completion(serialized);
      return;
    }

    const box = document.createElement('textarea');
    box.setAttribute('aria-label', 'StegVerse HB30 portable receipt');
    box.value = serialized;
    box.style.cssText = 'position:fixed;inset:8px;z-index:2147483647;width:calc(100% - 16px);height:calc(100% - 16px);font:12px ui-monospace,monospace;padding:12px;box-sizing:border-box;background:white;color:black;';
    document.documentElement.appendChild(box);
    box.focus();
    box.select();
  };

  run().catch((error) => fail(error instanceof Error ? error.message : String(error)));
})();
