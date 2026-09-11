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
source_implementation_complete: true
native_invocation_source_complete: true
authentic_current_iphone_runtime_complete: false
```

## Why this dependency exists

Canonical reconciliation of `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` established that `.github` PR #1403 is merged and validated and that its source integration is complete. The remaining roundtrip predicates begin with one authentic current-device Gateway sidecar plus a matching TVC `canonical_roundtrip_eligible=true` drain receipt.

TVC PR #401 introduced the platform-neutral `stegverse.tvc.recipient-key-capability/v1` boundary and PR #402 reconciled Linux/root/systemd/Remote Desktop/second-device absence out of the universal architecture. The missing production capability was a current-iPhone Secure Enclave / `SecKey` recipient adapter and an authentic TVC challenge exchange.

That source gap is now closed. The remaining gap is authentic current-iPhone execution, not repository implementation.

## Implemented source chain

- StegOS #338 merged the Secure-Enclave-only P-256 candidate source.
- StegOS #339 compiled it into the StegOSMobile target with Apple-toolchain validation.
- StegOS #340 added challenge-bound proof-of-possession signing.
- TVC #407 merged the TVC-owned challenge issuer/verifier/adopter and existing Coinbase recipient-capability activation seam binding.
- StegOS #341 merged the bounded current-iPhone invocation surface through the existing `stegverse` URL scheme. It exposes only candidate materialization and TVC challenge signing, returns public-only evidence only to the exact HTTPS callback on `stegverse.org`, and rejects invalid/expired artifacts, key drift, authority drift, and unsupported callback destinations.

StegOS #341 exact head `710fc16d4c3c7cca07257e7575e8914859d76846` passed:

```text
StegOS CI                              34612835986 SUCCESS
GADI native boundary defense          34612835913 SUCCESS
iOS Device Package Validation         34612836055 SUCCESS
iOS Apple Toolchain Validation        34612835919 SUCCESS
```

StegOS #341 merged as `a43b203d7c6d738f8c571d64b1669bd6285fc9ff`.

## Required authentic execution

Source presence is not runtime proof. Close predicates in order:

```text
SOURCE_IMPLEMENTED = CLOSED
IOS_TARGET_INTEGRATED = CLOSED
BUILD_VALIDATED = CLOSED
NATIVE_INVOCATION_SOURCE = CLOSED
CURRENT_IPHONE_NON_EXPORTABLE_KEY_ACTIVATION_OBSERVED = OPEN
CURRENT_IPHONE_LIVENESS_MATCHES_ACTIVATION = OPEN
TVC_RECIPIENT_PUBLIC_CONFIG_PROJECTED = OPEN
```

The authentic exchange must produce one current-iPhone Secure Enclave candidate, one fresh TVC-issued bounded challenge, one proof-of-possession signature from the same opaque key handle, successful TVC verification/adoption, and the public recipient projection. No private-key bytes may be exported.

## Authority invariants

```text
TVC recipient capability
  -> protected key operation / activation / liveness evidence

StegOS Mobile
  -> host integration and bounded URL invocation only
  -> no raw key bytes
  -> no credential-authority minting
  -> no transition-authority minting

Interlock/InTr
  -> governed hop admission only

Canonical StegOS EVENT_EPHEMERAL lane
  -> runtime lease lifecycle only

GitHub / CI
  -> source validation and evidence only
```

The source chain grants no credential, transition, runtime, custody, provider, or GitHub authority. It creates no second runtime owner and introduces no hosted fallback or second user-operated device requirement.

## Current state

```text
PLATFORM_NEUTRAL_TVC_CAPABILITY_CONTRACT = MERGED
IOS_TVC_OPAQUE_KEY_ADAPTER = MERGED_AND_APPLE_TOOLCHAIN_VALIDATED
TVC_IOS_SIGNATURE_VERIFIER = MERGED_AND_VALIDATED
TVC_COINBASE_ACTIVATION_SEAM = SOURCE_BOUND
CURRENT_IPHONE_BOUNDED_URL_EXCHANGE = MERGED_AND_VALIDATED
AUTHENTIC_TVC_CHALLENGE_EXCHANGE = NOT_OBSERVED
AUTHENTIC_CURRENT_IPHONE_ACTIVATION = NOT_OBSERVED
TVC_PUBLIC_RECIPIENT_CONFIG_FROM_AUTHENTIC_EXCHANGE = NOT_OBSERVED
```

## Next

1. Invoke the merged StegOS Mobile bounded recipient-capability route on the current iPhone.
2. Retain the public candidate artifact and bind it to a fresh TVC-issued challenge.
3. Sign that exact challenge through the same Secure Enclave opaque key handle.
4. Verify/adopt the response through the merged TVC #407 path and project the public recipient configuration.
5. Return control to `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` only after those authentic predicates are evidenced, then continue to the Gateway/TVC input pair, TVC drain, four-leg Interlock/InTr traversal, and exact SKAP/KV readback.

## README

StegOS #341 updated its repository README with the bounded current-iPhone capability exchange. TVC #407 likewise updated the TVC README for the verifier/adopter path. The `.github` root README was reviewed during this coordination reconciliation; no additional organization-level principle or runtime contract changed, so no root README prose change is required here.

## Manual work

None at this coordination stage. Do not enter provider credentials, key material, private-key bytes, or Secure Enclave secrets into chat, GitHub, ordinary KV, logs, screenshots, or repository state.
