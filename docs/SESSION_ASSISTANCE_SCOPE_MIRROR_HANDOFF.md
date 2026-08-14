# Session Assistance Scope Mirror Handoff

Updated: 2026-08-14T16:58:00-05:00

## Authority and goal

```text
goal_id: SESSION-GOAL-SCOPED-WORKER-ASSISTANCE-001
repository: StegVerse-Labs/.github
branch: main
canonical_issue: #143
implementation_tracker: #146
canonical_owner: StegVerse-Labs organization control plane
credential_authority: TV/TVC
github_token_runtime_authority: NONE
execution_authority_created: NONE
```

This handoff is authoritative for deciding whether an interactive session may assist a worker/task. It does not create worker execution authority, alter StegCore Admissible-Existence semantics, widen StegGate disposition, or mutate runtime/provider/wallet authority.

## Canonical rule

`assist workers` means: assist workers already owning or supporting an established originating goal of the current session, or a direct durable dependency, validation, integration, or propagation descendant of such a goal.

A shared/global boilerplate directive cannot become a new originating session goal without independent session-history lineage evidence. A globally visible unresolved task is not eligible merely because it is urgent, HANDOFF_READY, blocked, or machine-owned.

Worker-assistance selection therefore follows:

```text
SESSION ORIGINATING GOALS
-> durable goal IDs
-> direct owner/dependency/validation/integration/propagation lineage
-> eligible workers/tasks
-> collision check
-> assist or transfer
```

It must not follow:

```text
ALL WORKERS
-> most actionable/global blocker
-> session adopts unrelated task
```

## Current corrected session inventory

Canonical inventory:

```text
control/session-goal-inventory-2026-08-14-admissible-existence-core-local-runtime-v3.json
```

The prior v2/v3 trajectory incorrectly promoted `make this trade ready` into the AE/Core/local-runtime session. Under the clarified session-scope rule, StegFin trade readiness is recorded as `OUT_OF_SCOPE_SHARED_DIRECTIVE`, is not an archive dependency, and remains owned by `StegVerse-Labs/stegfin-governance` plus its registered workers.

The in-scope worker families for this session are limited to the durable goal lineage for:

- StegCore Admissible-Existence design/conformance;
- HANDOFF/Worker Task Registry AE verification;
- sovereign local-runtime discovery/launch/inference/proof;
- formal local-model development;
- TV/TVC-only credential/runtime authority boundaries required by those goals;
- session consolidation and session-scope enforcement.

## Installed enforcement

```text
control/session-assistance-scope-policy.json
scripts/validate_session_assistance_scope.py
tests/test_session_assistance_scope.py
control/session-goal-inventory-2026-08-14-admissible-existence-core-local-runtime-v3.json
.github/workflows/org-continuation-check.yml
```

The validator fails when a v3 session inventory:

- omits the required session-scope fields;
- permits a shared directive to create an originating goal;
- marks an out-of-scope directive/task as an archive dependency;
- claims `IN_SCOPE_ASSIST` for a worker whose `session_goal_id` is not in the session originating goal set;
- lacks lineage evidence for an in-scope worker;
- promotes a `SHARED_DIRECTIVE_ONLY` goal into active session scope.

## Collision boundaries

```text
live worker claims/fences/leases: NO MUTATION
runtime activation: NO AUTHORITY
provider operation: NO AUTHORITY
wallet signing/broadcast: NO AUTHORITY
StegCore AE lifecycle: UNCHANGED
StegGate disposition: UNCHANGED
TV/TVC credential authority: PRESERVED
GitHub token runtime authority: NONE
```

## Validation

Required commands:

```text
python3 scripts/validate_session_assistance_scope.py
python3 -m unittest tests.test_session_assistance_scope -v
```

Hosted canonical invocation is `Org Continuation Check - No GitHub Token Authority` after the workflow update. The workflow remains `permissions: {}` and performs anonymous checkout without GitHub credential authority.

## Completion/archival rule

The scope-routing defect is complete only when the exact main-head validator and tests pass under the no-token organization workflow and issues #143/#146 are closed/released with evidence. Until then this session retains a unique implementation/validation role.
