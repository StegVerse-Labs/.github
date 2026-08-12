# Repository Heartbeat Federation Mirror Handoff

## Goal

```text
goal_id: REPO-HEARTBEAT-FEDERATION-001
repository: StegVerse-Labs/.github
branch: main
state: ACTIVE_ENROLLMENT_AND_LIVE_COVERAGE
canonical_issue: StegVerse-Labs/.github#81
canonical_task_owner: SHWP-REPO-HEARTBEAT-FEDERATION-001 / single StegVerse heartbeat
credential_authority: TV/TVC
github_token_required: false
```

This layer extends the existing organization-level federation task with repository-level identity, commit/ref/runtime state, freshness, dependency-loss propagation, and fail-closed coverage. It does not create a second heartbeat or per-repository schedulers.

## Authoritative files

- `schemas/repo-heartbeat-manifest.schema.json`
- `control/repo-heartbeat-federation.json`
- `scripts/emit_repo_heartbeat_manifest.py`
- `workers/repo_heartbeat_federation_worker.py`
- `authorizations/SHWP-REPO-HEARTBEAT-FEDERATION-001.json`
- `handoffs/SHWP-REPO-HEARTBEAT-FEDERATION-001.json`
- `control/worker-registry.d/repo-heartbeat-federation-001.json`
- `control/worker-capability-profiles.json#repository-maintenance-v1`
- `control/process-worker-adapters.json#process:repo-heartbeat-federation-v1`
- `cost-basis/worker-runtime/repo-heartbeat-federation.json`
- `tests/test_repo_heartbeat_federation_worker.py`
- `tests/test_emit_repo_heartbeat_manifest.py`

## Initial critical denominator

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

`StegVerse-Labs/StegDB` is preserved as an adjacent denominator candidate. Read its applicable `*_MIRROR_HANDOFF.md` before classification and addition. Passive documentation/research repositories should normally use `REPO_LIVENESS` unless they own runtime/control/service state.

## Contract

Every participant manifest carries repository/org identity, participant class, sequence, emitted/fresh-until timestamps, status, capabilities, dependencies, evidence refs, and authority metadata. CONTROL/RUNTIME/SERVICE participants also require `commit_sha` and `runtime_id`. Optional fields include `ref`, `release_tag`, `handoff_hash`, and `last_success`.

Authority is fixed:

```text
credential_authority: TV/TVC
heartbeat_grants_execution_authority: false
github_token_required: false
```

The reusable emitter derives commit/ref/tag from a locally materialized repository and can hash an explicitly selected handoff. It does not schedule itself, fetch source, or contact GitHub.

## Fail-closed topology

The central worker builds an inspectable topology and SHA-256 topology hash. A required repository fails coverage when its manifest is missing, stale, invalid, FAILED, BLOCKED, RETIRED, or has lost a required dependency. Required dependency loss propagates to dependent status. The worker writes only `receipts/repo-heartbeat-federation/**` and grants no cross-repository mutation, execution, credential, deployment, or policy authority.

## Installed source evidence

```text
schema: 0a02c9a3dc32b83c8fce4887390258b0a0921e2f
registry: 49d3bbfebd9f9629addc8220d83a75727b425747
coverage worker: 4a14a416ffc0ed80d4bfa5ad861f35da42de367e
authorization: cc16bcad63ef1b32c9206a6d99afac2118fd6661
handoff: 9bc7d42c7c4ff8d64ba803f1ccbdec42725c0808
cost basis: 410f41df3a97e6707b7e7fabe77c41c3127656cf
capability profile: 66fbb858efd84c3655ef3a3b2cc2b3671a78a733
registry fragment: 19163e09a94c11f5b81ffa5b231b2ee79f98079d
coverage tests: d4c89eb660c6f90801dc9d6f9cb6d3558ad475a5
process adapter: 84a423ec1eca178503fd1110dc63eaa5f62de817
manifest emitter: c8f7c03fa3f47fd6d9cf164e29a3f232d4a920df
emitter tests: fbea12d575c2745d9a2e4d1923ac5fa5a418fa77
canonical issue: #81
handoff owner reconciliation: 0a47987306d436a20e19d6104d03c9ea22cc22bf
```

## Validation

Heartbeat Worker Project run `31610774741` on head `84a423ec1eca178503fd1110dc63eaa5f62de817` completed SUCCESS. It used anonymous checkout with GitHub credential variables absent, compiled runtime/workers/scripts, parsed canonical JSON, validated executable handoffs, and ran 112 deterministic tests PASS, including all five repository-federation worker tests. Its epoch-30 heartbeat execution was explicitly dry-run/nonpersistent, so it validates source integration but is not a live coverage receipt.

The reusable emitter and its two tests were added after that run, so the next deterministic validation cycle must execute them before source validation is fully released.

## Claims

```text
central implementation: SOURCE COMPLETE
source integration: COMPLETE
post-emitter validation: ACTIVE
live coverage execution: MACHINE OWNED / PENDING RESIDENT HEARTBEAT
repo enrollment: ACTIVE under issue #81
collision boundary: do not replace SHWP-ALL-ORG-FEDERATION-001; do not create per-repo schedulers
```

## Exact next tasks

1. Execute post-emitter deterministic validation and inspect the real job/logs.
2. Resident heartbeat admits `SHWP-REPO-HEARTBEAT-FEDERATION-001` and emits the first real fail-closed coverage receipt.
3. Read each participant repository's applicable `*_MIRROR_HANDOFF.md` before mutation and install the smallest manifest/adapter enrollment contract.
4. Read StegDB's applicable handoff and classify/add it through an admitted denominator transition.
5. Expand denominator only after critical coverage semantics are proven.
6. Publish/propagate coverage only after a real receipt exists.

## Completeness

```text
developed_files: 12/12 central source/control/test deliverables
scaffolding_or_stubs: 0
missing_required_central_files: 0
validation: 1/3
integration: 2/2
critical_repo_enrollment: 0/11 proven by live coverage receipt
goal_activation: 55%
archive_ready: false
```
