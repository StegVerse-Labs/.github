# Fail-Closed Resolution Escalation Mirror Handoff

## Authority

```text
goal_id: FAIL-CLOSED-RESOLUTION-ESCALATION-001
repository: StegVerse-Labs/.github
branch: feat/fail-closed-resolution-task-escalation-v2
canonical_pr: #82
parent_policy: docs/BLOCKER_RESOLUTION_MIRROR_HANDOFF.md
broad_state_invariant: control/active-worker-state-policy.json / #83/#85
policy_file: control/blocker-resolution-policy.json
resolution_core: heartbeat_runtime/engine_v10.py
canonical_compatibility_runtime: heartbeat_runtime/engine_v11.py
blocker_encoder: heartbeat_runtime/blocker_policy.py
canonical_registry: control/worker-registry.json
state: IMPLEMENTED_VALIDATION_REPAIR_ACTIVE
```

## Governing invariant

`FAIL_CLOSED` protects the attempted consequence; it does not terminate pursuit of the governing goal.

If a worker reaches a fail-closed or conditional constraint that would otherwise leave the task `BLOCKED`, its response must carry a resolution contract. The heartbeat converts that condition into a distinct goal-preserving task in the canonical worker registry and releases the original worker claim. The originating task becomes `ACTIVATION_PENDING` while the derived task owns solution work.

A failed resolution task is evidence that its assigned resolution level could not resolve the collision. Unless a same-level retry is explicitly justified by a changed workaround candidate, the runtime escalates:

```text
WORKER
-> REPOSITORY_OWNER
-> COMPONENT_AUTHORITY
-> ECOSYSTEM_GOVERNANCE
-> HUMAN_AUTHORITY
```

If no admitted worker exists at a machine resolution level, lack of an executor is itself treated as a constraint collision and is escalated. If no machine level can legally correct the collision, the final task is `HUMAN_AUTHORITY_REQUIRED` and must preserve the exact unresolved goal/constraints and identify the correction or decision required.

This scoped runtime work is the mechanical extension of the organization-wide active-worker invariant already installed under #83/#85. It does not replace the broad registry-normalization lane and must not duplicate its paths.

## Runtime construction

`heartbeat_runtime/blocker_policy.py` validates blocked response contracts and embeds a deterministic `resolution-contract:v1:*` evidence reference into the worker response. The existing process adapter already carries string evidence references, so the worker does not receive direct task-registry mutation authority.

`heartbeat_runtime/engine_v10.py` provides the resolution mechanics:

1. derive a deterministic `RESOLVE-*` or `ESCALATE-*` task ID;
2. write a generated executable handoff;
3. write a bounded generated cost basis;
4. append the derived task to the canonical runtime registry;
5. release the original worker claim;
6. move the originating task to `ACTIVATION_PENDING`;
7. admit an eligible solution worker through the ordinary fenced heartbeat path;
8. escalate unresolved resolution tasks to higher authority/capability levels;
9. reactivate the originating goal after successful resolution;
10. preserve fail-closed consequence authority throughout.

`heartbeat_runtime/engine_v11.py` is the canonical compatibility runtime. It activates the new behavior for worker responses that actually carry the resolution contract while preserving older lifecycle/orphan-recovery semantics until those legacy states receive a separately admitted migration. This avoids conflating an expiry-recovery condition with a worker-declared `FAIL_CLOSED` or conditional constraint.

The sovereign heartbeat materializer now binds `heartbeat_runtime.engine_v11.HeartbeatRuntime`. GitHub, Render, Cloudflare, or another hosted service does not become production heartbeat authority through this change.

## Constraint contract

Required on every worker-declared `BLOCKED` response:

```text
blocker.dependency_class
blocker.problem_statement
blocker.solution_required=true
blocker.workaround_candidates[]
blocker.next_solution_action
```

Optional but authoritative for solution routing/escalation:

```text
blocker.trigger_type = FAIL_CLOSED | CONDITIONAL_CONSTRAINT | ...
blocker.resolvable_by_current_worker = true | false
blocker.escalation_target
blocker.required_capabilities[]
blocker.completion_evidence[]
blocker.same_level_retry_authorized
blocker.workaround_candidate_changed
```

A worker may never resolve a collision by silently weakening the originating goal, bypassing StegGate, bypassing a safety predicate, manufacturing credential/route authority, or making GitHub tokens production authority.

## Credential and route boundary

```text
GitHub token production authority: NONE
credential/route authority: TV/TVC
resolution task authority effect: NONE beyond its separately admitted bounded task scope
```

## Validation evidence and active repair

Deterministic tests added:

```text
python -m unittest tests.test_fail_closed_resolution_escalation
python -m unittest tests.test_blocker_resolution_policy
```

The first hosted worker-validation attempt proved all four new escalation tests PASS, then exposed compatibility assumptions in legacy lifecycle/materialization tests. Engine v11 and the sovereign materializer were added to resolve those defects without weakening the new invariant.

A later organization-heartbeat validation exposed a stale disposable-state fixture that copied only top-level `handoffs/*.json` while the canonical registry referenced nested generated handoffs. `.github/workflows/org-heartbeat.yml` now recursively copies `handoffs/` and `cost-basis/`; organization-heartbeat run 37 subsequently reached SUCCESS on that repair.

The latest Heartbeat Worker Project run on the pre-convergence merge ref stopped during executable-handoff validation because concurrent `main` work introduced/modified VACC and sovereign-runtime handoffs while this branch was active. Those files are outside PR #82's mutation scope and are now owned by their canonical concurrent workstreams. PR #82 is registered under #83 as the distinct runtime auto-derivation/escalation lane so those concurrent changes must converge before final hosted validation/merge.

## Completion / release condition

Source construction for the fail-closed/conditional worker path is complete. Merge is permitted only after the current PR merge ref includes the latest canonical `main`, executable-handoff validation passes, the full deterministic worker suite passes, and organization-heartbeat validation passes.

After merge, the canonical rule is:

```text
failed consequence -> remains fail closed
unsatisfied governing goal -> active registered resolution task
worker cannot resolve constraint collision -> next capable resolution level
automation cannot legally resolve collision -> HUMAN_AUTHORITY_REQUIRED with exact decision/correction request
```

No unresolved worker-declared fail-closed/conditional condition may terminate as passive `BLOCKED` work.
