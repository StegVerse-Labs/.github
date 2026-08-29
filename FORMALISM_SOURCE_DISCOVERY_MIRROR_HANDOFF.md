# Formalism Source Discovery Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs
repository: .github
branch: main
goal_id: FORMALISM-SOURCE-DISCOVERY-001
parent_goal: FORMALISM-MANIFOLD-IMPLEMENTATION-ADMISSION-001
issue: #102
pull_request: #103
credential_authority: TV/TVC
github_token_required: false
network_checkout_authority: NONE_IN_THIS_GOAL
archive_ready: false_for_active_machine_task
```

## Originating requirement

Remove the chat/manual `STEGVERSE_FORMALISM_ROOTS_JSON` selection dependency. Registration does not prove executable continuation unless resident workers can locate their required first-cohort source roots. This goal installs deterministic local discovery and a durable roots manifest consumed automatically by the existing formalism/manifold worker adapters.

Missing repositories are not silently fetched or treated as available. A missing/ambiguous/handoff-less source fails closed and requires a separately admitted TV/TVC-compatible materialization successor.

## Initial cohort

`Admissible-Existence/AE`, `RTG`, `GTG`, `TT`, `STCM`, and `StegVerse-Labs/StegCore`.

## Installed implementation

```text
control/formalism-source-discovery.json
handoffs/SHWP-FORMALISM-SOURCE-DISCOVERY-001.json
control/worker-registry.d/formalism-source-discovery-001.json
control/process-worker-adapters.d/formalism-source-discovery-001.json
workers/formalism_source_discovery_worker.py
scripts/run_formalism_manifold_with_discovered_roots.py
tests/test_formalism_source_discovery_worker.py
control/process-worker-adapters.d/formalism-manifold-orchestration-001.json
receipts/formalism-source-discovery/**
```

Discovery checks canonical local workload/source paths under the control repo, `~/.stegverse`, and `/var/lib/stegverse`, including owner/repository and repository-only layouts. An explicit `STEGVERSE_FORMALISM_ROOTS_JSON` remains a non-secret override but is no longer required.

`formalism_source_discovery_worker.py` accepts a root only when it is a directory with at least one `*_MIRROR_HANDOFF.md` at repo root or `docs/`; duplicate valid search roots fail as ambiguous unless an explicit non-secret override resolves them. It performs no network checkout.

`run_formalism_manifold_with_discovered_roots.py` injects a completed `stegverse.formalism-roots-manifest/v0.1` into the existing four source-reading formalism lanes when no explicit root map exists. A malformed, authorizing, network-derived, or credential-requiring manifest is rejected.

## Authority boundary

Observation/discovery only. No clone/pull/fetch/authentication, no AE/StegCore mutation, no formalism standing, and no execution authority. Credential authority remains TV/TVC. GitHub/provider/wallet credentials are neither accepted nor forwarded.

## Claims and convergence

The predecessor implementation-admission claim is now `RELEASED_TRANSFERRED` with PR #101 merge evidence and this source-discovery claim as successor for the source-root deficiency. `OWNER_SOURCE_MUTATION_EXECUTOR_NOT_GENERALIZED` is intentionally not claimed complete or transferred by that release.

Implementation claim:

```text
control/session-implementation-claim-2026-08-13-formalism-source-discovery.json
state: RELEASED_TRANSFERRED_TO_MACHINE_CONTINUATION
PR #103 merged head: 00ead9d14a44be827c4110f3866556402a2d899b
merge: 5a5c77d45817407dc0b2f5010ba56a36ecdd5d5e
machine continuation: SHWP-FORMALISM-SOURCE-DISCOVERY-001 / formalism-source-discovery-worker
resident discovery receipt: NOT OBSERVED
missing-source absence set: NOT OBSERVED
```

The implementation claim is released because the source-discovery implementation and automatic roots-manifest consumption are merged and exact-head validated. No concrete missing-source materialization successor is required until resident discovery actually observes a missing/ambiguous/handoff-less source. Such an observation remains fail-closed and must derive a separately authorized machine successor rather than returning to chat selection.

The generalized owner-source mutation executor deficiency remains separate and unresolved; it is not transferred into or satisfied by this source-discovery claim release.

## Hosted validation

PR #103 final merged head `00ead9d14a44be827c4110f3866556402a2d899b` received:

```text
Heartbeat Worker Project - Validation Only / No GitHub Token Authority
run: 31770541037
result: SUCCESS

Validate organization control plane - No GitHub Token Authority
run: 31770541030
result: SUCCESS

Render Organization Handoff State - No GitHub Token Authority
run: 31770541087
result: SUCCESS
```

The heartbeat validation passed compilation, canonical JSON, executable handoffs, the complete deterministic test suite, non-mutating heartbeat dry run, ephemeral projections, and non-authorizing workflow checks. No GitHub credential token or non-TV/TVC credential path was introduced.

## Current state

```text
source-discovery worker: IMPLEMENTED
roots-manifest contract: IMPLEMENTED
formalism adapter consumption: IMPLEMENTED
fail-closed missing/ambiguous handling: IMPLEMENTED
hosted validation: PASS
canonical admission: MERGED_VALIDATED
resident discovery receipt: NOT OBSERVED
actual first-cohort roots present on resident carrier: NOT YET PROVEN
missing-source materialization successor: NOT YET INSTALLED because resident absence set is not yet observed
owner-source mutation executor: STILL UNRESOLVED / SEPARATE LANE
```

## Archive condition

The source-discovery implementation claim no longer requires this chat: execution is durably owned by the registered machine worker. The active source-discovery task itself remains nonterminal until resident roots are observed and a roots manifest is emitted.

The broader formalism/manifold workstream remains nonarchive for separate unresolved lanes, including the generalized owner-source mutation executor. That broader condition must not be encoded as a chat/thread dependency on SHWP-FORMALISM-SOURCE-DISCOVERY-001.
