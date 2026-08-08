# Heartbeat Continuity Worker Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `StegVerse-Labs/.github#12`. It is the canonical continuation for the single-heartbeat worker/continuity implementation. `management/SHWP_SESSION_EXECUTION_INVENTORY.json` is the machine-readable session inventory and `management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json` is the durable deployment-blocker receipt.

No separate scheduler, worker heartbeat, conversational trigger, GitHub Actions schedule, cron schedule, Render schedule, or third-party wake service is normative authority for this lane.

## Active goal and claims

```text
goal_id: STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001
originating_session_goal: complete and durably automate unfinished StegVerse work using one internal heartbeat and archive conversation state only after durable transfer
repository: StegVerse-Labs/.github
branch: main
canonical_owner: issue #12
implementation_claim: RELEASED — all protocol/read-layer child implementation issues complete
validation_claim: RELEASED — full control-plane hosted validation complete
claim_creation_time: historical implementation lane consolidated into #12
claim_release_condition: satisfied by run 31242995304 / job 93066913610 SUCCESS
collision_boundary: one heartbeat only; no duplicate scheduler, epoch owner, Audit Kit lane, StegCore lane, or completed child reactivation
session_state: BLOCKED_ON_DURABLE_RUNTIME_ACTIVATION_ONLY
```

## Canonical implementation

`heartbeat_runtime.engine_v8.HeartbeatRuntime` is the production-selected runtime through `heartbeat_runtime/__init__.py` at commit `11c1b801af35c94d3d67c398a7c93b2fed776448`.

Runtime layering preserves previously proven semantics:

- v2: activation, claim/fence, expiry and missing-Master-Records-final-report recovery;
- v3: one-HB organization assertions, renewal and orphan recovery;
- v4: BLOCKED recheck and human-authority separation;
- v5: bounded goal lineage, duplicate control and successor narrowing/expansion admission;
- v6: persistent resource/runtime/service/cost authority;
- v7/v7.1: policy continuity and canonical checkpoint envelope with worker/Master Records checkpoint preservation;
- v8: canonical worker capability-profile enforcement.

Additional canonical read/control surfaces:

- `scripts/project_heartbeat_workers.py` -> fail-closed `control/worker-status.json` v0.3;
- `scripts/query_worker_status.py` -> deterministic observational task/goal/state query;
- `scripts/evaluate_goal_convergence.py` -> deterministic `control/goal-convergence.json` no-work projection;
- `heartbeat_runtime/process_adapter.py` -> sandboxed fenced authoritative mutation boundary.

## One-heartbeat invariant

Every active worker answers the same heartbeat with relative transition state. That same epoch sequence is the timing frame for progress, response-loss thresholds, resource/runtime limits and expiry. No other heartbeat or scheduler clock exists in the protocol.

The heartbeat carries coordination information among registry/HANDOFF, workers, policy/resource/capability state, canonical checkpoints, Master Records evidence, failure/recovery signals, read projections, goal convergence and successor state. Carriage does not imply authority.

## Completed protocol/read capabilities

All SHWP child implementation work is COMPLETE:

```text
empty registry -> no worker                          COMPLETE
authorized eligible work -> exactly one worker       COMPLETE
atomic checkout / claim / fence                      COMPLETE
real bounded process executor                        COMPLETE
activation request != execution authority            COMPLETE
executor ambiguity refusal                           COMPLETE
BLOCKED machine recheck                              COMPLETE
HUMAN_AUTHORITY_REQUIRED boundary                    COMPLETE
same-HB renewal / orphan recovery                    COMPLETE
MR final-report-missing reconciliation               COMPLETE
successor reconstruction / higher fence              COMPLETE
bounded goals / lineage / successor depth            COMPLETE
separate authority expansion admission               COMPLETE
duplicate canonical lane quarantine                  COMPLETE
sandbox mutation scope / fence                       COMPLETE
persistent action/retry/runtime/service/cost bounds  COMPLETE
policy drift stop / separate rebind                  COMPLETE
canonical control-plane checkpoint + hash            COMPLETE
worker/MR checkpoint preservation                    COMPLETE
canonical checkpoint tamper refusal                  COMPLETE
worker capability profiles / effect classes          COMPLETE
profile/capability match != authorization            COMPLETE
fail-closed status/archive projection                COMPLETE
canonical observational read/query surface           COMPLETE
deterministic goal convergence/no-work condition     COMPLETE
```

Final live consistency checking surfaced four previously open children that earlier handoff text had omitted: #45, #47, #49 and #53. They were implemented, hosted-validated and closed complete. They are not future work.

## Validation evidence

### Canonical v8 promotion

```text
workflow: Heartbeat Worker Project
run: 31242636078
job: 93066031288
head: 11c1b801af35c94d3d67c398a7c93b2fed776448
result: SUCCESS
```

This is the canonical production-selected runtime proof.

