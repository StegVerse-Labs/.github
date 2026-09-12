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
- `stegfin-governance` PR #103 merged the signed InTr transport-integrity adapter at `80797f67d71c2f815f082a1f71f8df37778ae110` after exact-head validations passed.
- PR #103's Ed25519 channel envelope is retained only as an optional transport-integrity mechanism. It is not a user verifier, is not required as a user-verification trust root, grants no signing/credential/transition authority, and must not make any particular device non-interchangeable.
- The previously stated requirement for a distinct "iPhone authenticated-platform-request verifier" and a production channel identity as a user-verification prerequisite is retired as an architectural error.
- `stegwallet/container_vault_agent.py` still does not inject the platform signer in production.
- Authentic authority-key materialization, matching public-JWK binding, and fresh signed-admission runtime evidence remain unobserved.

## Exact remaining problem

Bind already-established KV/SKAP-backed user-verification state and current Interlock/InTr admission to the exact recipient-admission operation presented to whichever eligible StegOS node currently carries the required local capability. The node must enforce local operation integrity without becoming the verifier or a durable user trust root.

The operation binding must preserve, at minimum:

```text
KV/SKAP verification provenance
current Interlock/InTr admission
exact authority key role / key ID
matching public-JWK digest
exact message digest
nonce / freshness / replay state
non-exportability
recipient-key non-reuse
no alternate credential path
```

Device replacement must not change the user's verifier. If Node A is replaced by eligible Node B, the verifier remains KV/SKAP Vault; only the local capability endpoint and resulting runtime evidence may change.

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

1. Trace the existing KV/SKAP verification artifact/state that should accompany this admitted operation rather than creating a second verifier.
2. Bind that verification provenance and current InTr admission to the node-local authority-key invocation contract.
3. Enforce exact capability/key/message/nonce/freshness/replay/non-exportability checks locally without assigning user-verifier authority to the node.
4. Preserve node interchangeability: no device-specific pinned verifier may become required for the user.
5. Inject the platform signer into the existing vault-agent lifecycle only when the KV/SKAP-backed admitted operation can reach an eligible node fail-closed.
6. Materialize the distinct production authority key on an eligible node, project only public JWK/key ID, and bind the trust anchor.
7. Observe one fresh WorkerCoordinator-bound signed admission and verify the resulting authority signature.

## README review

The organization README already states that running on an iPhone does not create human authority and that Task Registry, TV/TVC, Interlock/InTr, and Master Records retain distinct roles. This handoff plus the machine-readable global invariant contract now carries the more specific KV/SKAP-verifier / interchangeable-node rule; no broad README topology rewrite is required for this correction.

## Manual work

None. Do not create, paste, export, upload, reconstruct, or screenshot the production TVC authority private key in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or repository state.
