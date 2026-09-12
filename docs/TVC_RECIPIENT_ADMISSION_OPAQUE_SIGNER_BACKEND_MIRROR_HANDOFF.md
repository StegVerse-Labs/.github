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
- The signer operation is now an operation of the existing `VaultAgentService`; no second signer daemon/socket owner is required or authorized.
- Repository search found no separate TVC admission-authority non-exportable signer backend.
- StegOS has an iPhone Secure Enclave recipient key, but that key is a recipient candidate with `authorityEffect=NONE_PLATFORM_KEY_CANDIDATE_ONLY`. It must not be promoted into the TVC admission authority key.
- Authentic production authority-key custody, matching public JWK binding, and fresh production signed admission remain unobserved.

## Exact remaining problem

Materialize or bind one purpose-specific TVC-controlled non-exportable P-256 authority signer that implements the existing `OpaqueRecipientAdmissionSigner` interface inside the existing vault-agent runtime lifecycle.

The backend may expose only:

```text
authority_key_id() -> public authority identifier
sign(message bytes) -> DER ECDSA P-256/SHA-256 signature
```

It must not expose private-key bytes, PEM, private JWK `d`, seed, scalar, exportable PKCS#8, or a secret-store string representation.

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

1. Inspect the authenticated runtime environment for an eligible already-owned non-exportable key capability that can implement `OpaqueRecipientAdmissionSigner` without changing authority ownership.
2. If none exists, implement the smallest TVC-owned backend adapter for the actual eligible platform primitive; do not emulate production custody with a repository PEM/test key.
3. Bind that backend to the existing vault-agent process lifecycle rather than a second daemon.
4. Materialize one production authority key under TV/TVC control and project only its public P-256 JWK/key ID.
5. Observe authentic runtime custody and issue one fresh WorkerCoordinator-fence/lease-bound admission through the merged TVC adapter.
6. Return to `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001` only after the signed admission is authentically observed.

## Manual work

None at this source/decomposition stage. Do not create, paste, export, upload, or reconstruct the production authority private key in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or repository state.
