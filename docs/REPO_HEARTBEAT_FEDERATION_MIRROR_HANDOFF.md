# Repository Heartbeat Federation Mirror Handoff

## Goal

```text
goal_id: REPO-HEARTBEAT-FEDERATION-001
repository: StegVerse-Labs/.github
branch: main
state: ACTIVE_UNIQUE_WORK
canonical_task_owner: SHWP-REPO-HEARTBEAT-FEDERATION-001 / single StegVerse heartbeat
credential_authority: TV/TVC
github_token_required: false
```

The existing `SHWP-ALL-ORG-FEDERATION-001` lane federates organization readiness for 14 organizations. It does **not** establish repository-level enrollment, normalized commit/ref/runtime identity, freshness/expiry, dependency-loss propagation, or ecosystem-wide repository coverage proof. This task adds that layer under the existing single heartbeat. It does not install an independent heartbeat engine or per-repository scheduler.

## Authoritative files

- `schemas/repo-heartbeat-manifest.schema.json`
- `control/repo-heartbeat-federation.json`
- `workers/repo_heartbeat_federation_worker.py`
- `authorizations/SHWP-REPO-HEARTBEAT-FEDERATION-001.json`
- `handoffs/SHWP-REPO-HEARTBEAT-FEDERATION-001.json`
- `control/worker-registry.d/repo-heartbeat-federation-001.json`
- `cost-basis/worker-runtime/repo-heartbeat-federation.json`
- `tests/test_repo_heartbeat_federation_worker.py`
- `receipts/repo-heartbeat-federation/SHWP-REPO-HEARTBEAT-FEDERATION-001.json` after first admitted execution

## Initial critical denominator

The first required participant set is intentionally bounded to the critical control/runtime/evidence path:

```text
StegVerse-Labs/StegCore
StegVerse-Labs/Continuity
StegVerse-Labs/TV
StegVerse-Labs/TVC
StegVerse-Labs/StegID
StegVerse-Labs/StegAgents
StegVerse-Labs/Site
StegVerse-Labs/ara-admissibility-interop
StegVerse-002/micro-node-runtime
StegVerse-org/LLM-adapter
master-records/orchestration
```

Additional repositories must be added through an admitted inventory transition rather than disappearing into or out of the denominator implicitly. Passive documentation/research repositories should use `REPO_LIVENESS` unless they own runtime/control/service state.

## Manifest semantics

Every participant manifest carries repository identity, organization, participant class, sequence, emitted/fresh-until timestamps, status, capabilities, dependencies, evidence references, and authority metadata. CONTROL/RUNTIME/SERVICE participants must also provide `commit_sha` and `runtime_id`. The contract may carry `ref`, `release_tag`, `handoff_hash`, and `last_success`.

Current authority requirements are fixed:

```text
credential_authority: TV/TVC
heartbeat_grants_execution_authority: false
github_token_required: false
```

A manifest is evidence, not authority.

## Fail-closed coverage semantics

The central worker builds a normalized topology and SHA-256 topology hash. Required participant states fail closed when a manifest is missing, stale, invalid, FAILED, BLOCKED, RETIRED, or loses a required dependency. Required dependency loss propagates to the dependent repository's topology state. Coverage completes only when every required participant is fresh, identity-valid, nonfailed, and dependency-satisfied.

The worker writes only `receipts/repo-heartbeat-federation/**`. It has no cross-repository mutation, credential, policy, deployment, or execution authority.

## Current claim state

```text
implementation claim: CLAIMED_FOR_IMPLEMENTATION by this session until source installation + validation evidence is complete
validation claim: same lane, deterministic source tests first; hosted execution only if a real job runs
integration claim: canonical heartbeat registry-fragment admission
collision boundary: do not modify or replace SHWP-ALL-ORG-FEDERATION-001 organization-level semantics
claim release: after source files are installed, adapter is bound, deterministic tests are validated, and initial coverage receipt path is machine-owned
```

## Incomplete work

1. Bind `process:repo-heartbeat-federation-v1` in `control/process-worker-adapters.json`.
2. Execute deterministic tests and inspect any actual hosted workflow jobs if triggered.
3. Allow the single heartbeat to admit the registry fragment and emit the first fail-closed coverage receipt.
4. Install normalized manifest emitters/files in the required participant repositories, reading each repository's applicable `*_MIRROR_HANDOFF.md` before mutation.
5. Bind TV/TVC signing/attestation to the coverage receipt only if/when an existing TV/TVC signing contract authorizes it; do not invent a second credential system.
6. Expand the participant denominator after the critical path proves coverage semantics.

## Archive conditions

This workstream is not archive-ready until the central repo-heartbeat task is source-complete and machine-owned, the first coverage receipt exists, and every remaining enrollment gap is durably assigned to a specific repository or machine task. Universal ecosystem coverage is a later completion condition; source installation alone is not universal federation.

## Completeness

```text
developed_files: 8/9 planned central source files before adapter binding
validation: 0/2 (deterministic tests; admitted heartbeat coverage execution)
integration: 1/2 (registry fragment installed; process adapter pending)
goal_activation: 45%
```
