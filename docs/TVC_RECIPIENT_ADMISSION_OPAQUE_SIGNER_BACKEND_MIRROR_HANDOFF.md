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
- `.github` PR #1589 passed fresh exact-head Heartbeat `34709100860`, deterministic repository suite `34709100853`, and organization-control `34709100935`, then squash-merged at `90bec60daaa295757bbb5166afe68d9d31634786`; this child is now canonical Task Registry truth.
- The signer operation is an operation of the existing `VaultAgentService`; no second signer daemon/socket owner is required or authorized.
- The current `stegwallet/container_vault_agent.py` production launcher still constructs `VaultAgentService(args.socket, store)` without a recipient-admission signer. Therefore the merged opaque signer interface is fail-closed but not yet production-reachable.
- Organization-wide source searches found no existing TPM, PKCS#11, HSM, Keychain/KMS, or other separate TVC admission-authority non-exportable signer backend.
- StegOS already contains an iPhone Secure Enclave P-256 signing implementation using `SecKeyCreateRandomKey`, `kSecAttrTokenIDSecureEnclave`, and `SecKeyCreateSignature`, but it is explicitly recipient-scoped at `TVCRecipientKeyCandidate.swift`, with recipient key tag `org.stegverse.stegos.tvc.skap.browser-recipient.coinbase.p256` and `authorityEffect=NONE_PLATFORM_KEY_CANDIDATE_ONLY`.
- That existing recipient key must not be promoted or reused as the admission-authority key. Reuse is limited to the established Secure Enclave mechanics: a purpose-distinct TVC authority key must use a separate application tag, authority key ID namespace, public-JWK projection, and authorization semantics.
- No authenticated resident device is connected through the available remote-device surface, so actual production authority-key materialization, same-device backend binding, and fresh production signing are not observed.
- Authentic production authority-key custody, matching public JWK binding, and fresh production signed admission therefore remain unobserved.

## Exact remaining problem

Materialize or bind one purpose-specific TVC-controlled non-exportable P-256 authority signer that implements the existing `OpaqueRecipientAdmissionSigner` interface inside the existing vault-agent runtime lifecycle.

The backend may expose only:

```text
authority_key_id() -> public authority identifier
sign(message bytes) -> DER ECDSA P-256/SHA-256 signature
```

It must not expose private-key bytes, PEM, private JWK `d`, seed, scalar, exportable PKCS#8, or a secret-store string representation.

## Reusable implementation direction

The repository evidence supports reusing the already-established Apple Secure Enclave P-256 process rather than inventing new cryptography. The authority implementation must remain a new role-specific key, not a renamed recipient key.

Required role separation:

```text
recipient key tag != authority key tag
recipient key ID namespace != tvc://authority-key/p256/<id>
recipient admission/liveness semantics != authority signing semantics
recipient candidate may never satisfy OpaqueRecipientAdmissionSigner
only public authority JWK/key ID may cross the custody boundary
private authority key remains non-exportable inside the eligible platform primitive
```

The unresolved integration question is the exact same-lifecycle bridge between the eligible Secure Enclave authority primitive and the existing `/run/stegverse/vault-agent.sock` signer operation. That bridge must reuse an existing authenticated resident path or be implemented as the smallest same-owner adapter; it must not create a second signer daemon or alternate credential authority.

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
```

## Next

1. Reuse the existing Secure Enclave P-256 mechanics to define a purpose-distinct TVC admission-authority key candidate with its own application tag and `tvc://authority-key/p256/...` identity; do not alter the recipient key tag or candidate semantics.
2. Bind the distinct authority primitive to the existing `OpaqueRecipientAdmissionSigner` operation through the smallest authenticated same-lifecycle adapter; do not create a second signer daemon/socket owner.
3. Preserve fail-closed behavior when the authority primitive or exact key identity is unavailable.
4. Materialize one production authority key under TV/TVC control on an authenticated eligible resident and project only its public P-256 JWK/key ID.
5. Observe authentic runtime custody and issue one fresh WorkerCoordinator-fence/lease-bound admission through the merged TVC adapter.
6. Return to `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001` only after the signed admission is authentically observed.

## Manual work

None. Do not create, paste, export, upload, reconstruct, or screenshot the production authority private key in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or repository state.
