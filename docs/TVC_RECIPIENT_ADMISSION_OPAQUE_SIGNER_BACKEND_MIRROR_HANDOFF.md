# TVC Recipient Admission Opaque Signer Backend Mirror Handoff

Updated: 2026-09-12

```text
goal_id: TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001
parent_goal: TVC-RECIPIENT-ADMISSION-SIGNING-CUSTODY-001
root_goal: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
cosv_id: 50000000102000
state: ACTIVE
checkout_state: CHECKED_OUT
credential_authority: TV/TVC
transition_authority: Interlock/InTr
github_runtime_authority: NONE
```

## Current truth

- `stegfin-governance` PR #100 merged the private-key-free opaque recipient-admission signing protocol at `c16d80b9b310add94565dfc40104fc49a889e9c3` after exact-head Governance, StegWallet governance, and iOS first-passkey validation passed.
- `stegfin-governance` PR #101 merged existing-vault-agent dispatch integration at `ed6a97dd9ae988323373b9310ab411f0da82e6d3` after exact-head Governance, StegWallet governance, iOS first-passkey, and external-collaboration broker validations passed.
- `.github` PR #1589 passed fresh exact-head Heartbeat `34709100860`, deterministic repository suite `34709100853`, and organization-control `34709100935`, then squash-merged at `90bec60daaa295757bbb5166afe68d9d31634786`; this child is canonical Task Registry truth.
- The signer operation remains an operation of the existing `VaultAgentService`; no second signer daemon/socket owner is required or authorized.
- The current `stegwallet/container_vault_agent.py` production launcher still constructs `VaultAgentService(args.socket, store)` without a recipient-admission signer. Therefore the merged opaque signer interface is fail-closed but not yet production-reachable.
- StegOS PR #356 created the first role-separated Secure Enclave authority-key candidate source. After an unrelated stale Device Continuity test was reconciled separately in StegOS PR #357 (`312a7c494d7f7e3e42d0c85f13c281a3daad9603`), PR #356 exact head `7a6c35b204233dc6a5460288f5a2ce5a7aee62a1` passed StegOS CI `34713849035`, iOS Apple Toolchain Validation `34713849131`, iOS Device Package Validation `34713849084`, and GADI native boundary defense validation `34713849085`, then squash-merged at `e81b981c1218fca2031a43207afd0a419ff1263d`.
- The merged StegOS authority candidate reuses only established Apple Secure Enclave P-256 mechanics. It uses application tag `org.stegverse.stegos.tvc.recipient-admission-authority.p256`, derives a public `tvc://authority-key/p256/...` identity, exposes only public JWK/digest/key ID plus an opaque Secure Enclave handle, and explicitly records `privateKeyExported=false`, `recipientKeyReused=false`, `signingReachable=false`, and `authorityEffect=NONE_AUTHORITY_KEY_CANDIDATE_ONLY`.
- The existing recipient key remains separate at tag `org.stegverse.stegos.tvc.skap.browser-recipient.coinbase.p256` and cannot satisfy the authority role.
- No authority-signing public URL action was added. The existing `stegverse://tvc-recipient-capability` envelope is shape/callback bounded but is not sufficient cryptographic authentication for arbitrary authority signing, so exposing `sign(message)` through it would create a signing oracle.
- StegOS also already contains `TVCAuthenticatedRecipientCapabilityAdapter`, which verifies a signed TVC admission against an exact P-256 authority public JWK, `tvc://authority-key/p256/...` identity, bounded lifetime, WorkerCoordinator fence, and authority-separation fields. This is useful downstream verification evidence, but it cannot authenticate a request to the same authority signer without circularly assuming an authority signature that the signer itself is being asked to produce.
- No authenticated resident device is connected through the available remote-device surface, so actual production authority-key materialization, same-device backend binding, and fresh production signing remain unobserved.
- Authentic production authority-key custody, matching public JWK binding, and fresh production signed admission therefore remain unobserved.

## Exact remaining problem

Bind the now-source-canonical purpose-specific Secure Enclave authority primitive to the existing `OpaqueRecipientAdmissionSigner` operation through one authenticated, non-public same-lifecycle bridge that does not require a prior signature from the same authority key and does not create a second signer daemon, credential socket, or alternate authority.

The final backend surface remains exactly:

```text
authority_key_id() -> public authority identifier
sign(message bytes) -> DER ECDSA P-256/SHA-256 signature
```

It must not expose private-key bytes, PEM, private JWK `d`, seed, scalar, exportable PKCS#8, or a secret-store string representation.

## Source-complete role separation

The role-separation portion is now source-implemented and Apple-toolchain validated:

```text
recipient key tag != authority key tag
recipient key ID namespace != tvc://authority-key/p256/<id>
recipient admission/liveness semantics != authority signing semantics
recipient candidate may never satisfy OpaqueRecipientAdmissionSigner
only public authority JWK/key ID may cross the custody boundary
private authority key remains non-exportable inside Secure Enclave
public deep-link signing is absent
```

The candidate is still deliberately non-authorizing and non-signing-reachable. Source merge is not production key materialization.

## Authentication constraint for the bridge

The existing authenticated-recipient verifier cannot simply be reused backwards. It verifies a TVC signature produced by the authority key. Requiring that same signature to authenticate a request asking the authority key to sign would be circular and would not establish a bootstrap trust path.

The bridge therefore must consume an independently authentic existing admission/claim/fence or same-lifecycle local authority signal already owned by TV/TVC / Interlock/InTr. It must fail closed if that independent authentication cannot be demonstrated. A callback allowlist, unsigned deep-link envelope, GitHub workflow identity, model output, heartbeat state, or recipient-key proof of possession is not sufficient signing authorization.

## Invariants

```text
TV/TVC remains credential/signing authority
Interlock/InTr remains transition authority
existing /run/stegverse/vault-agent.sock remains the credential boundary
no second signer daemon or alternate credential path
GitHub/CI/model/Heartbeat have no signing authority
recipient Secure Enclave key is not the admission authority key
production private key is non-exportable
public trust anchor contains public JWK only
no public unauthenticated authority-signing route
no circular same-key authentication of a signing request
```

## Next

1. Inventory the existing TV/TVC / Interlock/InTr resident operation surfaces for an independently authenticated, non-public request that can authorize the exact `recipient_admission_sign` operation without requiring a signature from the same authority key.
2. Implement only the smallest adapter needed to translate that already-authenticated request into the existing `OpaqueRecipientAdmissionSigner` call; do not create a second signer daemon/socket owner.
3. Bind the adapter to the distinct Secure Enclave authority key identity and fail closed on key-ID mismatch, missing platform primitive, missing independent authorization, or any recipient-key substitution.
4. Materialize one production authority key under TV/TVC control on an authenticated eligible resident and project only its public P-256 JWK/key ID.
5. Bind the matching public JWK as the recipient-admission trust anchor without private material.
6. Observe authentic runtime custody and issue one fresh WorkerCoordinator-fence/lease-bound admission through the merged TVC adapter.
7. Return to `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001` only after the signed admission is authentically observed.

## Manual work

None. Do not create, paste, export, upload, reconstruct, or screenshot the production authority private key in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or repository state.
