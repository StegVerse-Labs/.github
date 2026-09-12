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

## Corrected architecture invariant

User verification is maintained exclusively through KV/SKAP Vault. A StegOS device is an interchangeable transport node; an iPhone, another eligible device, node identity, transport-channel identity, Secure Enclave key, local key possession, GitHub, HeartBeat, or model output does not become a user verifier merely because it carries or executes an operation.

The global Task Registry contract is `data/task-registry-global-invariants.json`. This task must remain consistent with that contract.

A node may consume already-established KV/SKAP-backed verification state together with current Interlock/InTr admission and may enforce exact local operation constraints such as capability identity, key role, message/hash binding, nonce, freshness, replay protection, and non-exportability. Those node-local checks protect operation integrity; they do not create or replace user verification.

## Current truth

- `stegfin-governance` PR #100 merged the opaque recipient-admission signing protocol.
- PR #101 merged dispatch into the existing `/run/stegverse/vault-agent.sock` boundary.
- StegOS PR #356 merged the role-separated non-exportable P-256 Secure Enclave authority-key candidate at `e81b981c1218fca2031a43207afd0a419ff1263d`.
- TVC PR #418 consolidated the caller onto the existing vault-agent path at `5edf023aa7d45e1f525dd1bb556d25cacd35ae74` and preserved WorkerCoordinator validation before signer invocation.
- `stegfin-governance` PR #102 merged `PlatformOpaqueRecipientAdmissionSigner` at `6a42422d1faf2449f18f98efcd6b0c61bd0bb733`.
- `stegfin-governance` PR #103 merged the signed InTr transport-integrity adapter at `80797f67d71c2f815f082a1f71f8df37778ae110`. That Ed25519 envelope remains optional transport-integrity evidence only; it is not a user verifier and is not required as a durable trust root.
- `.github` PR #1627 established the global Task Registry invariant that KV/SKAP Vault is the sole user verifier and StegOS devices are interchangeable transport nodes.
- StegOS PR #358 implemented the platform-neutral `stegos/kv_skap_verified_local_operation.py` binding and squash-merged at `d39477a0a175c175266fe31fe0a2862323895ec9` after exact-head StegOS CI `34721268779` passed.
- The merged binding consumes only opaque KV/SKAP verification provenance (`verificationRef` + digest + VERIFIED state), requires a current Interlock/InTr admission reference/digest, binds the exact authority key ID, authority public-JWK digest, message digest, nonce, issue/expiry window, and requires injected one-time replay consumption.
- The binding rejects required-node identity, pinned-device identity, private-key-material requests, recipient-key reuse, public invocation, and any declaration that the device is the user verifier.
- Its output explicitly records `nodeRole=INTERCHANGEABLE_TRANSPORT_NODE`, `deviceUserVerifierAuthority=NONE`, `nodeUserVerifierAuthority=NONE`, and `transportUserVerifierAuthority=NONE`.
- Existing Device/KV/SKAP custody/readback receipts remain useful evidence but are not silently promoted into user verification; KV/SKAP user-verification provenance remains a distinct opaque upstream input.
- `stegwallet/container_vault_agent.py` still does not inject the platform signer in production.
- Authentic authority-key materialization, matching public-JWK binding, and fresh signed-admission runtime evidence remain unobserved.

## Source-complete portions

```text
opaque vault-agent signing protocol
single existing vault-agent caller path
WorkerCoordinator invocation validation before TVC signer call
role-separated non-exportable P-256 authority-key candidate
recipient-key non-reuse
fail-closed PlatformOpaqueRecipientAdmissionSigner
optional signed InTr transport-integrity envelope
KV/SKAP sole-user-verifier Task Registry invariant
platform-neutral KV/SKAP + InTr local-operation binding
exact authority-key/public-JWK/message/nonce/freshness binding
one-time replay-protector requirement
explicit node/device pinning rejection
no user verification performed by node
no duplicate signer socket/daemon
```

These source merges do not prove production user-verification state, vault-agent-to-node integration, local P-256 capability invocation, production authority-key materialization, public trust-anchor binding, or production signing.

## Exact remaining problem

Connect the already-merged vault-agent `PlatformOpaqueRecipientAdmissionSigner` request to the StegOS `KV/SKAP + InTr -> exact local operation` binding, then connect the resulting verified local-operation binding to whichever eligible StegOS node currently exposes the opaque role-separated P-256 authority capability.

No additional user verifier is needed. The node must not inspect or recreate user verification; it only consumes the KV/SKAP verification provenance and current InTr admission and enforces exact operation integrity before local capability invocation.

The integration must preserve:

```text
KV/SKAP verification provenance
current Interlock/InTr admission
exact authority key role / key ID
matching public-JWK digest
exact message digest
nonce / bounded freshness / one-time replay state
non-exportability
recipient-key non-reuse
no alternate credential path
no device/node pinning as user-verifier trust
```

Device replacement must not change the user's verifier. If Node A is replaced by eligible Node B, the verifier remains KV/SKAP Vault; only the eligible local capability endpoint and resulting runtime evidence may change.

## Invariants

```text
KV/SKAP Vault is the sole user verifier
StegOS devices are interchangeable transport nodes
node/device identity is not user-verifier authority
transport-channel identity is not user-verifier authority
local key possession is not user verification
Secure Enclave presence is not user verification
TV/TVC remains credential/signing authority
Interlock/InTr remains transition authority
existing /run/stegverse/vault-agent.sock remains the credential boundary
no second signer daemon or alternate credential path
GitHub/CI/model/Heartbeat have no user-verifier or signing authority
recipient Secure Enclave key is not the admission authority key
production authority private key is non-exportable
public trust anchor contains public material only
```

## Next

1. Adapt the exact `PlatformOpaqueRecipientAdmissionSigner` request into the merged `kv_skap_verified_local_operation` input shape while supplying externally established KV/SKAP verification provenance and current InTr admission; do not invent verifier state.
2. Connect the resulting local-operation binding to an eligible node-local opaque P-256 authority capability without adding a device-specific verifier or required node identity.
3. Preserve the one-time replay contract in the resident/runtime integration.
4. Inject the platform signer into the existing vault-agent lifecycle only when the KV/SKAP-backed admitted operation can reach an eligible node fail-closed.
5. Materialize the distinct production authority key on an eligible node, project only public JWK/key ID, and bind the trust anchor.
6. Observe one fresh WorkerCoordinator-bound signed admission and verify the resulting authority signature.

## README review

The organization README and StegOS README were reviewed during this source slice. The new StegOS module applies the already-canonical authority topology rather than changing it; the task-specific implementation details are carried by `StegVerse-Labs/StegOS/docs/KV_SKAP_VERIFIED_LOCAL_OPERATION_BINDING_MIRROR_HANDOFF.md` and this canonical handoff.

## Manual work

None. Do not create, paste, export, upload, reconstruct, or screenshot production private-key material in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or repository state.
