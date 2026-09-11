# Device <-> KV <-> SKAP Roundtrip Mirror Handoff

Updated: 2026-09-11

```text
goal_id: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
parent_goal: KV-CONNECTION-REVALIDATION-WORKER-001
cosv_id: 50000000102000
state: ACTIVE
checkout_state: CHECKED_OUT
canonical_owner: StegVerse-Labs/.github
implementation_owner: StegVerse-Labs/StegOS
canonical_runtime_lifecycle_owner: StegVerse-Labs/StegOS/stegos/canonical_runtime_lane.py
domain_binding_owner: StegVerse-Labs/StegOS/stegos/device_kv_skap_canonical_runtime.py
worker_entrypoint: workers/run_device_kv_skap_canonical_runtime_worker.py
worker_claim_authority: WorkerCoordinator
transition_authority: Interlock/InTr
credential_authority: TV/TVC
github_runtime_authority: NONE
hosted_runtime_fallback: NONE
second_user_operated_device_required: false
source_integration_complete: true
authentic_runtime_complete: false
```

## Goal

Prove one authentic sovereign operation lineage:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

Completion requires four adjacent canonical InTr receipts, exact packet/readback verification, one continuous receipt-hash chain, authentic retained-Node continuity, a fresh WorkerCoordinator claim/fence, canonical EVENT_EPHEMERAL lease evidence, TV/TVC credential authority, no secret plaintext in ordinary KV/device/repository state, no authority transfer, no hosted fallback, and no second user-operated device.

## Authority and runtime ownership

- Canonical Runtime Lane owns runtime lease lifecycle, evidence retention, and teardown.
- WorkerCoordinator owns fresh task claim/fence.
- Interlock/InTr owns governed transition admission.
- TV/TVC owns credential authority and remains the single SKAP ciphertext custody writer.
- StegOS Mobile may host the iOS adapter but does not mint credential or transition authority.
- GitHub/CI/Heartbeat provide source validation, evidence transport, and observation only.

No open lease, repository record, CI run, model output, or public-key projection grants signing, transition, credential, or runtime authority.

## Merged source lineage relevant to current execution

Canonical roundtrip/source integration is already merged through StegOS #326/#332/#333/#334/#335/#336, `.github` #1332/#1339/#1352/#1371/#1399/#1400/#1401/#1403, LLM-adapter #331, and TVC #377.

Current-iPhone recipient-capability source lineage is now:

- StegOS #338: Secure-Enclave-only P-256 candidate source.
- StegOS #339: candidate compiled into the StegOSMobile target.
- StegOS #340: TVC challenge-bound proof-of-possession signer.
- TVC #407: TVC-owned verifier/adopter bound into the existing Coinbase recipient-capability activation seam.
- TVC #408 merged at `8aa8eb084c3348e2565f81ca5d2e27044a5a4421`: canonical authenticated iOS recipient-adoption wrapper requiring a signed TVC admission plus an explicitly supplied TVC authority public JWK. Unsigned, wrong-anchor, stale/tampered, or challenge-mismatched admission fails closed. Validation run `34613199534` succeeded after freshness-binding repair.
- StegOS #343 merged at `0f3980ae29273b4dd131e6831034f11b7cde0df3`: compiled authenticated-admission verifier in StegOSMobile. Exact-head StegOS CI `34613115673`, iOS Device Package `34613115670`, and Apple Toolchain `34613115687` succeeded.

These source and CI results do not constitute authentic current-iPhone execution or the Device->KV->SKAP->KV->Device proof.

## Canonical execution chain

```text
fresh WorkerCoordinator invocation
-> authentic retained Node
-> authentic Universal InTr materialization
-> canonical LEASE_OPEN snapshot
-> exact lease / claim / fence binding
-> authenticated TVC recipient admission verification
-> current-iPhone Secure Enclave recipient operation
-> authentic Gateway sidecar
-> TVC canonical roundtrip-eligible drain receipt
-> four canonical Interlock/InTr hops
-> exact SKAP/KV return readback
-> DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED
-> evidence retained before lease teardown
```

## Current authenticated-admission gate

The unsigned-admission consumer gap is closed in source. Runtime-facing adoption now fails closed unless all of the following are true:

```text
1. TVC-controlled production admission signing-key custody exists outside GitHub/CI/model state.
2. Its matching public trust anchor is distributed through the canonical TVC-controlled path.
3. A fresh signed stegverse.tvc.recipient-capability-admission/v1 is issued for the exact bounded WorkerCoordinator fence/lease context.
4. StegOSMobile verifies that admission against the exact supplied TVC authority public JWK before Secure Enclave key use.
5. TVC verifies the current-iPhone liveness/challenge response and adopts the capability.
```

Do not create the TVC authority private key in GitHub, CI, ordinary KV, chat, logs, screenshots, or repository state. Do not manually materialize the iPhone recipient private key. Do not treat CMC-028 repository evidence as authority issuance: CMC-028 remains an evidence/custody observation lane and does not mint this recipient-admission signing authority.

## Current authentic evidence conditions

```text
TVC_PRODUCTION_RECIPIENT_ADMISSION_SIGNING_CUSTODY_NOT_YET_OBSERVED
TVC_RECIPIENT_ADMISSION_PUBLIC_TRUST_ANCHOR_NOT_YET_BOUND
AUTHENTIC_SIGNED_RECIPIENT_ADMISSION_NOT_YET_OBSERVED
AUTHENTIC_CURRENT_IPHONE_SECURE_ENCLAVE_EXECUTION_NOT_YET_OBSERVED
AUTHENTIC_TVC_CHALLENGE_ADOPTION_NOT_YET_OBSERVED
AUTHENTIC_CURRENT_DEVICE_GATEWAY_SIDECAR_NOT_YET_OBSERVED
AUTHENTIC_TVC_CANONICAL_ROUNDTRIP_ELIGIBLE_DRAIN_RECEIPT_NOT_YET_OBSERVED
AUTHENTIC_FOUR_LEG_INTR_ROUNDTRIP_NOT_YET_OBSERVED
AUTHENTIC_SKAP_KV_RETURN_RECEIPT_NOT_YET_OBSERVED
KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED
```

The absence of an always-on receiver, TestFlight deployment, Remote Desktop, a second device, or hosted runtime remains non-blocking for this proof.

## Next

1. Resolve/observe TVC-controlled production admission-signing custody and its canonical public trust-anchor projection without creating authority in GitHub/CI.
2. Issue one fresh signed admission bound to the exact current WorkerCoordinator fence/lease context.
3. Execute the compiled StegOSMobile authenticated verifier and Secure Enclave path on the current iPhone.
4. Complete TVC challenge verification/adoption and project the public recipient configuration.
5. Produce the authentic Gateway sidecar plus matching TVC `ADMITTED_TO_SKAP_VAULT_CUSTODY` / `canonical_roundtrip_eligible=true` receipt.
6. Execute the registered WorkerCoordinator -> StegOS canonical lane through all four InTr hops and exact readback.
7. Claim completion only after terminal verification returns `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED` with retained evidence.

## README

Root `README.md` was reviewed for this reconciliation. No repository-facing framework principle changed; this update narrows the authentic runtime/evidence gate, so no README prose change is required.

## Manual work

None at this stage. Do not enter provider credentials yet. Do not create or export the TVC authority private key through GitHub/CI. Do not manually materialize or export the iPhone recipient private key.
