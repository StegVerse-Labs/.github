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
```

## Why this dependency exists

Canonical reconciliation of `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` established that `.github` PR #1403 is merged and validated and that its source integration is complete. The remaining roundtrip predicates begin with one authentic current-device Gateway sidecar plus a matching TVC `canonical_roundtrip_eligible=true` drain receipt.

TVC PR #401 introduced the platform-neutral `stegverse.tvc.recipient-key-capability/v1` boundary and PR #402 reconciled Linux/root/systemd/Remote Desktop/second-device absence out of the universal architecture. The only concrete production adapter currently present is still the Linux root-protected PEM adapter. Repository-wide source search found no existing Apple Secure Enclave / `SecKey` recipient adapter.

Therefore current-iPhone execution cannot honestly produce the authentic recipient activation/liveness evidence yet. This task is the bounded remediation. It must not create a second runtime owner or reassign TV/TVC credential authority to StegOS.

## Required implementation

Use the existing StegOS Mobile iOS target under:

```text
StegVerse-Labs/StegOS/mobile/ios/StegOSMobile.xcodeproj
StegVerse-Labs/StegOS/mobile/ios/StegOSMobile/
```

Implement a TVC-owned mobile recipient capability with these properties:

1. Create or resolve a P-256 private key through Apple Security APIs using a non-exportable Secure Enclave-backed handle when supported by the current device.
2. Namespace the key as TVC recipient capability state; StegOS Mobile hosts the adapter but does not gain credential authority.
3. Export only the public key/JWK-equivalent material required for recipient projection plus non-secret identifiers, lease metadata, and an opaque `tvc-capability://` handle.
4. Emit activation and liveness evidence compatible with the semantic checks already enforced by `StegVerse-Labs/TVC/scripts/tvc_recipient_key_capability.py`.
5. Keep raw private-key bytes unavailable to StegOS Mobile application state, ordinary KV, repository state, logs, screenshots, argv, and provider payloads.
6. Fail closed if required non-exportability/Secure Enclave semantics are unavailable for production proof. Do not silently substitute an exportable software key.
7. Bind the mobile capability into the existing TVC Coinbase capability activation seam; do not open routes, grant InTr authority, or start provider operations from the adapter.
8. Preserve the existing canonical EVENT_EPHEMERAL StegOS runtime owner and the existing TVC activation owner.

## Validation levels

Source presence is not runtime proof. Close predicates in order:

```text
SOURCE_IMPLEMENTED
-> IOS_TARGET_INTEGRATED
-> BUILD_VALIDATED
-> CURRENT_IPHONE_NON_EXPORTABLE_KEY_ACTIVATION_OBSERVED
-> CURRENT_IPHONE_LIVENESS_MATCHES_ACTIVATION
-> TVC_RECIPIENT_PUBLIC_CONFIG_PROJECTED
```

Only after authentic current-iPhone activation/liveness may the parent task continue to Gateway sidecar creation, TVC stage drain, four-leg Interlock/InTr traversal, SKAP/KV exact readback, and `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`.

## Authority boundary

```text
TVC recipient capability
  -> protected key operation / activation / liveness evidence

StegOS Mobile
  -> host integration only
  -> no raw key bytes
  -> no credential-authority minting
  -> no transition-authority minting

Interlock/InTr
  -> governed hop admission only

Canonical StegOS EVENT_EPHEMERAL lane
  -> runtime lease lifecycle only
```

## Current state

```text
PLATFORM_NEUTRAL_TVC_CAPABILITY_CONTRACT = MERGED
LINUX_ROOT_ADAPTER = PRESENT
NATIVE_IOS_PROJECT = PRESENT
IOS_TVC_OPAQUE_KEY_ADAPTER = MERGED_AND_APPLE_TOOLCHAIN_VALIDATED\nTVC_IOS_SIGNATURE_VERIFIER = MERGED_AND_VALIDATED\nTVC_COINBASE_ACTIVATION_SEAM = SOURCE_BOUND\nAUTHENTIC_TVC_CHALLENGE_EXCHANGE = NOT_OBSERVED
AUTHENTIC_CURRENT_IPHONE_ACTIVATION = NOT_OBSERVED
```

## Next

Source implementation and validation are complete through StegOS #338/#339/#340 and TVC #407. Next obtain one authentic current-iPhone Secure Enclave candidate plus TVC-issued challenge/attestation exchange, verify it through the merged TVC adapter, and project the public recipient configuration. After that, return control to `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` for the authentic Gateway/TVC input pair and canonical four-leg roundtrip.

## README

The functional implementation is documented in the StegOS and TVC repository README/handoff surfaces. This coordination projection updates the organization README because implementation has now landed in both owning repositories.

## Manual work

None at this coordination stage. Do not enter provider credentials, key material, or private-key bytes into chat, GitHub, ordinary KV, logs, screenshots, or repository state.


## Validated merged source lineage

- StegOS #338 merged the Secure-Enclave-only P-256 candidate source.
- StegOS #339 compiled it into the StegOSMobile target with Apple-toolchain validation.
- StegOS #340 added challenge-bound proof-of-possession signing and passed exact-head StegOS CI, iOS Device Package Validation, and iOS Apple Toolchain Validation.
- TVC #407 merged at `3fbdba0cb539b3672b53c3aa29e948e58e4fdb8e`; the dedicated recipient-capability suite, credential-model consistency validation, and consent HTTP validation all passed at exact head `704f064a6fb07b6c72076b4ced68851fe7e84ea1`.

These results close source implementation, target integration, Apple-toolchain build, TVC signature-verification, and Coinbase activation-seam binding. They do not close physical current-iPhone execution or runtime evidence.
