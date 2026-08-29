# SV-DN-1 Production Source Preparation Mirror Handoff

## Canonical scope

```text
goal_id: SV-DN1-PRODUCTION-SOURCE-PREPARATION-001
task_id: SV-DN1-PRODUCTION-SOURCE-PREP-001
repository: StegVerse-Labs/.github
branch: main
canonical product owner: StegVerse-org/stegverse-demo-suite
canonical product handoff: docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md
upstream runtime dependency: SV-DN1-INTR-RUNTIME-001
downstream task: SV-DN1-SDK-FIRST-ROUND-001
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: SOURCE_PREPARATION_ONLY
```

## Goal

Prepare the exact canonical local production source roots required by the first SV-DN-1 SDK-governed round without introducing a second credential broker, a hosted runtime, or a manual source-copy dependency.

Required roots:

```text
STEGVERSE_SDK_SOURCE_ROOT
STEGVERSE_STEGCORE_SOURCE_ROOT
STEGVERSE_CORE_LITE_SOURCE_ROOT
STEGVERSE_MASTER_RECORDS_SOURCE_ROOT
```

Public repositories are acquired anonymously and hash-checked. Private repositories are requested only through the existing TV/TVC repository-operation spool/broker boundary.

## Source of truth order

1. `docs/SV_DN1_PRODUCTION_SOURCE_PREPARATION_MIRROR_HANDOFF.md`
2. `handoffs/SV-DN1-PRODUCTION-SOURCE-PREP-001.json`
3. `control/worker-registry.d/sv-dn1-production-source-prep-001.json`
4. `control/process-worker-adapters.d/sv-dn1-production-source-prep-001.json`
5. `workers/sv_dn1_production_source_prep_worker.py`
6. `StegVerse-Labs/TVC#92` repository-operation broker lane
7. `docs/SV_DN1_SDK_FIRST_ROUND_MIRROR_HANDOFF.md`

Newer authentic runtime evidence overrides older conversation claims.

## Collision boundary

This lane does NOT create or replace a credential broker.

Private repository acquisition authority remains exclusively:

```text
StegVerse-Labs/TVC
TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001
operation_class: MATERIALIZE_SOURCE_ARCHIVE
credential_authority: TV/TVC
consumer credential: NONE
```

Current broker posture:

```text
PR #92: OPEN / NOT ADMITTED ON MAIN
governed TV/TVC local validation: PENDING
repository admission: PENDING
```

Therefore this worker may emit bounded spool requests, but MUST remain HANDOFF_READY until sanitized materialization receipts and exact local roots are observed.

## Exact source pins

Current canonical source commits captured for this lane:

```text
StegVerse-org/StegVerse-SDK
  commit: 4461a1edf83549c51189ca4217dd75752caf604e

Data-Continuation/core-lite
  commit: 284ddc21a352ee9c7decdd40dd499b7286710bc8

StegVerse-Labs/StegCore
  commit: eb2ef110d09328aa90bf1ed91c18b47a3ba32a71

master-records/orchestration
  commit: baf9272f89ebe515fc4c2413b5d951d28f1e4485
```

Runtime anchor blobs remain:

```text
SDK/stegverse/governance_ingress_runtime.py
  62c5ae4799ae018f6b100766215c3c68078c5b2e

SDK/stegverse/sovereign_validation_runtime.py
  814d4cb607cc2cb4c7a605474fe845e13540898d

StegCore/src/stegcore/transaction_lifecycle.py
  81935669846fedd2867272810b090226b05780ab

core-lite/core_lite/transaction_route.py
  734923a86bfcd4d41d07e0fb8797de50f0fb9408

master-records/orchestration/services/manifest_receipt_custody.py
  26a4c1e082ee91128648b2b9bd13cc32ce915f82
```

A source pin drift is not silently accepted. The task returns HANDOFF_READY / SOURCE_PIN_RECONCILIATION_REQUIRED.

## Public source acquisition

Allowed anonymous acquisition:

