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

TVC credential/capability admission and Interlock/InTr transition admission remain distinct. A TVC-signed capability admission may name `transitionAuthority=Interlock/InTr`, but cannot substitute for an authentic InTr admission receipt.

## Current source truth

The existing source chain is now complete through the node-local signing primitive:

```text
PlatformOpaqueRecipientAdmissionSigner
  -> KVSKAPAdmittedNodePlatformTransport
  -> already-verified KV/SKAP provenance + current InTr admission
  -> interchangeable StegOS node operation bundle
  -> kv_skap_verified_local_operation + one-time replay protection
  -> existing NodeEventExecutionBroker capability adapter
  -> injected opaque P-256 authority capability
  -> native role-separated Secure Enclave authority signer
```

Merged evidence:

- Opaque vault-agent signing protocol and the existing `/run/stegverse/vault-agent.sock` dispatch are merged; no second signer socket or credential path is authorized.
- `PlatformOpaqueRecipientAdmissionSigner` remains merged at `StegVerse-Labs/stegfin-governance@6a42422d1faf2449f18f98efcd6b0c61bd0bb733`.
- StegOS role-separated non-exportable P-256 authority-key candidate remains merged at `e81b981c1218fca2031a43207afd0a419ff1263d`.
- StegOS PR #358 merged the platform-neutral KV/SKAP + InTr local-operation binder at `d39477a0a175c175266fe31fe0a2862323895ec9`; StegOS CI `34721268779` passed.
- `stegfin-governance` source already contains `KVSKAPAdmittedNodePlatformTransport`; canonical provenance remains the earlier merged owner recorded in the task (`1e592bd6c385e79411ac72229ae9fd12a70411c9`). This session also validated the same architecture-aligned transport shape through PR #106; no duplicate authority is inferred from that later compatible merge.
- TVC provider-neutral already-verified KV/SKAP provenance projection remains merged at `4c78f8653b8a5899350479d57c58e936b50e023a`.
- The dedicated recipient-admission signing Universal InTr source route remains merged in `.github` at `08178861cfa144ce032d9399d50c56a77bd1a74b`; source installability does not prove resident route installation or a live receipt.
- `UniversalInTrCurrentAdmissionProvider` remains merged at `0980ca24f3acc4ed9a26cd24e433276d37c72911`; it is read/projection-only and requires an exact fresh `INGRESS_ADMITTED` receipt.
- StegOS PR #359 merged `TVCRecipientAdmissionNodeCapability` at `8b3b83532b26333570369884a270481f48aeaeef`. It reuses the existing `NodeEventExecutionBroker`, consumes the canonical local-operation binder, validates exact key/JWK/message bindings, and invokes an injected opaque P-256 capability. It performs no user verification, creates no runtime lifecycle, and selects no permanent device.
- A current-main Device Continuity wording/test drift exposed by PRs #359/#360 was repaired separately in StegOS PR #361 at `622ab94a7698eacec4993985e870d8f12158baf8`; StegOS CI `34722527570` passed. That repair changes no authority or runtime semantics.
- StegOS PR #360 merged the native bound authority signer at `ad05e62f0d84549e511b6ebd047bb8091a3b0ce7`. Exact head `2e6010a3ff6c4775abb12e783097e67427ff1c4e` passed StegOS CI `34722630460`, iOS Apple Toolchain Validation `34722630468`, and iOS Device Package Validation `34722630448`.
- The native signer lives in the already-compiled `TVCAuthenticatedRecipientCapability.swift`. It consumes only an already-successful KV/SKAP+InTr bound operation plus the exact original platform sign request, rechecks key ID/public-JWK/message/nonce/time equality, re-derives the role-separated authority Secure Enclave key identity, and calls `SecKeyCreateSignature(.ecdsaSignatureMessageX962SHA256)` only for that exact message.
- No `SIGN_RECIPIENT_ADMISSION` or `MATERIALIZE_AUTHORITY_KEY` public deep-link action was added. The public recipient-capability URL path remains unrelated to authority signing.
- The native signer returns no private-key material, does not reuse the recipient key, performs no user verification, and keeps device/node/transport verifier authority at `NONE`.

## Source-complete portions

