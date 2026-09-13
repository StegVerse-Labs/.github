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

## Reusable Task Component Model reconciliation

The Reusable Task Component Model merged canonically in `StegVerse-Labs/.github#1652` at `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`. This Goal Task remains the same Goal Task and retains COSV `50000000102000`; componentization does not create a successor, mint authority, or change authentic runtime predicates.

Deterministic decomposition score: `27`, disposition `STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION`.

Component-model source truth is projected separately in:

```text
docs/TVC_RECIPIENT_ADMISSION_OPAQUE_SIGNER_COMPONENT_MODEL_MIRROR_HANDOFF.md
data/goal-task-transport-profiles/TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001.json
```

This runtime handoff remains the authoritative runtime/evidence continuation record.

Selected reusable transport components:

```text
RTC-MANIFEST-001
RTC-GOVERNED-PROCESSING-002
RTC-ROUNDTRIP-003 x1: recipient_admission_signature_round_trip
RTC-EVIDENCE-CUSTODY-004
RTC-INTERLOCK-INTR-TRANSPORT-008 x1: recipient_admission_sign_request_ingress
```

Not selected because they are not signer completion requirements:

```text
RTC-PUBLISHER-005
RTC-SDK-RETURN-006
RTC-STEGVERSE-EGRESS-007
RTC-FARSIDE-FINAL-009
```

Execution materialization reuses `data/reusable-task-ephemeral-construct-contract.json`, the existing canonical `EVENT_EPHEMERAL` runtime, and `NodeEventExecutionBroker`. Current KV/SKAP provenance and current InTr admission reuse their already-merged projector/provider owners. TV/TVC remains the signing owner. No further bespoke scheduler, listener, runtime plane, verifier, or generic transport adapter may be added to this Goal Task when an existing reusable owner applies.

## Current source truth

The source chain is complete through the canonical node-event broker and separately through the native bound Secure Enclave signer:

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
- The canonical `KVSKAPAdmittedNodePlatformTransport` source remains recorded at `StegVerse-Labs/stegfin-governance@1e592bd6c385e79411ac72229ae9fd12a70411c9`. Under the component model this is retained as task-specific composition/configuration over existing reusable transport/evidence owners; it must not grow into a second generic transport plane.
- TVC already-verified KV/SKAP provenance projection remains merged at `4c78f8653b8a5899350479d57c58e936b50e023a` and is reused rather than reimplemented.
- The recipient-admission signing Universal InTr source route remains merged in `.github` at `08178861cfa144ce032d9399d50c56a77bd1a74b`. It is the existing reusable InTr transport/governed-ingress owner for this sign-request class. Source installability does not prove authentic resident route installation or a current receipt.
- `UniversalInTrCurrentAdmissionProvider` remains merged at `0980ca24f3acc4ed9a26cd24e433276d37c72911`; it requires an exact fresh `INGRESS_ADMITTED` receipt and is projection-only.
- StegOS PR #359 merged `TVCRecipientAdmissionNodeCapability` at `8b3b83532b26333570369884a270481f48aeaeef`. It reuses the existing `NodeEventExecutionBroker`, validates the canonical local-operation binding, and invokes an injected opaque P-256 capability without performing user verification or selecting a permanent device.
- StegOS PR #360 merged the native bound authority signer at `ad05e62f0d84549e511b6ebd047bb8091a3b0ce7`. Exact head passed StegOS CI `34722630460`, Apple Toolchain `34722630468`, and Device Package `34722630448`. It signs only after exact KV/SKAP+InTr operation/key/JWK/message/nonce/time binding and exposes no public signing URL.
- StegOS PR #362 merged `CanonicalRuntimeRecipientAdmissionNodeCarrier` at `b6b6a370bffb2cee20ae1037b0a8292c41c08858` after exact-head StegOS CI `34722999313` passed. Under the component model this is a task-specific binding to the existing reusable ephemeral execution/runtime component and must not become a new runtime lifecycle owner.
- The carrier consumes externally observed current materialization, retained Node, open canonical EVENT_EPHEMERAL lease admission, and the full exact WorkerCoordinator invocation. It derives the claim/fence only for this Goal Task, registers the already-merged `tvc_recipient_admission_authority_sign` capability on the existing broker, and returns only the broker-observed platform result.
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
reusable transport/component composition projection
no user verification performed by node/transport/projectors/native signer
no permanent device pin
no public authority-signing deep link or loopback signing service
no duplicate listener, runtime, generic transport plane, or signer daemon
```

These source merges and reusable-component bindings do not prove current production user-verification state, live Universal InTr receipt availability, generic-to-native device-local interop, production vault-agent launcher injection, production authority-key materialization, public trust-anchor binding, Master Records reconstruction, or a production signature.

## Exact remaining problem

```text
current applicable KV/SKAP owner-verification record
  -> existing provenance projector
  -> missing canonical current-record selector/provider binding