### Final full control-plane validation

```text
workflow: Heartbeat Worker Project
run: 31242995304
job: 93066913610
result: SUCCESS
```

The final hosted path directly passed:

- runtime/projector compilation including v7.1/v8;
- canonical JSON parsing;
- executable HANDOFF validation;
- core one-HB runtime semantics;
- ambiguity-safe executor discovery;
- BLOCKED/human authority boundaries;
- goal lineage/duplicate/successor controls;
- bounded resource authority;
- policy continuity + canonical checkpoint/tamper controls;
- capability-profile matching;
- fail-closed status, observational query and convergence tests;
- sandboxed mutation scope/fence;
- one-HB renewal/orphan recovery;
- cost basis/no-guess behavior;
- dry-run nonmutation;
- worker-status, convergence and continuity projection refresh;
- observational query smoke;
- current StegGate successor blocked/unclaimed and Audit Kit nonconverged posture.

## Fail-closed status / query contract

`control/worker-status.json` is `stegverse.heartbeat-worker-status/v0.3` and states:

```text
query_is_observational: true
execution_authority_from_heartbeat: false
```

Any structural or authority validation error forces `archive_eligible=false`. Missing/ambiguous executor, unresolved authority, missing checkpoint for worker-owned work, invalid fence/timing, missing HANDOFF, missing Master Records custody and unresolved successor reconstruction all remain non-archivable.

`scripts/query_worker_status.py` is observational only and returns deterministic task/goal/state views containing lifecycle state, archive posture/reasons, worker/claim/fence, last checkpoint, next authorized action and evidence refs. It cannot trigger work or grant authority.

## Goal convergence / no-work contract

Canonical surface: `control/goal-convergence.json`, schema `stegverse.goal-convergence/v0.1`.

A root goal is converged only when:

1. the authoritative root task is `COMPLETED`;
2. no unresolved descendant remains;
3. no active claim/worker remains in the goal family;
4. required custody/reconstruction is complete;
5. no separately authorized remaining action exists.

Current `STEGGATE-AUDITKIT-001` convergence is **false** despite its root being completed because `STEGGATE-FIRST-BOUNDARY-001` is an unresolved blocked descendant and its required custody/reconstruction is not complete. This prevents false terminal closure or perpetual autonomous successor generation.

## Canonical checkpoint contract

After every accepted worker response the control plane writes `stegverse.worker-checkpoint/v0.1` to `checkpoints/workers/**` and makes that the task `last_checkpoint_ref`.

It binds task/goal, worker/instance, claim/fence, heartbeat epoch, state/transitions, unresolved work, evidence refs, next authorized action, authorized policy version and authority source, HANDOFF ref/hash, nested worker/Master Records checkpoint ref when supplied, resource budget, `execution_authority=false`, and canonical SHA-256.

Successor reconstruction verifies hash/fence/policy and rejects a mutated canonical checkpoint. Worker/Master Records checkpoint evidence is preserved and is not confused with control-plane execution authority.

## Policy continuity

Initial authorized checkout binds the HANDOFF policy version. If live policy changes while a claim remains active, invocation stops in `EXPIRING` with `POLICY_REBIND_REQUIRED`. A separate `stegverse.worker-policy-rebind/v0.1` admission must bind task, claim, fence, old/new policy, current HANDOFF hash and authority source. Heartbeat cannot approve policy expansion/change.

## Capability profiles

Canonical registry: `control/worker-capability-profiles.json`.

```text
deterministic-workflow-v1
repository-maintenance-v1
code-change-agent-v1
deployment-worker-v1
read-only-observer-v1
```

Selection verifies profile existence, executor type, allowed capability subset, task-required capabilities, mutation/deployment effect permission and exactly-one-match ambiguity. Every profile explicitly declares availability and capability matching non-authoritative.

## Resource authority

HANDOFF execution binds action, retry, HB-relative runtime, rate class, allowed service and external-cost ceilings. Runtime v8 persists usage in `resource_budget`; worker responses do not reset counters. Exhaustion cannot silently continue. Separate renewal may extend admitted bounds; unadmitted service use or cost ceiling violation fails closed.

## Recovery and remediation

Known expiry plus missing required Master Records final worker report creates exactly one deduplicated lifecycle-reconciliation task. The old worker is released and not resurrected. Same-HB response loss crosses an admitted threshold before orphan recovery; recovery requires reconstruction and a higher fence.

Lifecycle discrepancies can create investigation work. Candidate remedies can be sandbox-tested. Sandbox evidence grants no execution authority; validated/admissible remediation returns through normal registry/claim/fence/checkpoint/final-report lifecycle.

## StegGate / StegCore truth