```text
opaque vault-agent signing protocol
single existing vault-agent caller path
role-separated non-exportable P-256 authority-key candidate
KV/SKAP sole-user-verifier invariant
provider-neutral already-verified KV/SKAP provenance projection
platform-neutral KV/SKAP + InTr node-local operation binding
vault-agent platform request -> KV/SKAP/InTr/interchangeable-node transport adaptation
Universal InTr signing-operation request builder + shared-listener ingress source
fresh exact InTr receipt -> CurrentInTrAdmissionProvider projection
existing NodeEventExecutionBroker recipient-admission capability adapter
exact bound-operation replay/key/JWK/message checks
native role-separated Secure Enclave bound signing primitive
no user verification performed by node/transport/projectors/native signer
no permanent device pin
no public authority-signing deep link
no duplicate listener or signer daemon
```

These source merges do not prove current production user-verification state, authentic resident Universal InTr receipt availability, actual broker-to-native device interop, vault-agent launcher injection, production authority-key materialization, public trust-anchor binding, or a production signature.

## Exact remaining problem

The remaining work is runtime/integration binding rather than a new verifier or a new signing algorithm:

```text
current applicable KV/SKAP owner-verification record
  -> concrete read-only KVSKAPVerificationProvenanceProvider

exact platform sign request
  -> authentic installed shared Universal InTr route
  -> current write-once INGRESS_ADMITTED receipt
  -> concrete CurrentInTrAdmissionEvidenceSource
  -> UniversalInTrCurrentAdmissionProvider

both current artifacts
  -> KVSKAPAdmittedNodePlatformTransport
  -> concrete InterchangeableStegOSNodeCarrier
  -> existing NodeEventExecutionBroker capability tvc_recipient_admission_authority_sign
  -> generic OpaqueP256AuthorityCapability
  -> native TVCRecipientAdmissionBoundOperationSigner on any eligible StegOS node
  -> signature response
  -> existing /run/stegverse/vault-agent.sock
```

The generic Python opaque-capability interface and native Swift signer are both source-complete, but their concrete device-local interop binding is not yet observed or claimed. No component may select a durable trusted device or create a second verifier.

## Remaining blockers

```text
CURRENT_KV_SKAP_VERIFICATION_RECORD_SELECTION_AND_RUNTIME_PROVIDER_BINDING_NOT_YET_IMPLEMENTED
CURRENT_INTR_ADMISSION_RUNTIME_ROUTE_INSTALLATION_AND_EXACT_RECEIPT_EVIDENCE_SOURCE_NOT_YET_OBSERVED
INTERCHANGEABLE_STEGOS_NODE_CARRIER_NOT_YET_BOUND_TO_EXISTING_NODE_EVENT_EXECUTION_BROKER_RUNTIME
GENERIC_NODE_OPAQUE_P256_CAPABILITY_NOT_YET_BOUND_TO_NATIVE_STEGOS_AUTHORITY_SIGNER
PLATFORM_SIGNER_BACKEND_NOT_YET_INJECTED_INTO_PRODUCTION_VAULT_AGENT_LIFECYCLE
PRODUCTION_AUTHORITY_KEY_MATERIALIZATION_NOT_YET_OBSERVED
MATCHING_PUBLIC_JWK_BINDING_NOT_YET_OBSERVED
FRESH_WORKERCOORDINATOR_BOUND_PRODUCTION_SIGNATURE_NOT_YET_OBSERVED
```

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

1. Bind current applicable KV/SKAP record selection to the concrete read-only runtime provenance provider; reject arbitrary historical SKAP receipts.
2. Bind the current-InTr evidence source to authentic existing Universal InTr resident receipt/request/payload state for the exact sign request; do not synthesize admission.
3. Implement the concrete `InterchangeableStegOSNodeCarrier` on the existing Canonical Runtime / NodeEventExecutionBroker path with no device pinning.
4. Bind the generic `OpaqueP256AuthorityCapability` to the native `TVCRecipientAdmissionBoundOperationSigner` on whichever eligible StegOS node carries the capability.
5. Inject `PlatformOpaqueRecipientAdmissionSigner` into the existing vault-agent launcher only when those concrete runtime bindings fail closed.
6. Materialize one production authority key on an eligible node, project only public JWK/key ID, bind the trust anchor, and observe one fresh WorkerCoordinator-bound signed admission.

## README review

StegOS README was reviewed. One task-specific paragraph still describes the authority candidate as entirely non-signing-reachable. That wording is now stale because PR #360 source-implements an internal KV/SKAP+InTr-bound signing path, while the public deep link remains non-signing. The connector available in this session cannot safely apply a partial patch to the large README without whole-file replacement, so this documentation mismatch is explicitly retained as reconciliation debt rather than falsely claimed updated. The applicable task handoffs and canonical record carry the correct current architecture.

## Manual work

None. Production private-key, credential, assertion, biometric, authenticator, or user-verification material must not be placed in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or model output.
