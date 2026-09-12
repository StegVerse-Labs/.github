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

- `stegfin-governance` PR #100 merged the private-key-free opaque recipient-admission signing protocol at `c16d80b9b310add94565dfc40104fc49a889e9c3`.
- `stegfin-governance` PR #101 merged dispatch integration into the existing `VaultAgentService` at `ed6a97dd9ae988323373b9310ab411f0da82e6d3`; `/run/stegverse/vault-agent.sock` remains the only admitted credential/signing process boundary.
- `.github` PR #1589 registered this canonical child and merged at `90bec60daaa295757bbb5166afe68d9d31634786` after all required exact-head validations passed.
- StegOS PR #356 implemented the purpose-distinct Secure Enclave P-256 authority-key candidate and merged at `e81b981c1218fca2031a43207afd0a419ff1263d` after StegOS CI `34713849035`, Apple Toolchain `34713849131`, Device Package `34713849084`, and GADI native-boundary `34713849085` passed. The authority tag is `org.stegverse.stegos.tvc.recipient-admission-authority.p256`; the existing recipient tag remains separate. The candidate reports `privateKeyExported=false`, `recipientKeyReused=false`, `signingReachable=false`, and `authorityEffect=NONE_AUTHORITY_KEY_CANDIDATE_ONLY`.
- TVC PR #418 consolidated the caller onto `/run/stegverse/vault-agent.sock`, rejected the legacy second signer socket, preserved WorkerCoordinator task/claim/fence validation before signer invocation, passed Recipient Admission Signing Custody Validation `34714208673`, and merged at `5edf023aa7d45e1f525dd1bb556d25cacd35ae74`.
- `.github` PR #1618 reconciled that caller consolidation and merged at `9d12a004ae9dca391266db493300ea2f37732dbf` after Heartbeat `34714283799`, deterministic suite `34714283786`, and organization-control `34714283782` passed.
- `stegfin-governance` PR #102 implemented `PlatformOpaqueRecipientAdmissionSigner`, a fail-closed backend adapter that satisfies the existing `OpaqueRecipientAdmissionSigner` interface only through an injected independently authenticated platform transport. Exact head `adaeb72920eb155ee84ccab09c684833431041e0` passed Governance `34714539071`, StegWallet governance `34714539078`, and iOS first-passkey `34714539141`, then squash-merged at `6a42422d1faf2449f18f98efcd6b0c61bd0bb733`.
- The merged platform backend binds exact TVC authority-key ID, public-JWK digest, purpose-distinct Secure Enclave application tag, message digest, fresh nonce, signature algorithm, TV/TVC credential authority, and Interlock/InTr transition authority. It fails closed on recipient-key reuse, private-key export/material, public invocation, GitHub/model signing authority, missing transport authentication, or identity drift.
- The platform backend owns no socket, HTTP client/server, URL/deep-link handler, scheduler, daemon, credential lookup, or private-key loader. It therefore does not create a second credential or signer path.
- Existing Universal InTr/HIL carriage is not sufficient authority-signing authentication by itself: relay ingress checks payload hash/origin/authorization-ID shape but does not cryptographically authenticate that ID at the receiver. Upstream TVC relay EGRESS authorization binds a validated single-use execution grant, exact route, payload hash, and next-hop identity, but the authorization/grant artifacts are hash-bound rather than a standalone device-verifiable cryptographic source identity.
- No existing mutual-TLS/client-certificate identity path was found in StegOS, TVC, or stegfin-governance. Accordingly no transport was fabricated or promoted into production authentication.
- `stegwallet/container_vault_agent.py` still constructs the production `VaultAgentService` without this platform backend because no eligible independently authenticated transport exists yet.
- No authenticated resident device is connected through the available remote-device surface, so production authority-key materialization, backend transport binding, public trust-anchor binding, and fresh production signing remain unobserved.

## Source-complete portions

```text
opaque vault-agent signing protocol
single existing vault-agent caller path
WorkerCoordinator invocation validation before TVC signer call
role-separated Secure Enclave authority-key candidate
recipient-key non-reuse
fail-closed platform OpaqueRecipientAdmissionSigner adapter
exact authority-key/public-JWK/message/nonce binding
no private-key input/export surface
no public signing URL
no duplicate signer socket/daemon
no transport implementation hidden inside the backend adapter
```

These source merges do not prove production key materialization, transport authentication, vault-agent launcher injection, public trust-anchor binding, or production signing.

## Exact remaining problem

Implement one **independently authenticated resident/platform transport** that can be injected into `PlatformOpaqueRecipientAdmissionSigner` and can reach the role-separated non-exportable authority primitive without becoming a second credential/signing authority or public signing oracle. Then inject that backend into the existing vault-agent launcher lifecycle.

The transport must prove its own authentication independently of:

```text
callback allowlisting
unsigned deep links
GitHub workflow identity
model output
heartbeat/HB state
recipient-key possession
hash-only execution-grant or relay-authorization structure
```

Universal InTr may be reused as carriage only if a stronger independently verifiable authentication binding is added or already evidenced at the platform endpoint. InTr carriage itself remains non-authorizing.

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
transport authentication is independently evidenced
```

## Next

1. Identify or build the smallest independently verifiable resident/platform channel identity suitable for the current-iPhone authority primitive; prefer reuse of existing identity/certificate machinery if found, otherwise add a bounded authenticated-carrier primitive without granting it signing authority.
2. Implement the corresponding `AuthenticatedRecipientAdmissionPlatformTransport` adapter and exact iOS-side request verifier; bind authority key ID, public-JWK digest, message digest, nonce, expiry/replay state, and the independent channel identity.
3. Inject `PlatformOpaqueRecipientAdmissionSigner` into the existing `VaultAgentService` launcher lifecycle only when that authenticated transport is available; otherwise remain fail-closed.
4. Materialize one production authority key under TV/TVC control on an authenticated eligible resident and project only its public P-256 JWK/key ID.
5. Bind the matching public JWK as the recipient-admission trust anchor without private material.
6. Observe one fresh WorkerCoordinator-fence/lease-bound admission through `/run/stegverse/vault-agent.sock` and verify its signature against the bound public JWK.
7. Return to `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001` only after authentic signed admission exists.

## Manual work

None. Do not create, paste, export, upload, reconstruct, or screenshot the production TVC authority private key in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or repository state.
