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

TVC credential/capability admission and Interlock/InTr transition admission remain distinct. A TVC-signed capability admission cannot substitute for an authentic InTr admission receipt.

## Current source truth

The source chain is now complete through the canonical node-event broker and separately through the native bound Secure Enclave signer:

```text
PlatformOpaqueRecipientAdmissionSigner
  -> KVSKAPAdmittedNodePlatformTransport
  -> current KV/SKAP provenance + current InTr admission
  -> CanonicalRuntimeRecipientAdmissionNodeCarrier
  -> existing NodeEventExecutionBroker
  -> TVCRecipientAdmissionNodeCapability
  -> generic OpaqueP256AuthorityCapability

native eligible-node capability:
  TVCRecipientAdmissionBoundOperationSigner
  -> distinct role-separated Secure Enclave P-256 key
```

Merged evidence:

- `PlatformOpaqueRecipientAdmissionSigner` remains merged at `StegVerse-Labs/stegfin-governance@6a42422d1faf2449f18f98efcd6b0c61bd0bb733` and the existing `/run/stegverse/vault-agent.sock` remains the only resident credential/signing process boundary.
- StegOS role-separated non-exportable P-256 authority-key candidate remains merged at `e81b981c1218fca2031a43207afd0a419ff1263d`.
- StegOS PR #358 merged the KV/SKAP + InTr local-operation binder at `d39477a0a175c175266fe31fe0a2862323895ec9`; StegOS CI `34721268779` passed.
- The canonical `KVSKAPAdmittedNodePlatformTransport` source remains recorded at `StegVerse-Labs/stegfin-governance@1e592bd6c385e79411ac72229ae9fd12a70411c9`. It performs no user verification and does not select a node.
- TVC already-verified KV/SKAP provenance projection remains merged at `4c78f8653b8a5899350479d57c58e936b50e023a`.
- The recipient-admission signing Universal InTr source route remains merged in `.github` at `08178861cfa144ce032d9399d50c56a77bd1a74b`. Source installability does not prove authentic resident route installation or a current receipt.
- `UniversalInTrCurrentAdmissionProvider` remains merged at `0980ca24f3acc4ed9a26cd24e433276d37c72911`; it requires an exact fresh `INGRESS_ADMITTED` receipt and is projection-only.
- StegOS PR #359 merged `TVCRecipientAdmissionNodeCapability` at `8b3b83532b26333570369884a270481f48aeaeef`. It reuses the existing `NodeEventExecutionBroker`, validates the canonical local-operation binding, and invokes an injected opaque P-256 capability without performing user verification or selecting a permanent device.
- StegOS PR #360 merged the native bound authority signer at `ad05e62f0d84549e511b6ebd047bb8091a3b0ce7`. Exact head passed StegOS CI `34722630460`, Apple Toolchain `34722630468`, and Device Package `34722630448`. It signs only after exact KV/SKAP+InTr operation/key/JWK/message/nonce/time binding and exposes no public signing URL.
- StegOS PR #362 merged `CanonicalRuntimeRecipientAdmissionNodeCarrier` at `b6b6a370bffb2cee20ae1037b0a8292c41c08858` after exact-head StegOS CI `34722999313` passed.
- The carrier consumes externally observed current materialization, retained Node, open canonical EVENT_EPHEMERAL lease admission, and the full exact WorkerCoordinator invocation. It derives the claim/fence only for `TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001`, registers the already-merged `tvc_recipient_admission_authority_sign` capability on the existing broker, and returns only the broker-observed platform result.
- The carrier does not discover/select a node, mint a claim/fence, open/own a runtime lease, issue InTr admission, create persistent transport, require an always-on receiver, or perform user verification.
- Investigation of the current Universal InTr sign-ingress receipt confirms it is deterministic/write-once/hash-bound evidence with `authority_effect=INGRESS_TRANSITION_ONLY`, not a cryptographic credential. Therefore neither the existing public recipient deep link nor the loopback continuity HTTP carrier may be promoted into a public authority-signing endpoint merely by accepting a receipt object.

## Source-complete portions

