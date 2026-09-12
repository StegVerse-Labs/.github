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

The node may consume already-established KV/SKAP verification provenance plus current Interlock/InTr admission and enforce exact operation integrity. Those checks do not create user verification.

## Current truth

- The opaque vault-agent signing protocol and existing `/run/stegverse/vault-agent.sock` dispatch are merged.
- TVC caller consolidation remains merged at `5edf023aa7d45e1f525dd1bb556d25cacd35ae74`; WorkerCoordinator claim/fence validation occurs before signer invocation.
- The role-separated non-exportable P-256 authority-key candidate remains merged in StegOS at `e81b981c1218fca2031a43207afd0a419ff1263d`; the recipient key is separate and ineligible as authority key.
- `PlatformOpaqueRecipientAdmissionSigner` remains merged at `6a42422d1faf2449f18f98efcd6b0c61bd0bb733`.
- StegOS PR #358 merged the platform-neutral KV/SKAP + InTr local-operation binder at `d39477a0a175c175266fe31fe0a2862323895ec9` after StegOS CI `34721268779` passed.
- `stegfin-governance` PR #104 merged `KVSKAPAdmittedNodePlatformTransport` at `1e592bd6c385e79411ac72229ae9fd12a70411c9` after iOS first-passkey `34721416782`, Governance `34721416818`, and StegWallet governance `34721416838` passed.
- TVC PR #419 merged the provider-neutral `project_kv_skap_user_verification_provenance.py` projector at `4c78f8653b8a5899350479d57c58e936b50e023a` after exact-head TVC Recipient Capability Validation `34721637270` passed.
- The projector reuses the common existing SKAP `owner_authorization_digest` pattern observed across Coinbase, App Store Connect, post-return release, and external-collaboration credential ingress. It requires an already-verified owner authorization (`user_verification=REQUIRED`, `verified=true`) exact-digest-bound into an `ADMITTED` TV/TVC receipt with `authority_transfer=false`.
- The projector does **not** perform WebAuthn, create user-verification state, expose assertion material, or infer user verification from ciphertext custody/readback. It emits only a non-secret KV/SKAP verification reference/digest with `userVerificationAuthority=KV/SKAP Vault`, `projectionCreatesVerification=false`, and device/node/transport verifier roles false.
- The merged platform transport can now consume that generic provenance shape, but current applicable-record selection and concrete runtime provider binding remain unresolved; source existence is not authentic current verification state.
- `container_vault_agent.py` still does not inject the completed platform backend in production.
- Current InTr admission provider binding, canonical-runtime node carrier binding, local P-256 authority invocation, production authority-key materialization, public-JWK trust-anchor binding, and fresh signed-admission runtime evidence remain unobserved.

## Source-complete portions

```text
opaque vault-agent signing protocol
single existing vault-agent caller path
WorkerCoordinator invocation validation before TVC signer call
role-separated non-exportable P-256 authority-key candidate
recipient-key non-reuse
fail-closed PlatformOpaqueRecipientAdmissionSigner
KV/SKAP sole-user-verifier Task Registry invariant
platform-neutral KV/SKAP + InTr node-local operation binding
one-time replay-protector requirement
vault-agent platform request -> KV/SKAP/InTr/interchangeable-node transport adaptation
provider-neutral already-verified KV/SKAP provenance projection
explicit node/device pinning rejection
no user verification performed by node, transport adapter, or provenance projector
no duplicate signer socket/daemon
```

These source merges do not prove current production user-verification state, current-record selection, concrete runtime provider bindings, canonical-runtime node carriage, local P-256 invocation, production authority-key materialization, public trust-anchor binding, or production signing.

## Exact remaining problem

The generic provenance projection now exists. The next work is to bind the **applicable current KV/SKAP record** into `KVSKAPVerificationProvenanceProvider` at runtime, rather than choosing a stale or unrelated admitted SKAP record. In parallel, bind the current InTr admission and existing Canonical Runtime/node-event carriage, then feed those exact current artifacts through the merged local-operation binder before any opaque P-256 authority operation.

```text
current KV/SKAP verification record selection
  -> project_kv_skap_user_verification_provenance
  -> KVSKAPVerificationProvenanceProvider

current admitted operation/transition
  -> CurrentInTrAdmissionProvider

existing Canonical Runtime / resident node carriage
  -> InterchangeableStegOSNodeCarrier

receiving eligible StegOS node
  -> kv_skap_verified_local_operation binder
  -> one-time replay protector
  -> local opaque role-separated P-256 authority capability
```

No component may select a durable trusted device or create a second verifier. If Node A is replaced by eligible Node B, KV/SKAP remains the user's verifier and the exact operation contract remains unchanged.

## Invariants

```text
KV/SKAP Vault is the sole user verifier
StegOS devices are interchangeable transport nodes
node/device/transport identity is not user-verifier authority
SKAP custody/readback alone is not user verification
local key possession / Secure Enclave presence is not user verification
TV/TVC remains credential/signing authority
Interlock/InTr remains transition authority
WorkerCoordinator remains claim/fence authority
existing /run/stegverse/vault-agent.sock remains the credential process boundary
no second signer daemon or alternate credential path
production authority private key is non-exportable
public trust anchor contains public material only
```

## Next

1. Identify the canonical rule for selecting the current applicable KV/SKAP owner-verification + admitted-receipt pair, and bind that source to `KVSKAPVerificationProvenanceProvider`; do not accept arbitrary historical SKAP receipts.
2. Bind `CurrentInTrAdmissionProvider` to the exact current admitted operation artifact.
3. Reuse the existing StegOS Canonical Runtime / node-event execution path for `InterchangeableStegOSNodeCarrier`, with no durable device pin.
4. Feed the exact current artifacts through `kv_skap_verified_local_operation` and its one-time replay protector on the receiving node.
5. Connect the successful binding to the local opaque role-separated P-256 authority capability.
6. Inject the resulting backend into the existing vault-agent launcher only when the concrete providers/carrier are available fail-closed.
7. Materialize one production authority key on an eligible node, project only public JWK/key ID, bind the trust anchor, and observe one fresh WorkerCoordinator-bound signed admission.

## README review

The organization, StegOS, stegfin-governance, and TVC authority topology was reviewed through the applicable repository handoffs. The provenance projector reuses existing admitted SKAP owner-verification evidence without altering authority ownership; no broad README topology rewrite is required for this slice.

## Manual work

None. Production private-key, credential, assertion, biometric, or authenticator material must not be placed in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or model output.