```text
https://github.com/StegVerse-org/StegVerse-SDK/archive/<commit>.tar.gz
https://github.com/Data-Continuation/core-lite/archive/<commit>.tar.gz
```

No Authorization header, GitHub token, Git client, or remote checkout is allowed.

Each archive is extracted safely into:

```text
/var/lib/stegverse/source/StegVerse-org/StegVerse-SDK
/var/lib/stegverse/source/Data-Continuation/core-lite
```

and runtime anchor Git blob identities are revalidated after extraction.

## Private source requests

The worker emits two bounded TVC spool warrants under:

```text
~/.stegverse/transport/formalism-tvc-repository/outbox/
```

Destinations:

```text
/var/lib/stegverse/source/StegVerse-Labs/StegCore
/var/lib/stegverse/source/master-records/orchestration
```

Each warrant asserts:

```text
schema: stegverse.tvc-github-repository-operation-warrant/v0.1
operation_class: MATERIALIZE_SOURCE_ARCHIVE
credential_authority: TV/TVC
consumer_credential_present: false
secret_values_present: false
single_use: true
```

The request itself carries no credential and grants no authority.

A new warrant is emitted only if:
- the exact root is absent or its anchor does not match;
- no successful sanitized receipt already binds the same request;
- no unexpired identical request already exists.

## Private receipt acceptance

Accepted receipt location:

```text
~/.stegverse/transport/formalism-tvc-repository/inbox/<operation_id>.json
```

Completion requires:

```text
schema: stegverse.tvc-github-repository-operation-receipt/v0.1
operation_class: MATERIALIZE_SOURCE_ARCHIVE
repository: exact expected repository
result.status: MATERIALIZED
result.commit_sha: exact pinned commit
credential_authority: TV/TVC
credential_value_exposed: false
non_tv_tvc_secret_or_token_used: false
scope_expanded: false
merge_performed: false
```

The local extracted anchor blob is then revalidated independently.

## Dependency position

The first-round chain becomes:

```text
SV-DN1-SOURCE-MATERIALIZATION-001
-> SV-DN1-RESIDENT-OBSERVER-001
-> SV-DN1-INTR-RUNTIME-001
-> SV-DN1-PRODUCTION-SOURCE-PREP-001
-> SV-DN1-SDK-FIRST-ROUND-001
```

This placement lets the public observation and InTr traversal proceed without waiting on private repository acquisition, while still preventing canonical SDK execution before exact production roots are available.

## Bound-state outputs

```text
~/.stegverse/state/sv-dn1-production-source-prep/
  observed/source-roots.json
  requests/private-source-requests.json
  receipts/latest.json
```

No repository writeback occurs.

## Completion transition

`SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE`

Completion requires all four exact local roots present and all five runtime anchor Git blob identities verified.

The completion receipt exposes the four non-secret local root paths for the SDK first-round worker.

## Current state

```text
public source preparation worker: MERGED / VALIDATED
private TVC spool request generation: MERGED / VALIDATED
TVC broker PR #92: OPEN / governed local validation pending
private broker admission: NOT COMPLETE
production source prep runtime receipt: NOT OBSERVED
SDK first round: NOT ANALYZED
```

## Merge and validation evidence

```text
PR #371: MERGED
merge_commit: f488e70fca67e80fa6b674ee7380b0e04c5000f7
validated_head: 25c32163562b877a1510ea04dc8994f9f1cfee30
heartbeat worker validation run 33228272533 / job 99036145798: PASS
organization control plane run 33228272505 / job 99036145748: PASS
complete deterministic repository suite: PASS
executable handoff validation: PASS
AE conformance: PASS
private-transport authority remains TVC-only: PASS
hosted/credential rejection tests: PASS
safe archive extraction tests: PASS
```

Source preparation is now machine-owned and admitted on main. Authentic runtime completion remains pending on an actual sovereign WorkerCoordinator claim/fence plus TVC private-source materialization receipts.

## Archive readiness

This handoff is the canonical continuation source for SV-DN-1 canonical production source preparation.