```text
STEGGATE-AUDITKIT-001: COMPLETED / archive eligible / NEVER REACTIVATE
STEGGATE-FIRST-BOUNDARY-001: BLOCKED / UNCLAIMED / non-archivable
first-boundary release: durable target + authority model + ara activation READY + validator PASS
StegCore#54: COMPLETE / RELEASED; no duplicate runtime work
```

## Current registry / collision state

No active SHWP protocol/read implementation claim exists. The only nonterminal named StegGate task is intentionally BLOCKED and unclaimed. Historical ChatGPT/bootstrap worker is DISABLED. The bounded native process canary is AVAILABLE but unclaimed.

## Remaining exact work: parent #12 durable activation

There is no remaining SHWP child implementation work. The sole unfinished task is the durable runtime activation boundary:

```text
task_id: SHWP-DURABLE-RUNTIME-ACTIVATION
owner: StegVerse-Labs/.github#12
claim_state: BLOCKED
state: BLOCKED_RUNTIME_ACTIVATION
blocker_receipt: management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json
surface: scripts/run_heartbeat_runtime.py --continuous
```

Connected Render inspection proved the current blocker rather than assuming it:

- no existing correctly owned `.github` service is suitable;
- `stegverse-hil-receiver` has persistent disk but belongs to `StegVerse-org/LLM-adapter`;
- `scw-worker` is a background worker but belongs to `StegVerse-Labs/StegVerse-SCW`;
- existing persistent KV stores belong to named SCW/TVC subsystem state;
- no Postgres instance exists;
- direct connected creation exposes web service creation without persistent-disk configuration and no background-worker creation action.

No stateless substitute, cross-subsystem appropriation, paid resource, provider-specific unproven state adapter, ChatGPT monitor, or external scheduler was created.

Release condition:

```text
1. long-lived replaceable host correctly owned by .github control plane
2. heartbeat/registry/event/cost/receipt/checkpoint state durably writable across restart/deploy
3. host runs scripts/run_heartbeat_runtime.py --continuous
4. runtime controls cadence; host supplies process liveness only
5. restart preserves/increments one epoch lineage without duplicate claim/fence
6. no ChatGPT automation, GitHub cron, Render cron or external scheduler owns activation
```

Next executable action is machine-observable: reinspect connected deployment controls when a correctly owned durable process-host capability or already-admitted provider-neutral durable host becomes available; then deploy v8 and execute restart proof.

## Machine-owned tasks

None are active for the deployment blocker. GitHub Actions remains validation-only. No ChatGPT monitoring is active in this session.

## Cross-repository dependencies / propagation

- `master-records/orchestration`: lifecycle custody/reconstruction evidence owner.
- `ara-admissibility-interop`: owns first real StegGate boundary when its blocker clears.
- `StegCore`: #54 complete; no active duplicate dependency.
- Site/Publisher/admissibility-wiki/stegguardian-wiki: no propagation obligation was established merely by SHWP runtime/read-layer completion.

## Validation commands

```bash
python scripts/validate_executable_handoffs.py
python -m unittest -v tests.test_heartbeat_runtime
python -m unittest -v tests.test_executor_discovery
python -m unittest -v tests.test_block_boundaries
python -m unittest -v tests.test_goal_lineage
python -m unittest -v tests.test_resource_authority
python -m unittest -v tests.test_checkpoint_policy
python -m unittest -v tests.test_capability_profiles
python -m unittest -v tests.test_status_failclosed_convergence
python -m unittest -v tests.test_process_adapter_scope
python -m unittest -v tests.test_lifecycle_authority
python -m unittest -v tests.test_worker_cost_basis_estimator
python scripts/project_heartbeat_workers.py --write
python scripts/evaluate_goal_convergence.py --write
python scripts/query_worker_status.py --state BLOCKED
python scripts/run_heartbeat_runtime.py --dry-run --cycles 1
```

## Integration / propagation obligations

Runtime v8 and the read/convergence layer are integrated into the canonical package/projection/validation paths. No deployment, public release, Site/Publisher publication or wiki propagation is implied by protocol completion.

## Session consolidation

```text
merged_into: StegVerse-Labs/.github#12 + docs/ORG_MIRROR_HANDOFF.md + this handoff + management/SHWP_SESSION_EXECUTION_INVENTORY.json + management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json
unique_protocol_or_read_information_remaining_only_in_chat: NONE
protocol_or_read_implementation_claims_remaining: NONE
runtime_activation_unique_information_remaining_only_in_chat: NONE — blocker/evidence/release predicates are durable
thread_archive_ready: false under governing archive invariant because unfinished activation has no active non-conversational executor/observer and is not at a human-authority terminal boundary
```

## Completion assessment

```text
protocol/read-layer tasks: 22/22 = 100%
developed required protocol/read files: 47/47 = 100%
scaffolding/stubs: 0
validation: 25/25 = 100%
protocol/read integration: 27/27 = 100%
goal activation including durable host: 27/28 = 96%
session consolidation: 18/19 = 95%
```
