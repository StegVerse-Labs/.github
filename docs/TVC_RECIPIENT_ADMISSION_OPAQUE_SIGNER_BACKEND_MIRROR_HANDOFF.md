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
- StegOS PR #356 implemented the purpose-distinct Secure Enclave P-256 authority-key candidate and merged at `e81b981c1218fca2031a43207afd0a419ff1263d` after StegOS CI `34713849035`, Apple Toolchain `34713849131`, Device Package `34713849084`, and GADI native-boundary `34713849085` passed. The authority key remains role-separated from the recipient key and non-exportable.
- TVC PR #418 consolidated the caller onto `/run/stegverse/vault-agent.sock`, rejected the legacy second signer socket, preserved WorkerCoordinator task/claim/fence validation before signer invocation, passed Recipient Admission Signing Custody Validation `34714208673`, and merged at `5edf023aa7d45e1f525dd1bb556d25cacd35ae74`.
- `stegfin-governance` PR #102 implemented the fail-closed `PlatformOpaqueRecipientAdmissionSigner` backend. Exact head `adaeb72920eb155ee84ccab09c684833431041e0` passed Governance `34714539071`, StegWallet governance `34714539078`, and iOS first-passkey `34714539141`, then merged at `6a42422d1faf2449f18f98efcd6b0c61bd0bb733`.
- `.github` PR #1619 reconciled the platform-backend merge after organization control `34714621760`, deterministic suite `34714621800`, and Heartbeat `34714621793` passed; it squash-merged at `d308c4061b976f022dfd3598b50a05a9d8e402f9`.
- Investigation found a reusable independent identity mechanism already in StegOS: `Ed25519PublicKeyVerifierPlugin` cryptographically verifies a signed-payload SHA-256 digest using a separately trusted public-key registry; `SoloMachineBinding` and `SoloMachineKeyState` already bind/rotate verifier-key references without granting credential, execution, transition, claim/fence, or custody authority.
- The separate `governed-agent-passport` Ed25519 key generator was explicitly rejected for this lane because it serializes raw unencrypted Ed25519 private-key bytes. It is not used for production channel identity.
- `stegfin-governance` PR #103 implemented the resident-side authenticated carrier as `SignedInTrRecipientAdmissionPlatformTransport`. The first exact head exposed a test-only false positive because the test rejected the required control field name `privateKeyMaterialRequested=false`; the test was corrected without changing transport semantics.
- PR #103 corrected exact head `407fd495637436a2a69ea8f59f434c17f8121da5` passed iOS first-passkey `34718286407`, Governance `34718286411`, and StegWallet governance `34718286413`, then squash-merged at `80797f67d71c2f815f082a1f71f8df37778ae110`.
- The authenticated transport reuses the existing StegOS `signed-payload-v1` / `signature-ready-payload-v1` / `signature-envelope-v1` shape. It canonicalizes the exact platform-sign request, binds its SHA-256, channel signer ID/key ref, bounded issue/expiry times, InTr carriage, TV/TVC + Interlock/InTr labels, and explicit no-authority/no-private-material predicates, then signs the raw 32-byte SHA-256 digest through an injected Ed25519 channel signer.
- The transport module owns neither the channel private key nor the network route. Universal InTr remains carriage only. The channel identity authenticates requester/carriage identity and explicitly grants no TV/TVC signing authority, Interlock/InTr transition authority, WorkerCoordinator claim/fence, credential custody, or runtime completion.
- The iPhone side does **not yet** contain the matching authenticated platform-request verifier. Therefore the source path is currently one-sided: the resident can construct a cryptographically authenticated envelope, but the Secure Enclave authority key remains non-signing-reachable until the iPhone independently verifies the registered channel public key and exact request/nonce/expiry bindings.
- The iOS Xcode project uses explicit source membership rather than filesystem-synchronized source groups. A new Swift file cannot be treated as integrated merely by adding it to the repository; the verifier must land in an already-compiled source unit or be added to the Xcode project explicitly and pass Apple-toolchain validation.
- `stegwallet/container_vault_agent.py` still constructs the production `VaultAgentService` without the platform backend because a production channel signer, matching iPhone public-key registration, and verified platform endpoint are not yet authentically available.
- No authenticated resident device is connected through the available remote-device surface, so production channel-key custody, production authority-key materialization, public trust-anchor binding, and fresh production signing remain unobserved.

