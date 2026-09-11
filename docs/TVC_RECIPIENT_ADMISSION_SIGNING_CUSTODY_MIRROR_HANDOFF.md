# TVC Recipient Admission Signing Custody Mirror Handoff

Updated: 2026-09-11

```text
goal_id: TVC-RECIPIENT-ADMISSION-SIGNING-CUSTODY-001
parent_goal: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
cosv_id: 50000000102000
state: ACTIVE
checkout_state: CHECKED_OUT
canonical_owner: StegVerse-Labs/.github
implementation_owner: StegVerse-Labs/TVC
credential_authority: TV/TVC
transition_authority: Interlock/InTr
github_runtime_authority: NONE
hosted_runtime_fallback: NONE
second_user_operated_device_required: false
```

## Goal

Close the remaining authentic authority boundary required by TVC #408 and StegOS #343: establish TVC-controlled production custody for the P-256 recipient-admission signing key, derive and bind the matching public JWK trust anchor, then permit issuance of a fresh WorkerCoordinator-fence/lease-bound `stegverse.tvc.recipient-capability-admission/v1` without exporting private-key bytes or granting GitHub/CI/model authority.

## Current truth

- TVC #408 merged at `8aa8eb084c3348e2565f81ca5d2e27044a5a4421`; validation run `34613199534` succeeded.
- StegOS #343 merged at `0f3980ae29273b4dd131e6831034f11b7cde0df3`; StegOS CI `34613115673`, iOS Device Package `34613115670`, and Apple Toolchain `34613115687` succeeded.
- Runtime-facing recipient adoption now fails closed on unsigned, stale/tampered, wrong-anchor, or incorrectly bound admission.
- Production TVC admission-signing private-key custody has not been authentically observed.
- The matching canonical public JWK trust anchor has not been authentically bound/distributed.
- No fresh production signed admission, physical current-iPhone Secure Enclave adoption, Gateway/TVC pair, four-hop InTr roundtrip, or exact SKAP/KV readback is claimed.

## Authority invariants

```text
TV/TVC
  -> sole recipient-admission signing authority
  -> owns production signing-key custody
  -> publishes only matching public trust-anchor material

GitHub / CI / Heartbeat / model
  -> source validation / coordination / observation only
  -> MUST NOT create, reconstruct, escrow, or receive the production private key

StegOS Mobile
  -> verifies signed admission and hosts recipient Secure Enclave operations
  -> MUST NOT mint TVC signing authority

Interlock/InTr
  -> transition admission only
```

## Required authentic predicates

```text
TVC_PRODUCTION_RECIPIENT_ADMISSION_SIGNING_CUSTODY_OBSERVED
TVC_RECIPIENT_ADMISSION_PUBLIC_TRUST_ANCHOR_BOUND
FRESH_SIGNED_RECIPIENT_ADMISSION_BOUND_TO_EXACT_WORKER_FENCE_AND_LEASE
PRIVATE_SIGNING_KEY_BYTES_NEVER_EXPORTED
GITHUB_CI_MODEL_HAVE_NO_SIGNING_AUTHORITY
```

Only after those predicates are satisfied may `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001` proceed with authentic current-iPhone Secure Enclave candidate/challenge adoption and public recipient projection.

## Next

1. Inspect existing TVC credential/key-custody primitives for an eligible production non-exportable signing-key owner; reuse one if it preserves the authority invariants.
2. If no eligible primitive exists, implement the smallest TVC-owned secure-custody adapter without creating key material in GitHub/CI or ordinary repository state.
3. Bind the matching public JWK as the canonical verification anchor for TVC #408 / StegOS #343.
4. Validate source behavior with non-production test vectors only.
5. Require authentic TVC-controlled runtime materialization before issuing a production signed admission.

## README

The `.github` README must be reviewed with this task. No README claim should imply production signing custody or runtime completion without evidence.

## Manual work

None at this stage. Do not create or paste the production authority private key in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or repository state. Do not enter provider credentials yet.
