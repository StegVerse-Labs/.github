# Device <-> KV <-> SKAP Authentic Runtime Mirror Handoff

Updated: 2026-09-11

```text
goal_id: STEGOS-DEVICE-KV-SKAP-AUTHENTIC-RUNTIME-002
parent_goal: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
cosv_id: 50000000102000
state: ACTIVE
checkout_state: CHECKED_OUT
issue: StegVerse-Labs/.github#1500
credential_authority: TV/TVC
transition_authority: Interlock/InTr
worker_claim_authority: WorkerCoordinator
github_runtime_authority: NONE
hosted_runtime_fallback: NONE
second_user_operated_device_required: false
source_integration_complete: true
authentic_runtime_complete: false
```

## Goal

Close only the remaining authentic runtime evidence for the sovereign single-device lineage:

```text
CURRENT_IPHONE_SECURE_ENCLAVE_ACTIVATION
-> TVC_CHALLENGE_VERIFICATION
-> TVC_PUBLIC_RECIPIENT_PROJECTION
-> DEVICE_SYSTEM -> KV GATEWAY SIDECAR
-> TVC SKAP CUSTODY DRAIN
-> DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
-> exact SKAP/KV readback
-> DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED
```

## Inherited proven source state

The parent `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` reached its 20/20 prompt ceiling after source/native integration was completed. `.github` PR #1456 passed exact-head Organization Control `34614835385`, Deterministic Repository Suite `34614835384`, and Heartbeat Worker Validation `34614835482`, then merged as `3150529c5da12f9eaa4c612b85a2feab2de9a693`.

StegOS #341 merged the bounded `stegverse://tvc-recipient-capability` current-iPhone invocation surface. TVC #407 owns challenge issue/verification/adoption. Existing canonical WorkerCoordinator, StegOS EVENT_EPHEMERAL runtime, Interlock/InTr continuation, and TVC SKAP custody paths remain the only eligible execution owners.

Source/CI/merge state is not runtime proof. Do not create duplicate recipient adapters, TVC verifiers, runtime lanes, InTr executors, or SKAP custody writers unless authentic execution exposes a concrete defect.

## Remaining predicates

Close in order:

1. `AUTHENTIC_CURRENT_IPHONE_TVC_RECIPIENT_ACTIVATION_OBSERVED`
2. `AUTHENTIC_TVC_CHALLENGE_EXCHANGE_VERIFIED`
3. `TVC_PUBLIC_RECIPIENT_CONFIG_PROJECTED_FROM_AUTHENTIC_EXCHANGE`
4. `AUTHENTIC_CURRENT_DEVICE_GATEWAY_CANONICAL_SIDECAR_OBSERVED`
5. `AUTHENTIC_TVC_CANONICAL_ROUNDTRIP_ELIGIBLE_DRAIN_RECEIPT_OBSERVED`
6. `AUTHENTIC_RETAINED_NODE_BINDING_OBSERVED`
7. `AUTHENTIC_CANONICAL_EVENT_EPHEMERAL_LEASE_OPEN_OBSERVED`
8. `FRESH_WORKERCOORDINATOR_CLAIM_FENCE_BOUND_TO_CANONICAL_RUNTIME_BRIDGE`
9. `AUTHENTIC_FOUR_LEG_INTR_ROUNDTRIP_OBSERVED`
10. `AUTHENTIC_SKAP_KV_RETURN_RECEIPT_OBSERVED`
11. `KV_SKAP_TERMINAL_EXACT_READBACK_OBSERVED`
12. terminal `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`

## Runtime evidence rules

Eligible current-iPhone recipient evidence must come from the merged bounded StegOS Mobile route and the same non-exportable Secure Enclave P-256 key handle. The TVC challenge must be fresh, successfully verified, and bound to that candidate before public recipient projection.

The Gateway/TVC input pair must be authentic and receipt-bound. TVC remains sole SKAP ciphertext custody writer. The canonical roundtrip must produce four adjacent Interlock/InTr receipts with continuous hash lineage and exact packet/readback validation. Fixtures, reconstruction-only evidence, GitHub Actions artifacts, hosted substitutes, fabricated receipts, or private-key export are ineligible.

## Authority invariants

- WorkerCoordinator owns claim/fence.
- Interlock/InTr owns transition admission.
- TV/TVC owns credential authority and SKAP ciphertext custody.
- StegOS canonical runtime lane owns EVENT_EPHEMERAL lifecycle.
- GitHub/CI/Heartbeat are source validation and evidence surfaces only.
- No hosted fallback and no second user-operated device.

## Related evidence trackers

- #1503 current-iPhone TVC activation/challenge/public projection.
- #1505 authentic Gateway/TVC input pair.
- #1504 four-hop InTr plus exact SKAP/KV readback.
- #1260 ecosystem runtime-evidence umbrella; observation context only, not lane ownership.

## README

Root README reviewed during successor registration. No repository-facing principle, runtime ownership, or authority model changed; no root README prose change is required.

## Manual work

None at registration. Do not place provider credentials, raw private-key material, Secure Enclave secrets, or exported key bytes in chat, GitHub, Drive, ordinary KV, logs, or screenshots.
