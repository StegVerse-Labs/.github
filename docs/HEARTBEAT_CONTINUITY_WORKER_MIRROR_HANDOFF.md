# Heartbeat Continuity Worker Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `StegVerse-Labs/.github#12`. It is the canonical continuation for the single-heartbeat worker/continuity implementation. `management/SHWP_SESSION_EXECUTION_INVENTORY.json` is the machine-readable session inventory.

No separate scheduler, worker heartbeat, conversational trigger, GitHub Actions schedule, cron schedule, Render schedule, or third-party wake service is normative authority for this lane.

## Active goal and claims

```text
goal_id: STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001
originating_session_goal: complete and durably automate unfinished StegVerse work using one internal heartbeat and archive conversation state only after durable transfer
repository: StegVerse-Labs/.github
branch: main
canonical_owner: issue #12
implementation_claim: RELEASED — all protocol child implementation issues complete
validation_claim: RELEASED — promoted runtime v8 hosted validation complete
claim_creation_time: historical implementation lane consolidated into #12
claim_release_condition: satisfied by promoted v8 run 31242636078 / job 93066031288 SUCCESS
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

`process_adapter.py` remains the sandboxed fenced authoritative mutation boundary.

## One-heartbeat invariant

Every active worker answers the same heartbeat with relative transition state. That same epoch sequence is the timing frame for progress, response-loss thresholds, resource/runtime limits and expiry. No other heartbeat or scheduler clock exists in the protocol.

The heartbeat carries coordination information among registry/HANDOFF, workers, policy/resource/capability state, checkpoints, Master Records evidence, failure/recovery signals and successor state. Carriage does not imply authority.

## Completed protocol capabilities

All protocol child implementation work is COMPLETE:

```text
empty registry -> no worker                         COMPLETE
authorized eligible work -> exactly one worker      COMPLETE
atomic checkout / claim / fence                     COMPLETE
real bounded process executor                       COMPLETE
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
profile/capability match != authorization             COMPLETE
```

Issue #40, #41 and #44 were closed complete after promoted v8 validation. #21, #19, #20, #32, #39, #43, #48 and earlier implementation children are likewise complete and must not be reopened as parallel architecture workstreams.

## Promoted validation evidence

```text
workflow: Heartbeat Worker Project
run: 31242636078
job: 93066031288
head: 11c1b801af35c94d3d67c398a7c93b2fed776448
result: SUCCESS
```

Substantive hosted steps all passed:

- runtime/projector compilation including v7.1/v8;
- all canonical JSON surfaces parse;
- executable HANDOFF goal/resource validation;
- core one-HB runtime semantics;
- ambiguity-safe executor discovery;
- BLOCKED/human authority boundaries;
- goal lineage/duplicate/successor controls;
- bounded resource authority;
- policy continuity + canonical checkpoints;
- capability profiles;
- sandboxed mutation scope/fence;
- one-HB renewal/orphan recovery;
- cost-basis and no-guess behavior;
- dry-run nonmutation;
- worker/continuity projection;
- StegGate successor blocked/unclaimed posture.

## Canonical checkpoint contract

After every accepted worker response the control plane writes `stegverse.worker-checkpoint/v0.1` to `checkpoints/workers/**` and makes that the task `last_checkpoint_ref`.

It binds:

- task and goal;
- worker and worker instance;
- claim and fencing token;
- heartbeat epoch;
- current state and completed transitions;
- unresolved work;
- evidence refs;
- next authorized action;
- authorized policy version and authority source;
- HANDOFF ref/hash;
- nested worker/Master Records checkpoint ref, when supplied;
- resource budget;
- `execution_authority=false`;
- canonical SHA-256.

Successor reconstruction verifies hash/fence/policy and rejects a mutated canonical checkpoint. Worker/Master Records checkpoint evidence is not overwritten or confused with control-plane reconstruction authority.

## Policy continuity

Initial authorized checkout binds the HANDOFF policy version. If the live HANDOFF policy changes while a claim remains active, invocation stops in `EXPIRING` with `POLICY_REBIND_REQUIRED`. The heartbeat cannot approve the change. A separate `stegverse.worker-policy-rebind/v0.1` admission must bind task, claim, fence, old/new policy, current HANDOFF hash and authority source before execution resumes.

## Capability profiles

Canonical registry: `control/worker-capability-profiles.json`.

Profiles:

```text
deterministic-workflow-v1
repository-maintenance-v1
code-change-agent-v1
deployment-worker-v1
read-only-observer-v1
```

Registered workers name `capability_profile_ref`. Selection verifies profile existence, executor type, allowed capability subset, task required capabilities, mutation/deployment effect permission and exactly-one-match ambiguity. Every profile explicitly declares availability and capability matching non-authoritative.

## Resource authority

HANDOFF execution binds action, retry, HB-relative runtime, rate, allowed service and external-cost ceilings. Runtime v8 persists usage in `resource_budget`; worker responses do not reset counters. Exhaustion cannot silently continue. Separate renewal may extend admitted bounds; unadmitted service use or cost ceiling violation fails closed.

## Recovery and remediation

Known expiry plus missing required Master Records final worker report creates exactly one deduplicated lifecycle-reconciliation task. The old worker is released and not resurrected. Same-HB response loss crosses an admitted threshold before orphan recovery; recovery requires reconstruction and a higher fence.

Lifecycle discrepancies can create investigation work. Candidate remedies can be sandbox-tested. Sandbox evidence grants no execution authority; validated/admissible remediation returns through normal registry/claim/fence/checkpoint/final-report lifecycle.

## StegGate / StegCore continuation truth

```text
STEGGATE-AUDITKIT-001: COMPLETED; never reactivate
STEGGATE-FIRST-BOUNDARY-001: BLOCKED / UNCLAIMED
first-boundary release: durable target + authority model + ara activation READY + validator PASS
StegCore#54: COMPLETE / RELEASED; no duplicate runtime work
```

## Current registry / collision state

No active SHWP protocol implementation claim exists. The only nonterminal named StegGate task is intentionally BLOCKED and unclaimed. The historical ChatGPT/bootstrap worker is DISABLED. The bounded native process canary is AVAILABLE but has no current claim.

## Remaining exact work: parent #12 durable activation

There is no remaining protocol child implementation work. The sole unfinished goal is activating the validated v8 runtime on a correctly owned long-lived durable state host.

```text
task_id: STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001-RUNTIME-ACTIVATION
owner: StegVerse-Labs/.github#12
claim_state: BLOCKED
state: BLOCKED_RUNTIME_ACTIVATION
surface: scripts/run_heartbeat_runtime.py --continuous
release_condition:
  1. long-lived replaceable host is correctly owned by .github control plane;
  2. heartbeat/registry/event/cost/receipt/checkpoint state is durably writable and survives restart/deploy;
  3. host runs the continuous entrypoint;
  4. runtime controls internal cadence; host supplies process liveness only;
  5. restart proof preserves/increments one epoch lineage without duplicate claim/fence;
  6. no ChatGPT automation, GitHub cron, Render cron, or external scheduler owns worker activation.
next_action: inspect connected deployment controls and activate only if every predicate is satisfiable.
```

This blocker is not permission to move the control-plane runtime into a service owned by another StegVerse subsystem or to use stateless storage.

## Machine-owned tasks

None are currently active for the deployment blocker. GitHub Actions is validation-only and is not a machine execution lane for continuous scheduling. No ChatGPT monitoring is active in this session.

## Cross-repository dependencies

- `master-records/orchestration`: lifecycle custody/reconstruction evidence owner.
- `ara-admissibility-interop`: owns first real StegGate boundary release when its blocker clears.
- `StegCore`: #54 complete; no active dependency requiring duplicate work here.

No Site/Publisher/wiki publication obligation was established by v8 runtime implementation itself.

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
python -m unittest -v tests.test_process_adapter_scope
python -m unittest -v tests.test_lifecycle_authority
python -m unittest -v tests.test_worker_cost_basis_estimator
python scripts/run_heartbeat_runtime.py --dry-run --cycles 1
```

## Integration / propagation obligations

Runtime v8 is integrated into the canonical package import and validation workflow. Protocol changes do not imply deployment, public release, Site/Publisher publication, or wiki propagation. Such actions require their own live authority/contracts.

## Session consolidation

```text
merged_into: StegVerse-Labs/.github#12 + this handoff + ORG_MIRROR_HANDOFF.md + management/SHWP_SESSION_EXECUTION_INVENTORY.json
protocol_unique_information_remaining_only_in_chat: NONE
protocol_implementation_claims_remaining: NONE
runtime_activation_unique_information_remaining_only_in_chat: NONE — blocker and predicates are durable
thread_archive_ready: false until deployment blocker is dispositioned under governing archive rule
```

## Completion assessment

```text
protocol task completion: 18/18 = 100%
developed protocol files: 43/43 = 100%
scaffolding/stubs: 0
validation: 24/24 = 100%
protocol integration: 23/23 = 100%
goal activation including durable host: 23/24 = 96%
session consolidation: 17/18 = 94%
```
