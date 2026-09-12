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
- StegOS PR #358 merged `kv_skap_verified_local_operation.py` at `d39477a0a175c175266fe31fe0a2862323895ec9` after StegOS CI `34721268779` passed. It consumes opaque KV/SKAP verification provenance, current InTr admission, exact authority key/public-JWK/message/nonce/freshness data, and an injected one-time replay protector while rejecting node/device pinning and any device-verifier role.
- `stegfin-governance` PR #104 merged `KVSKAPAdmittedNodePlatformTransport` at `1e592bd6c385e79411ac72229ae9fd12a70411c9` after iOS first-passkey `34721416782`, Governance `34721416818`, and StegWallet governance `34721416838` passed.
- The merged transport adapts the exact vault-agent platform-sign request by consuming an injected KV/SKAP verification-provenance provider, injected current-InTr-admission provider, and injected interchangeable-StegoS-node carrier. It adds bounded issue/expiry metadata but performs no user verification, node selection, key custody, or network ownership.
- It rejects required-node/pinned-device identity, private-key-material requests, recipient-key reuse, public invocation, and node responses that claim device/node/transport verifier authority.
- The prior Ed25519 signed-carrier implementation remains optional transport-integrity evidence only; it is not the user verifier or a required device trust root.
- `container_vault_agent.py` still does not inject the completed platform backend in production.
- Authentic KV/SKAP verification provenance binding, current InTr admission provider binding, canonical-runtime node carrier binding, local P-256 authority invocation, production authority-key materialization, public-JWK trust-anchor binding, and fresh signed-admission runtime evidence remain unobserved.

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
explicit node/device pinning rejection
no user verification performed by node or transport adapter
no duplicate signer socket/daemon
```

These source merges do not prove production KV/SKAP verification state, concrete provider bindings, canonical-runtime node carriage, local P-256 invocation, production authority-key materialization, public trust-anchor binding, or production signing.

## Exact remaining problem

The generic interfaces are now in place. The remaining source/runtime integration is to bind them to existing owners without inventing new authority:

```text
KVSKAPVerificationProvenanceProvider
  -> existing KV/SKAP-owned verification state only

CurrentInTrAdmissionProvider
  -> existing current admitted transition/operation only

InterchangeableStegOSNodeCarrier
  -> existing Canonical Runtime / resident StegOS carriage

receiving StegOS node
  -> kv_skap_verified_local_operation binder
  -> one-time replay protector
  -> eligible local opaque role-separated P-256 authority capability
```

No component in that chain may select a durable trusted device or create a second verifier. If Node A is replaced by eligible Node B, KV/SKAP remains the user's verifier and the operation contract remains unchanged.

## Invariants

```text
KV/SKAP Vault is the sole user verifier
StegOS devices are interchangeable transport nodes
node/device/transport identity is not user-verifier authority
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

1. Locate and bind the existing KV/SKAP-owned verification-provenance producer to `KVSKAPVerificationProvenanceProvider`; do not synthesize verifier state from SKAP custody/readback alone.
2. Bind `CurrentInTrAdmissionProvider` to the exact existing current admission artifact for this operation.
3. Reuse the existing StegOS Canonical Runtime / node-event execution path for `InterchangeableStegOSNodeCarrier`, with no durable device pin.
4. Feed the bundle through `kv_skap_verified_local_operation` and its one-time replay protector on the receiving node.
5. Connect the successful binding to the local opaque role-separated P-256 authority capability.
6. Inject the resulting backend into the existing vault-agent launcher only when all three concrete providers/carrier are available fail-closed.
7. Materialize one production authority key on an eligible node, project only public JWK/key ID, bind the trust anchor, and observe one fresh WorkerCoordinator-bound signed admission.

## README review

The organization, StegOS, and stegfin-governance README topology was reviewed through the applicable handoffs. These merges implement the already-canonical authority model rather than altering it; task-specific details are recorded in the repository handoffs and this canonical handoff.

## Manual work

None. Production private-key or credential material must not be placed in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or model output.
