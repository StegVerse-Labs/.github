# TVC Recipient Admission Opaque Signer Backend Mirror Handoff

Updated: 2026-09-12

```text
goal_id: TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001
parent_goal: TVC-RECIPIENT-ADMISSION-SIGNING-CUSTODY-001
root_goal: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
cosv_id: 50000000102000
state: ACTIVE
checkout_state: CHECKED_OUT
user_verification_authority: KV/SKAP Vault
credential_authority: TV/TVC
transition_authority: Interlock/InTr
device_role: INTERCHANGEABLE_STEGOS_TRANSPORT_NODE
```

## Canonical architecture

KV/SKAP Vault is the sole user verifier. StegOS devices are interchangeable transport/execution nodes. Device identity, node identity, transport identity, Secure Enclave presence, local key possession, GitHub, HeartBeat, or model output cannot become user-verifier authority.

TVC credential/capability admission and Interlock/InTr transition admission remain distinct. A TVC-signed capability admission may name `transitionAuthority=Interlock/InTr`, but its own source explicitly does not grant Interlock/InTr transition authority and cannot substitute for an authentic InTr admission receipt.

## Current truth

- Opaque vault-agent signing protocol, existing `/run/stegverse/vault-agent.sock` dispatch, TVC caller consolidation, and the role-separated non-exportable P-256 authority-key candidate are merged.
- `PlatformOpaqueRecipientAdmissionSigner` remains merged at `6a42422d1faf2449f18f98efcd6b0c61bd0bb733`.
- StegOS PR #358 merged the platform-neutral KV/SKAP + InTr local-operation binder at `d39477a0a175c175266fe31fe0a2862323895ec9` after StegOS CI `34721268779` passed.
- `stegfin-governance` PR #104 merged `KVSKAPAdmittedNodePlatformTransport` at `1e592bd6c385e79411ac72229ae9fd12a70411c9` after iOS first-passkey `34721416782`, Governance `34721416818`, and StegWallet governance `34721416838` passed.
- TVC PR #419 merged provider-neutral already-verified KV/SKAP provenance projection at `4c78f8653b8a5899350479d57c58e936b50e023a` after TVC Recipient Capability Validation `34721637270` passed. It performs no WebAuthn, creates no verification, and exposes no verification material.
- `.github` PR #1633 merged the dedicated recipient-admission signing Universal InTr source route at `08178861cfa144ce032d9399d50c56a77bd1a74b` after organization-control `34721877459`, deterministic suite `34721877447`, and Heartbeat `34721877451` passed.
- That source reuses the existing Universal InTr listener. `build_tvc_recipient_admission_sign_intr_request.py` can only build a `NONE_REQUEST_ONLY` request. `tvc_recipient_admission_sign_intr_ingress.py`, when invoked by the shared listener, can emit one write-once `INGRESS_ADMITTED` receipt with `authority_effect=INGRESS_TRANSITION_ONLY`, exact platform-request/key/JWK/message/nonce bindings, and no runtime execution or user verification.
- The route installer is idempotent and fail-closed and creates no second listener. Source merge/installability does not prove the route is installed in an authentic resident runtime or that an authentic receipt exists.
- `stegfin-governance` PR #105 merged `UniversalInTrCurrentAdmissionProvider` at `0980ca24f3acc4ed9a26cd24e433276d37c72911` after Governance `34721959961`, iOS first-passkey `34721960023`, and StegWallet governance `34721959977` passed.
- The current-InTr provider is read/projection-only. It requires the exact materialization request + payload + `INGRESS_ADMITTED` receipt, recomputes all hashes/bindings, enforces a bounded freshness window, rejects runtime-execution/user-verification creation, and projects only `admissionRef`/`admissionSHA256` into the generic provider shape.
- The current-InTr provider explicitly rejects a signed TVC recipient-capability admission substituted for the InTr ingress receipt.
- Current applicable KV/SKAP record selection/runtime provider binding remains unresolved. Authentic Universal InTr runtime route installation and an exact current receipt evidence source remain unobserved.
- Canonical Runtime interchangeable-node carrier binding, local P-256 authority invocation, production vault-agent launcher injection, authority-key materialization, public-JWK trust-anchor binding, and fresh signed-admission runtime evidence remain unobserved.

