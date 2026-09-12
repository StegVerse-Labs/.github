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
source_implementation_complete: true
source_validation_complete: true
authentic_runtime_complete: false
```

## Goal

Close the remaining authentic authority boundary required by TVC #408 and StegOS #343: establish TVC-controlled production custody for the P-256 recipient-admission signing key, derive and bind the matching public JWK trust anchor, then permit issuance of a fresh WorkerCoordinator-fence/lease-bound `stegverse.tvc.recipient-capability-admission/v1` without exporting private-key bytes or granting GitHub/CI/model authority.

## Current merged source state

- TVC #408 merged at `8aa8eb084c3348e2565f81ca5d2e27044a5a4421`; validation run `34613199534` succeeded.
- StegOS #343 merged at `0f3980ae29273b4dd131e6831034f11b7cde0df3`; StegOS CI `34613115673`, iOS Device Package `34613115670`, and Apple Toolchain `34613115687` succeeded.
- TVC #410 merged at `f7124a2f0a60a3474a1f8868fb3b03e8821c1e38` after exact-head signer validation run `34670427194` succeeded.
- TVC now contains `scripts/tvc_recipient_admission_resident_signer.py`, which binds the existing signed-admission contract to an opaque resident signing boundary rather than a private-key path.
- The adapter requires a protected local UNIX signing socket, accepts a public P-256 JWK only, verifies each returned signature locally, rejects private JWK input, rejects wrong signatures, and projects only public trust-anchor material.
- Source/CI do not prove an authentic production signer exists behind that socket.

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

The merged signer adapter does not accept private-key bytes, private JWK, seed/scalar material, or a production private-key path. The authentic signer may be backed by a TVC-controlled non-exportable local provider, but its private key remains outside GitHub, CI, chat, repository state, ordinary KV, logs, screenshots, and model-visible state.

## Source predicates now closed

```text
OPAQUE_SIGNER_CLIENT_SOURCE_IMPLEMENTED
PRIVATE_KEY_INPUT_SURFACE_ABSENT
PUBLIC_TRUST_ANCHOR_PROJECTION_IMPLEMENTED
RETURNED_SIGNATURE_VERIFIED_LOCALLY
WRONG_SIGNATURE_FAILS_CLOSED
PRIVATE_JWK_FAILS_CLOSED
SOURCE_VALIDATION_SUCCESS
```

## Authentic predicates still open

```text
TVC_PRODUCTION_RECIPIENT_ADMISSION_SIGNING_CUSTODY_OBSERVED
TVC_RECIPIENT_ADMISSION_PUBLIC_TRUST_ANCHOR_BOUND
FRESH_SIGNED_RECIPIENT_ADMISSION_BOUND_TO_EXACT_WORKER_FENCE_AND_LEASE
PRIVATE_SIGNING_KEY_BYTES_NEVER_EXPORTED
GITHUB_CI_MODEL_HAVE_NO_SIGNING_AUTHORITY
```

Only after those predicates are satisfied may `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001` proceed with authentic current-iPhone Secure Enclave candidate/challenge adoption and public recipient projection.

## Next

1. Materialize or observe an authentic TVC-controlled opaque/non-exportable production signer at the merged resident boundary outside GitHub/CI.
2. Project that signer's matching public P-256 JWK through the merged public trust-anchor artifact.
3. Retain evidence that private signing-key bytes were never exported and that GitHub/CI/model have no signing authority.
4. Issue one fresh admission bound to the exact WorkerCoordinator claim/fence and bounded lease.
5. Return control to `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001` for current-iPhone Secure Enclave challenge/adoption, then to the parent roundtrip for Gateway/TVC input pairing and four-hop proof.

## README

The TVC README was reviewed for authority consistency; no production runtime completion is claimed. The `.github` README remains unchanged because the organization-level authority model did not change.

## Manual work

None at this stage. Do not create or paste the production authority private key in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or repository state. Do not enter provider credentials yet.
