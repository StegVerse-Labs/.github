# TVC iOS Opaque Recipient Capability Mirror Handoff

Updated: 2026-09-11

```text
goal_id: TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001
parent_goal: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
cosv_id: 50000000102000
state: ACTIVE
checkout_state: CHECKED_OUT
credential_capability_owner: StegVerse-Labs/TVC
mobile_host_integration_owner: StegVerse-Labs/StegOS
roundtrip_consumer: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
credential_authority: TV/TVC
transition_authority: Interlock/InTr
github_runtime_authority: NONE
hosted_runtime_fallback: NONE
second_user_operated_device_required: false
source_implemented: true
source_validated: true
authentic_runtime_observed: false
```

## Goal

Materialize and authenticate one real current-iPhone TVC recipient capability using a non-exportable P-256 Secure Enclave key while preserving TV/TVC credential authority, Interlock/InTr transition authority, no private-key export, and the existing StegOS canonical runtime owner.

## Merged implementation lineage

- StegOS #338: Secure-Enclave-only P-256 candidate source.
- StegOS #339: candidate compiled into the StegOSMobile target.
- StegOS #340: challenge-bound proof-of-possession signing.
- TVC #407: TVC verifier/adopter and Coinbase activation-seam binding.
- TVC #408 merged at `8aa8eb084c3348e2565f81ca5d2e27044a5a4421`: authenticated runtime-facing adopter requiring a signed TVC admission plus explicit TVC authority public JWK. Unsigned, wrong-anchor, stale/tampered, and broken challenge/admission bindings fail closed. Validation run `34613199534` succeeded.
- StegOS #343 merged at `0f3980ae29273b4dd131e6831034f11b7cde0df3`: authenticated admission verifier compiled into StegOSMobile. Exact-head StegOS CI `34613115673`, iOS Device Package `34613115670`, and Apple Toolchain `34613115687` all succeeded.

No production TVC signing private key or trust anchor is embedded in source. No private iPhone recipient-key bytes are exported.

## Current runtime gate

Source implementation is complete through authenticated admission verification. Authentic execution now requires:

```text
TVC-controlled production recipient-admission signing-key custody
-> canonical distribution of matching TVC authority public JWK
-> fresh signed admission bound to exact WorkerCoordinator fence + bounded lease
-> StegOSMobile admission verification
-> Secure Enclave key operation on the current iPhone
-> TVC challenge verification/adoption
-> public recipient configuration projection
```

The source must fail closed until the trust anchor is supplied through the canonical TVC-controlled path. GitHub, CI, model output, ordinary KV, and repository state are not permitted to mint or custody the production signing private key.

CMC-028 is not reused as a signing-authority mint. Its current registered worker is evidence/observation only and explicitly cannot grant key custody, issuance, signing, credential, claim, fence, or heartbeat authority.

## Evidence state

```text
SOURCE_IMPLEMENTED = true
IOS_TARGET_INTEGRATED = true
APPLE_TOOLCHAIN_BUILD_VALIDATED = true
AUTHENTICATED_ADMISSION_VERIFIER_MERGED = true
UNSIGNED_ADMISSION_FAILS_CLOSED = true
WRONG_ANCHOR_FAILS_CLOSED = true
TVC_PRODUCTION_ADMISSION_SIGNING_CUSTODY_OBSERVED = false
TVC_AUTHORITY_PUBLIC_JWK_BOUND = false
FRESH_AUTHENTIC_SIGNED_ADMISSION_OBSERVED = false
CURRENT_IPHONE_SECURE_ENCLAVE_EXECUTION_OBSERVED = false
AUTHENTIC_TVC_CHALLENGE_EXCHANGE_OBSERVED = false
TVC_PUBLIC_RECIPIENT_CONFIG_PROJECTED = false
```

## Next

1. Resolve or observe production TVC-controlled admission-signing custody outside GitHub/CI/model state.
2. Bind/distribute only its matching public JWK through the canonical TVC-controlled trust path.
3. Issue one fresh signed admission for the exact current WorkerCoordinator fence/lease.
4. Run the compiled StegOSMobile authenticated verifier and Secure Enclave operation on the current iPhone.
5. Complete TVC challenge verification/adoption and project the public recipient config.
6. Return control to `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` for Gateway/TVC pair creation and four-leg roundtrip proof.

## Authority boundary

- TV/TVC remains credential authority.
- Interlock/InTr remains transition authority.
- StegOS Mobile is a host/integration surface, not authority.
- GitHub/CI/Heartbeat are validation/evidence surfaces only.
- No hosted runtime fallback or second user-operated device is authorized.

## README

The parent and owning-repository README principles remain accurate. This reconciliation changes only the authentic runtime/evidence gate, so no README prose change is required.

## Manual work

None at this stage. Do not enter provider credentials. Do not create/export the TVC authority signing private key in GitHub/CI. Do not manually create or export the iPhone recipient private key.