```text
opaque vault-agent signing protocol
single existing vault-agent caller path
role-separated non-exportable P-256 authority-key candidate
KV/SKAP sole-user-verifier invariant
already-verified KV/SKAP provenance projection
platform-neutral KV/SKAP + InTr local-operation binding
vault-agent platform request -> admitted interchangeable-node bundle
Universal InTr signing-operation ingress source + current-admission projector
existing NodeEventExecutionBroker recipient-admission capability
concrete canonical-runtime interchangeable-node carrier
exact WorkerCoordinator task/claim/fence binding
exact retained-node/materialization/open-lease binding
replay/key/JWK/message/nonce/freshness checks
native role-separated Secure Enclave bound signing primitive
no user verification performed by node/transport/projectors/native signer
no permanent device pin
no public authority-signing deep link or loopback signing service
no duplicate listener or signer daemon
```

These source merges do not prove current production user-verification state, live Universal InTr receipt availability, generic-to-native device-local interop, production vault-agent launcher injection, production authority-key materialization, public trust-anchor binding, or a production signature.

## Exact remaining problem

```text
current applicable KV/SKAP owner-verification record
  -> concrete read-only runtime KVSKAPVerificationProvenanceProvider

exact platform sign request
  -> authentic installed shared Universal InTr route
  -> current write-once INGRESS_ADMITTED receipt
  -> concrete CurrentInTrAdmissionEvidenceSource
  -> UniversalInTrCurrentAdmissionProvider

both current artifacts
  -> KVSKAPAdmittedNodePlatformTransport
  -> CanonicalRuntimeRecipientAdmissionNodeCarrier
  -> existing NodeEventExecutionBroker
  -> TVCRecipientAdmissionNodeCapability
  -> generic OpaqueP256AuthorityCapability
  -> [remaining eligible execution-context interop]
  -> native TVCRecipientAdmissionBoundOperationSigner
  -> signature response
  -> existing /run/stegverse/vault-agent.sock
```

The remaining native interop must not become a public signing oracle. The current InTr receipt is not itself a cryptographic bearer credential, so a public loopback/deep-link endpoint that trusts a supplied receipt object is not admissible. The binding must occur inside an eligible StegOS execution context or another already-authorized native process relationship without creating a second verifier or alternate credential path.

## Remaining blockers

```text
CURRENT_KV_SKAP_VERIFICATION_RECORD_SELECTION_AND_RUNTIME_PROVIDER_BINDING_NOT_YET_IMPLEMENTED
CURRENT_INTR_ADMISSION_RUNTIME_ROUTE_INSTALLATION_AND_EXACT_RECEIPT_EVIDENCE_SOURCE_NOT_YET_OBSERVED
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
existing /run/stegverse/vault-agent.sock remains the resident credential process boundary
existing Universal InTr listener remains the transition ingress process
no second signer daemon, public signing service, listener, or alternate credential path
production authority private key is non-exportable
public trust anchor contains public material only
```

## Next

1. Bind current applicable KV/SKAP record selection to the concrete read-only runtime provenance provider; reject arbitrary historical SKAP receipts.
2. Bind the current-InTr evidence source to authentic existing resident request/payload/receipt locations; do not synthesize admission.
3. Bind the generic `OpaqueP256AuthorityCapability` to `TVCRecipientAdmissionBoundOperationSigner` only inside an eligible StegOS native execution context; do not expose signing on the public recipient URL or loopback continuity HTTP carrier.
4. Inject `PlatformOpaqueRecipientAdmissionSigner` into the existing vault-agent launcher only when the concrete providers and native capability binding fail closed.
5. Materialize one production authority key on an eligible node, project only public JWK/key ID, bind the trust anchor, and observe one fresh WorkerCoordinator-bound signed admission.

## README review

StegOS README was reviewed. One task-specific paragraph still describes the authority candidate as entirely non-signing-reachable. That wording is stale because PR #360 source-implements an internal KV/SKAP+InTr-bound signing path, while public signing remains unavailable. The available connector cannot safely apply a partial edit to the large README without whole-file replacement, so this mismatch remains explicit documentation debt rather than being falsely claimed updated.

## Manual work

None. Production private-key, credential, assertion, biometric, authenticator, or user-verification material must not be placed in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or model output.