exact platform sign request
  -> existing reusable RTC-INTERLOCK-INTR-TRANSPORT-008 / Universal InTr route
  -> authentic installed shared Universal InTr route
  -> current write-once INGRESS_ADMITTED receipt
  -> concrete CurrentInTrAdmissionEvidenceSource
  -> UniversalInTrCurrentAdmissionProvider

both current artifacts
  -> selected reusable governed-processing/round-trip composition
  -> existing canonical ephemeral runtime + NodeEventExecutionBroker
  -> TVCRecipientAdmissionNodeCapability
  -> generic OpaqueP256AuthorityCapability
  -> [remaining eligible execution-context interop]
  -> native TVCRecipientAdmissionBoundOperationSigner
  -> signature response
  -> existing /run/stegverse/vault-agent.sock
  -> RTC-EVIDENCE-CUSTODY-004 / Master Records custody and reconstruction
```

The remaining native interop must not become a public signing oracle. The current InTr receipt is not itself a cryptographic bearer credential, so a public loopback/deep-link endpoint that trusts a supplied receipt object is not admissible. The binding must occur inside an eligible StegOS execution context or another already-authorized native process relationship without creating a second verifier or alternate credential path.

The current-record selector is a real unresolved dependency. Do not choose an arbitrary historical or merely latest SKAP receipt and call it current user verification. The selector must be canonical, context-bound, and feed the already-existing provenance projector/provider rather than creating a new verification mechanism.

## Remaining blockers

```text
CURRENT_KV_SKAP_VERIFICATION_RECORD_SELECTION_AND_RUNTIME_PROVIDER_BINDING_NOT_YET_IMPLEMENTED
CURRENT_INTR_ADMISSION_RUNTIME_ROUTE_INSTALLATION_AND_EXACT_RECEIPT_EVIDENCE_SOURCE_NOT_YET_OBSERVED
GENERIC_NODE_OPAQUE_P256_CAPABILITY_NOT_YET_BOUND_TO_NATIVE_STEGOS_AUTHORITY_SIGNER
PLATFORM_SIGNER_BACKEND_NOT_YET_INJECTED_INTO_PRODUCTION_VAULT_AGENT_LIFECYCLE
PRODUCTION_AUTHORITY_KEY_MATERIALIZATION_NOT_YET_OBSERVED
MATCHING_PUBLIC_JWK_BINDING_NOT_YET_OBSERVED
FRESH_WORKERCOORDINATOR_BOUND_PRODUCTION_SIGNATURE_NOT_YET_OBSERVED
MASTER_RECORDS_CUSTODY_RECONSTRUCTION_NOT_YET_OBSERVED
```

## Invariants

```text
Task Registry is coordination only
WorkerCoordinator owns claim/fence authority
KV/SKAP Vault is the sole user verifier
StegOS devices are interchangeable transport/execution nodes
TVC capability admission != Interlock/InTr transition admission
node/device/transport identity is not user-verifier authority
SKAP custody/readback alone is not user verification
local key possession / Secure Enclave presence is not user verification
TV/TVC remains credential/signing authority
Interlock/InTr remains transition authority
Master Records remains observed-reality custody/reconstruction authority
HeartBeat remains timing/freshness/liveness/correlation observability only
GitHub has no runtime authority
existing /run/stegverse/vault-agent.sock remains the resident credential process boundary
existing Universal InTr listener remains the transition ingress process
no second signer daemon, public signing service, listener, runtime plane, or alternate credential path
production authority private key is non-exportable
public trust anchor contains public material only
```

## Next

1. Reuse the existing KV/SKAP provenance component and bind only the missing canonical current-record selector/provider; reject arbitrary historical or latest-only selection semantics.
2. Reuse the existing Universal InTr component and bind the current-InTr evidence source to authentic existing resident request/payload/receipt locations; do not synthesize admission or add another listener.
3. Reuse the existing canonical ephemeral runtime/broker component and bind the generic `OpaqueP256AuthorityCapability` to `TVCRecipientAdmissionBoundOperationSigner` only inside an eligible StegOS native execution context; do not expose signing on the public recipient URL or loopback continuity HTTP carrier.
4. Inject `PlatformOpaqueRecipientAdmissionSigner` into the existing vault-agent launcher only when the componentized providers and native capability binding fail closed.
5. Materialize one production authority key on an eligible node, project only public JWK/key ID, bind the trust anchor, observe one fresh WorkerCoordinator-bound signed admission, and submit the authentic evidence to Master Records custody/reconstruction.

## README review

StegOS README was reviewed. One task-specific paragraph still describes the authority candidate as entirely non-signing-reachable. That wording is stale because PR #360 source-implements an internal KV/SKAP+InTr-bound signing path, while public signing remains unavailable. This remains explicit documentation debt and is covered by the reusable README-validation requirement; do not treat stale prose as runtime truth.

The `.github` root README already carries the canonical Reusable Task Component Model projection from PR #1652. This reconciliation does not materially change the `.github` repository-wide component-model function, so no additional root README architecture mutation is required by this task-specific projection.

## Manual work

None. No second user-operated device is required. No device-local user verification is authorized. Production private-key, credential, assertion, biometric, authenticator, or user-verification material must not be placed in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or model output.