## Source-complete portions

```text
opaque vault-agent signing protocol
single existing vault-agent caller path
role-separated non-exportable P-256 authority-key candidate
KV/SKAP sole-user-verifier invariant
provider-neutral already-verified KV/SKAP provenance projection
platform-neutral KV/SKAP + InTr node-local operation binding
vault-agent platform request -> KV/SKAP/InTr/interchangeable-node transport adaptation
Universal InTr signing-operation request builder
shared-listener signing-operation ingress adapter
write-once exact-bound InTr admission receipt schema
idempotent shared-listener route installer
fresh exact InTr receipt -> CurrentInTrAdmissionProvider projection
explicit rejection of TVC capability admission as InTr transition evidence
no user verification performed by node/transport/projectors
no duplicate listener or signer daemon
```

These source merges do not prove current production user-verification state, runtime route installation, authentic current InTr receipt availability, node carriage, local P-256 invocation, production key materialization, public trust-anchor binding, or signing.

## Exact remaining problem

The generic and source-level InTr path now exists without authority conflation. Remaining work is concrete runtime binding:

```text
current applicable KV/SKAP owner-verification + admitted receipt
  -> provenance projector
  -> runtime KVSKAPVerificationProvenanceProvider

exact platform sign request
  -> Universal InTr request
  -> authentic existing shared Universal InTr listener
  -> current write-once INGRESS_ADMITTED receipt
  -> read-only CurrentInTrAdmissionEvidenceSource
  -> UniversalInTrCurrentAdmissionProvider

both current artifacts
  -> KVSKAPAdmittedNodePlatformTransport
  -> existing Canonical Runtime interchangeable-node carrier
  -> kv_skap_verified_local_operation + one-time replay protector
  -> eligible local opaque role-separated P-256 authority capability
```

No component may select a durable trusted device or create a second verifier. Source availability must not be promoted into runtime receipt evidence.

## Invariants

```text
KV/SKAP Vault is the sole user verifier
StegOS devices are interchangeable transport nodes
TVC capability admission != Interlock/InTr transition admission
node/device/transport identity is not user-verifier authority
SKAP custody/readback alone is not user verification
local key possession / Secure Enclave presence is not user verification
TV/TVC remains credential/signing authority
Interlock/InTr remains transition authority
WorkerCoordinator remains claim/fence authority
existing /run/stegverse/vault-agent.sock remains the credential process boundary
existing Universal InTr listener remains the transition ingress process
no second signer daemon, listener, or alternate credential path
production authority private key is non-exportable
public trust anchor contains public material only
```

## Next

1. Bind current applicable KV/SKAP record selection to a concrete read-only runtime provenance provider; reject arbitrary historical SKAP receipts.
2. Bind `CurrentInTrAdmissionEvidenceSource` to the existing Universal InTr runtime receipt/payload/request locations for the exact platform request hash; do not synthesize receipt state.
3. Reuse the existing Canonical Runtime/node-event path for `InterchangeableStegOSNodeCarrier`, with no durable device pin.
4. Feed exact current KV/SKAP + InTr state through `kv_skap_verified_local_operation` and one-time replay protection.
5. Connect successful local-operation binding to the eligible node-local opaque P-256 authority capability.
6. Inject the completed backend into the existing vault-agent launcher only when all concrete bindings are fail-closed and available.
7. Materialize one production authority key on an eligible node, project only public JWK/key ID, bind the trust anchor, and observe one fresh WorkerCoordinator-bound signed admission.

## README review

Organization, StegOS, stegfin-governance, and TVC README/handoff authority topology was reviewed. These slices reuse existing shared Universal InTr and KV/SKAP authority ownership and do not require a broad README topology rewrite.

## Manual work

None. Production private-key, credential, assertion, biometric, or authenticator material must not be placed in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or model output.
