# SV-DN-1 Exact Source Materialization Mirror Handoff

## Canonical scope

```text
goal_id: SV-DN1-EXACT-SOURCE-MATERIALIZATION-001
task_id: SV-DN1-SOURCE-MATERIALIZATION-001
repository: StegVerse-Labs/.github
branch: main
canonical product owner: StegVerse-org/stegverse-demo-suite
canonical product handoff: docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md
upstream runtime manifest: config/sv_dn1_runtime_source_manifest.json
downstream consumer: SV-DN1-RESIDENT-OBSERVER-001
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: SOURCE_MATERIALIZATION_ONLY
```

## Goal

Close the machine-execution prerequisite that currently leaves the resident observer in `HANDOFF_READY`: exact pinned `StegVerse-org/stegverse-demo-suite` source is not yet observed on the sovereign carrier.

This lane is a source-materialization prerequisite only. It MUST NOT:

- observe Hugging Face;
- execute SV-DN-1;
- perform Interlock/InTr traversal;
- perform SDK admission;
- perform StegCore/StegGate governance;
- write repositories;
- use GitHub credentials or tokens;
- claim production evaluation success.

## Source of truth order

1. `docs/SV_DN1_SOURCE_MATERIALIZATION_MIRROR_HANDOFF.md`
2. `handoffs/SV-DN1-SOURCE-MATERIALIZATION-001.json`
3. `control/worker-registry.d/sv-dn1-source-materialization-001.json`
4. `control/process-worker-adapters.d/sv-dn1-source-materialization-001.json`
5. `workers/sv_dn1_source_materialization_worker.py`
6. `StegVerse-org/stegverse-demo-suite/config/sv_dn1_runtime_source_manifest.json`
7. `StegVerse-Labs/.github/docs/SV_DN1_RESIDENT_OBSERVER_MIRROR_HANDOFF.md`

Newer live runtime evidence overrides older chat/session claims.

## Why this lane is distinct

The resident observer is intentionally forbidden from remote checkout or repository acquisition. That preserves the observation worker's narrow authority.

The missing prerequisite is therefore assigned to a separate, bounded source-materialization worker that may acquire exact public source bytes without credentials and make them available on the same sovereign carrier.

This is not a duplicate observation lane. It owns only:

```text
pinned public source acquisition
-> byte identity validation
-> local source materialization
-> materialization receipt
```

The resident observer remains the sole owner of the first live Hugging Face observation.

## Pinned source identities

The materializer MUST first obtain the canonical current runtime manifest from the public repository and verify its Git blob SHA-1 before trusting it.

Pinned manifest:

```text
repository: StegVerse-org/stegverse-demo-suite
path: config/sv_dn1_runtime_source_manifest.json
expected_manifest_git_blob_sha1: 47760f63898fff0f5ba6dfab97eee5acd7290c9b
manifest source_basis_commit: 4988d453419f43404100c69dd97dd1785d7e0a75
```

Non-executable resident-required support files are separately pinned from current canonical main:

```text
docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md
git_blob_sha1: ba9acf76fd6eb488e5f3b9f9be01bb17e3a02d48

tasks/SV-DN1-RESIDENT-OBSERVER-001.json
git_blob_sha1: 0dbe655a86bea3d2a0f77aa2ada57a62882f00db
```

The manifest's `files` map remains authoritative for all production-critical executable/config/schema bytes.

## Public source acquisition boundary

Allowed network source:

```text
scheme: HTTPS
host: raw.githubusercontent.com
authentication: NONE
credential_forwarding: false
repository: StegVerse-org/stegverse-demo-suite
```

The worker fetches:

1. the pinned runtime manifest from canonical `main`;
2. every manifest-listed source file at the manifest's `source_basis_commit`;
3. the two separately pinned resident-required support files from canonical `main`.

Every byte object is validated using Git blob SHA-1 before local persistence.

No archive extraction, Git client, remote checkout, provider credential, GitHub API token, or repository mutation is required.

## Materialization destination

Default local destination:

`~/.stegverse/source/stegverse-demo-suite`

The materialized root MUST contain the canonical relative paths expected by the resident observer.

Durable materialization evidence is written only to the ProcessWorkerAdapter bound-state namespace:

```text
materialization/source-manifest.json
materialization/validation.json
receipts/latest.json
```

The source tree itself is runtime materialization, not repository writeback.

## Completion boundary

Completion requires:

```text
canonical manifest blob identity: VERIFIED
manifest schema/hash profile: VERIFIED
all manifest source blobs: VERIFIED
resident handoff blob: VERIFIED
resident task blob: VERIFIED
materialized source root: PRESENT
post-write full pinned validation: PASS
credential use: false
GitHub token use: false
repository writeback: false
```

Completion transition:

`SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE`

The completion receipt MUST expose the exact local source root so the resident observer can consume the same source without remote acquisition.

## Failure / retry posture

Public source unavailable, missing object, hash mismatch, manifest drift, or filesystem write failure MUST fail closed.

A canonical manifest blob mismatch returns `HANDOFF_READY` with a machine-readable blocker indicating that the source pin changed and this materialization task must be reconciled before execution.

No fallback to `main` source files without hash validation is allowed.

## Successor

After this task completes:

```text
SV-DN1-SOURCE-MATERIALIZATION-001
-> SV-DN1-RESIDENT-OBSERVER-001
```

The resident observer may then consume the exact local root and proceed with its existing fenced WorkerCoordinator claim.

This task does not claim that the resident observer has executed merely because source materialization completed.

## Current state

```text
canonical runtime manifest: MERGED
resident source-pin validation: MERGED
resident materialization blocker: OBSERVED
dedicated source-materialization handoff: MERGED
dedicated worker: MERGED
worker registry/process adapter: MERGED
runtime materialization receipt: NOT OBSERVED
resident observation: NOT OBSERVED
```

## Merge and validation evidence

```text
PR #337: MERGED
merge_commit: f5ca06543d1dd17b3095d424dc5eed578c15299d
validated_head: a60e928c8ba304ab2457e8f1fd8c4119b07d7a1f
organization control plane run 33135530888 / job 98734500203: PASS
heartbeat worker validation run 33135530923 / job 98734508189: PASS
complete deterministic repository suite: PASS
AE conformance: PASS
no GitHub token authority: PASS
atomic source swap cwd-preservation regression: PASS
```

The source-materialization worker is registered and machine-owned on main. Runtime completion still requires an authentic sovereign WorkerCoordinator claim/fence and resulting materialization receipt.

## Independent task-control admission

PR #343 merged the explicit independent-task-control contract for this root task:

```text
dependencies: []
authority_domain: INDEPENDENT_TASK_CONTROL
claim_state: AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM
fresh_fence_required: true
minimum_fencing_token_exclusive: 22
heartbeat_grants_execution_authority: false
merge_commit: 75fbb638a8003d42517620cc95b383070ea3b15e
```

The merged sovereign first-round chain in `docs/SV_DN1_SOVEREIGN_EXECUTION_CHAIN_MIRROR_HANDOFF.md` may target this task first. Runtime completion remains NOT OBSERVED.

## Archive readiness

This handoff is the canonical continuation source for exact SV-DN-1 source materialization. Once merged, the lane can be recovered and executed without the originating chat.
