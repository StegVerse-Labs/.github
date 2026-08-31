# Publisher Universal InTr Artifact Transfer Mirror Handoff

Updated: 2026-08-31

```text
goal_id: SHWP-PUBLISHER-ARTIFACT-TRANSFER-001
issue: StegVerse-Labs/.github#582
destination_source: GCAT-BCAT-Engine/Publisher@173cf4db19b4795a82fcca3774b62926d29e78b7
profile: publisher-artifact-transfer
state: SOURCE_IMPLEMENTATION_IN_PROGRESS
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

## Canonical event

```text
KV / KnowledgeVault:DocumentExport
 -> DEVICE_SYSTEM
 -> STEGOS_ECOSYSTEM / Publisher:Ingress
 -> Publisher destination-owned render
 -> Publisher:Export
 -> DEVICE_SYSTEM
 -> KV / KnowledgeVault:DocumentImport
```

The inbound materialization request is non-authorizing. Publisher-specific shared
ingress must receive the exact canonical payload bytes, hash them independently,
persist them write-once, and only then invoke the existing-authority WorkerCoordinator
task. The task reconstructs the canonical StegOS connector intent, issues the forward
hop receipts only after exact payload observation, executes merged Publisher transfer
semantics, and uses `CanonicalInTrConnector.prepare_response()` for the return path.

The task may stage the first return hop to the device. It must not claim the terminal
KV hop, KV import, publication, release, or global activation until separately observed.

The exact payload and return packet are transport objects; receipt objects contain only
hashes/references and no document plaintext.
