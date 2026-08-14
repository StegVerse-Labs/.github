# Formalism Source Discovery Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs
repository: .github
branch: feat/formalism-source-discovery-001
goal_id: FORMALISM-SOURCE-DISCOVERY-001
parent_goal: FORMALISM-MANIFOLD-IMPLEMENTATION-ADMISSION-001
credential_authority: TV/TVC
github_token_required: false
network_checkout_authority: NONE_IN_THIS_GOAL
archive_ready: false
```

## Originating requirement

The formalism/manifold workers currently require `STEGVERSE_FORMALISM_ROOTS_JSON`. Registration alone does not prove executable continuation if a resident machine cannot locate the first-cohort source roots. This goal removes the chat-only/manual root-selection step by installing deterministic discovery of already materialized canonical source/workload trees and a durable roots manifest consumed by the existing workers.

This goal does **not** claim that missing private repositories can be fetched without a separately authorized TV/TVC source-materialization capability. If a required repository is not present locally, the worker must emit a machine-observable blocker naming the exact missing repository and a successor materialization requirement rather than silently treating the source as available.

## Initial cohort

```text
Admissible-Existence/AE
Admissible-Existence/RTG
Admissible-Existence/GTG
Admissible-Existence/TT
Admissible-Existence/STCM
StegVerse-Labs/StegCore
```

## Canonical search roots

```text
<control-repo>/workloads/<owner>/<repo>
<control-repo>/workloads/<repo>
<control-repo>/source/<owner>/<repo>
<control-repo>/source/<repo>
~/.stegverse/workloads/<owner>/<repo>
~/.stegverse/workloads/<repo>
~/.stegverse/source/<owner>/<repo>
~/.stegverse/source/<repo>
/var/lib/stegverse/workloads/<owner>/<repo>
/var/lib/stegverse/workloads/<repo>
/var/lib/stegverse/source/<owner>/<repo>
/var/lib/stegverse/source/<repo>
```

An explicit `STEGVERSE_FORMALISM_ROOTS_JSON` remains an admissible non-secret override, but is no longer the only discovery path.

## Required implementation

```text
control/formalism-source-discovery.json
handoffs/SHWP-FORMALISM-SOURCE-DISCOVERY-001.json
control/worker-registry.d/formalism-source-discovery-001.json
control/process-worker-adapters.d/formalism-source-discovery-001.json
workers/formalism_source_discovery_worker.py
tests/test_formalism_source_discovery_worker.py
receipts/formalism-source-discovery/**
```

The discovery receipt must contain a deterministic repository-to-local-root map and may contain no credential material. The existing formalism/manifold worker will be updated to consume that durable manifest when `STEGVERSE_FORMALISM_ROOTS_JSON` is absent.

## Authority boundary

This worker has observation/discovery authority only. It does not clone, pull, fetch, mutate, or authenticate to GitHub; it does not create formalism standing; it does not mutate AE/StegCore; and it does not grant execution authority. Any missing-source materialization successor must be separately admitted and remain TV/TVC-compatible.

## Active implementation claim

```text
task_id: FORMALISM-SOURCE-DISCOVERY-001
claimant: current ChatGPT formalism/manifold continuation session
claim_state: CLAIMED_FOR_IMPLEMENTATION
collision_scope: new formalism-source-discovery surfaces plus bounded update to workers/formalism_manifold_orchestration_worker.py and its tests/adapters to consume the discovered roots manifest
release_condition: source discovery is hosted-validated, merged to main, existing formalism workers can resolve discovered local roots without chat input, and any still-missing source has a durable executable materialization owner rather than an unassigned manual step
```

## Archive condition

This session is not archive-ready while source-root availability remains a prerequisite that only a chat/human can satisfy, or while a missing-source materialization capability has no active executor.
