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
- StegOS PR #356 created the role-separated Secure Enclave authority-key candidate source. After an unrelated stale Device Continuity test was reconciled separately in StegOS PR #357 (`312a7c494d7f7e3e42d0c85f13c281a3daad9603`), PR #356 exact head `7a6c35b204233dc6a5460288f5a2ce5a7aee62a1` passed StegOS CI `34713849035`, iOS Apple Toolchain Validation `34713849131`, iOS Device Package Validation `34713849084`, and GADI native boundary defense validation `34713849085`, then squash-merged at `e81b981c1218fca2031a43207afd0a419ff1263d`.
- The merged StegOS authority candidate uses application tag `org.stegverse.stegos.tvc.recipient-admission-authority.p256`, derives a public `tvc://authority-key/p256/...` identity, exposes only public JWK/digest/key ID plus an opaque Secure Enclave handle, and explicitly records `privateKeyExported=false`, `recipientKeyReused=false`, `signingReachable=false`, and `authorityEffect=NONE_AUTHORITY_KEY_CANDIDATE_ONLY`.
- The existing recipient key remains separate at tag `org.stegverse.stegos.tvc.skap.browser-recipient.coinbase.p256` and cannot satisfy the authority role.
- TVC PR #418 consolidated the caller side onto the existing vault-agent boundary. Exact head `e91560722284d8e36a339d6909fe7ae65c4c395f` passed Recipient Admission Signing Custody Validation `34714208673` and squash-merged at `5edf023aa7d45e1f525dd1bb556d25cacd35ae74`.
- TVC's signed-admission issuer still validates exact WorkerCoordinator task/claim/fence freshness and handoff authority before it invokes the signing callable. That independently establishes the caller-side work predicate without requiring a prior signature from the same authority key.
- `scripts/tvc_recipient_admission_resident_signer.py` now accepts only `/run/stegverse/vault-agent.sock`, emits the exact `stegverse.vault.agent.recipient_admission_sign_request.v1` / `recipient_admission_sign` contract, verifies the returned signature against the separately materialized public JWK, and explicitly rejects the legacy `/run/stegverse/tv-tvc-credentials/recipient-admission-signer.sock` path.
- The signer operation therefore has one caller-side credential boundary and no second signer socket. The remaining backend problem is wholly behind the existing `VaultAgentService` operation.
- The current `stegwallet/container_vault_agent.py` production launcher still constructs `VaultAgentService(args.socket, store)` without a recipient-admission signer. Therefore the merged opaque signer interface remains fail-closed but not yet production-reachable.
- No authority-signing public URL action exists in StegOS. The existing `stegverse://tvc-recipient-capability` envelope remains insufficient authentication for arbitrary authority signing, so no signing oracle has been introduced.
- StegOS `TVCAuthenticatedRecipientCapabilityAdapter` verifies a completed signed admission downstream, but it cannot authenticate a request to the same authority signer without circularly requiring the authority signature being requested.
- No authenticated resident device is connected through the available remote-device surface, so actual production authority-key materialization, platform-backend binding, matching public trust-anchor binding, and fresh production signing remain unobserved.

## Exact remaining problem

Bind one eligible non-exportable platform signer backend to the existing `VaultAgentService` `OpaqueRecipientAdmissionSigner` interface so the canonical `/run/stegverse/vault-agent.sock` request can reach the distinct authority key without creating another signer daemon/socket, exposing a public signing oracle, or reusing the recipient key.

The final backend surface remains exactly:

```text
authority_key_id() -> public authority identifier
sign(message bytes) -> DER ECDSA P-256/SHA-256 signature
```

It must not expose private-key bytes, PEM, private JWK `d`, seed, scalar, exportable PKCS#8, or a secret-store string representation.

## Source-complete caller and role separation

The following portions are now source-implemented and validated:

```text
recipient key tag != authority key tag
recipient key ID namespace != tvc://authority-key/p256/<id>
recipient candidate may never satisfy OpaqueRecipientAdmissionSigner
private authority key candidate remains non-exportable inside Secure Enclave
public deep-link signing is absent
TVC validates WorkerCoordinator task/claim/fence before signer invocation
TVC caller uses only /run/stegverse/vault-agent.sock
legacy second recipient-admission signer socket is rejected
vault-agent response is checked for purpose, key ID, algorithm, no private material, no GitHub/model signing authority
returned signature is verified against the public JWK
```

These source merges do not prove production key materialization or production signing.

## Backend authentication constraint

The caller-side TVC work predicate is independently checked before the signing callable is invoked, but the platform backend still needs a trustworthy same-lifecycle binding from the existing vault agent to the actual non-exportable authority primitive. The backend must not treat callback allowlisting, unsigned deep links, GitHub workflow identity, model output, heartbeat state, or recipient-key possession as authority-signing authorization.

If the Secure Enclave candidate is used, the bridge must preserve the exact authority key ID, distinguish it from the recipient key, and expose only the two opaque signer operations to the vault agent. Any cross-process or cross-surface transport used solely to reach the platform primitive must remain an implementation detail of the existing vault-agent signer backend, not a second credential/signing authority or independently callable public signer.

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

1. Inventory existing resident/local Interlock/InTr transport surfaces that can be reused internally by a vault-agent platform backend to reach the role-separated Secure Enclave authority primitive without becoming a second signing authority.
2. Implement the smallest `OpaqueRecipientAdmissionSigner` backend adapter behind the existing `VaultAgentService`; fail closed on missing platform primitive, exact key-ID mismatch, unavailable authenticated transport, or recipient-key substitution.
3. Wire the backend into the existing vault-agent launcher lifecycle without a second daemon/socket owner.
4. Materialize one production authority key under TV/TVC control on an authenticated eligible resident and project only its public P-256 JWK/key ID.
5. Bind the matching public JWK as the recipient-admission trust anchor without private material.
6. Observe authentic runtime custody and issue one fresh WorkerCoordinator-fence/lease-bound admission through `/run/stegverse/vault-agent.sock`.
7. Return to `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001` only after the signed admission is authentically observed.

## Manual work

None. Do not create, paste, export, upload, reconstruct, or screenshot the production authority private key in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or repository state.