## Source-complete portions

```text
opaque vault-agent signing protocol
single existing vault-agent caller path
WorkerCoordinator invocation validation before TVC signer call
role-separated Secure Enclave authority-key candidate
recipient-key non-reuse
fail-closed platform OpaqueRecipientAdmissionSigner adapter
resident-side Ed25519 authenticated InTr envelope construction
exact platform-request SHA-256 binding
bounded channel identity / issue / expiry metadata
no channel private-key loader in transport module
no network stack in transport module
no public signing URL
no duplicate signer socket/daemon
```

These source merges do not prove iPhone-side channel verification, production channel-key custody, launcher injection, authority-key materialization, public trust-anchor binding, or production signing.

## Exact remaining problem

Complete the other half of the authenticated channel on the iPhone: verify the separately registered Ed25519 channel public key over the exact signed-payload digest, reject expiry/replay/nonce/key/JWK/message drift, and only then permit the role-separated P-256 Secure Enclave authority key to execute the existing admission-sign operation. The public recipient-capability deep link must remain unable to invoke this signing path.

After that source path is Apple-toolchain validated, bind a production channel signer/public-key pair through the existing vault-agent lifecycle and current-iPhone platform runtime without creating a second credential authority or exporting either production private key.

## Invariants

```text
TV/TVC remains credential/signing authority
Interlock/InTr remains transition authority
existing /run/stegverse/vault-agent.sock remains the credential boundary
Universal InTr is carriage only
Ed25519 channel identity authenticates carriage only
channel identity grants no signing/credential/transition authority
no second signer daemon or alternate credential path
GitHub/CI/model/Heartbeat have no signing authority
recipient Secure Enclave key is not the admission authority key
production authority private key is non-exportable
production channel private key is not placed in GitHub/CI/chat/Drive/KV/logs
public trust anchor contains public verification material only
no public unauthenticated authority-signing route
no circular same-key authentication of a signing request
```

## Next

1. Implement the matching iOS authenticated-platform-request verifier using the existing signed-payload/Ed25519 verifier semantics and a separately registered channel public key.
2. Bind exact envelope schema, channel signer key ref, platform request SHA-256, request nonce, issue/expiry window, authority key ID, authority public-JWK digest, message digest, application tag, and algorithm; retain replay state and fail closed on reuse.
3. Permit `TVCRecipientAdmissionAuthorityKeyCandidateAdapter` to sign only after that verifier succeeds; do not add authority signing to `TVCRecipientCapabilityURLCoordinator` or any other public deep-link route.
4. Ensure the verifier/signing source is actually in the StegOS Xcode build and require Apple Toolchain + Device Package validation before merge.
5. Materialize/bind one production channel identity and the distinct production authority key only on an authenticated eligible resident; project public verification material only.
6. Inject `PlatformOpaqueRecipientAdmissionSigner` plus `SignedInTrRecipientAdmissionPlatformTransport` into the existing vault-agent launcher only when both production identities and the authenticated iPhone path are available; otherwise remain fail-closed.
7. Observe one fresh WorkerCoordinator-fence/lease-bound signed admission through `/run/stegverse/vault-agent.sock`, verify against the bound authority public JWK, then return to `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001`.

## Manual work

None. Do not create, paste, export, upload, reconstruct, or screenshot the production TVC authority private key or production channel private key in GitHub, CI, chat, Drive, ordinary KV, logs, screenshots, or repository state.
