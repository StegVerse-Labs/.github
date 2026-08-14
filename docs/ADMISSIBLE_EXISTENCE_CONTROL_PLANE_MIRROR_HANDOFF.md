# Admissible-Existence Control-Plane Mirror Handoff

Updated: 2026-08-14T15:34:00-05:00

## Authority and state

```text
goal_id: ADMISSIBLE-EXISTENCE-CONTROL-PLANE-CONFORMANCE-001
reconciliation_issue: StegVerse-Labs/.github#129
repository: StegVerse-Labs/.github
branch: reconcile/ae-stegcore-conformance-129
state: ACTIVE_VALIDATION_RECONCILIATION
canonical_owner: StegVerse-Labs organization control plane
formalism_authority: Admissible-Existence/AE
canonical_runtime_authority: StegVerse-Labs/StegCore / stegcore.steggate.evaluate_admissibility
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

This is the canonical **cross-repository** procedure for verifying that executable HANDOFF records and the organization Worker Task Registry conform to the current StegCore Admissible-Existence capability lifecycle. It does not create a parallel policy evaluator or execution authority.

StegCore separately owns the **repository-local** lifecycle, capability registry, and repository-local handoff/task-conformance procedure. The two verification surfaces are explicitly noncompeting:

```text
StegVerse-Labs/StegCore
  docs/AE_HANDOFF_TASK_CONFORMANCE_MIRROR_HANDOFF.md
  ecosystem_management/ae_task_conformance.v1.json
  tools/verify_ae_handoff_task_conformance.py

StegVerse-Labs/.github
  docs/ADMISSIBLE_EXISTENCE_CONTROL_PLANE_MIRROR_HANDOFF.md
  control/admissible-existence-control-plane-policy.json
  scripts/validate_admissible_existence_control_plane.py
```

## Canonical StegCore bindings

```text
capability lifecycle origin merge: 7d94908be562f9f9ace05877d4507dc68c984e06
capability registry origin merge: c63b4cce408bc8b3a9c33c6417d96d959678ac19
latest registry + task-conformance merge binding: ca484e0786ee4539af06394bc036e6a7624256f8
latest capability-handoff update: dc539b252f764662340acb9dce10597dfe0a66b2
StegCore lifecycle: src/stegcore/admissible_existence.py
StegCore registry: src/stegcore/capability_registry.py
StegCore capability handoff: docs/ADMISSIBLE_EXISTENCE_CAPABILITY_MODEL_MIRROR_HANDOFF.md
StegCore task conformance handoff: docs/AE_HANDOFF_TASK_CONFORMANCE_MIRROR_HANDOFF.md
```

Canonical lifecycle:

```text
DECLARED -> STANDING -> ADMISSIBLE -> ACTIVATED
ACTIVATED -> SUSPENDED | SUPERSEDED | TERMINATED
```

`COMPLETED` task state does not imply `ACTIVATED` capability state. Canonical StegGate ALLOW is necessary but not sufficient. ACTIVATED requires integration evidence and an activation proof; blocked ADMISSIBLE requires a continuation owner; ACTIVATED may not retain unresolved activation blockers.

## Installed control-plane surfaces

```text
control/admissible-existence-control-plane-policy.json
scripts/validate_admissible_existence_control_plane.py
.github/workflows/org-control-plane-validate.yml
receipts/admissible-existence-control-plane/AE-CONTROL-PLANE-VALIDATION-20260814.json
docs/ADMISSIBLE_EXISTENCE_CONTROL_PLANE_MIRROR_HANDOFF.md
```

The workflow runs anonymously with `permissions: {}` and checks `GITHUB_TOKEN` and `GH_TOKEN` are absent before repository fetch. This validator grants no runtime, credential, provider, wallet, custody, route, signing, broadcast, receipt-minting, or continuity authority.

## Canonical verification procedure

The verifier performs all of the following on every organization control-plane validation run:

```text
HANDOFF
- inspect handoffs/*.json where schema=stegverse.executable-handoff/v0.1
- verify task identity and exact Worker Task Registry binding
- enforce TV/TVC credential authority where declared
- reject GitHub-token runtime/production authority

WORKER TASK REGISTRY
- inspect control/worker-registry.json
- inspect control/worker-registry.d/*.json
- use fragment definitions as repository-native overrides of the aggregate snapshot
- bind task_id to exact handoff_ref

ADMISSIBLE-EXISTENCE
- validate explicit lifecycle bindings against StegCore phases/evidence semantics
- never infer ACTIVATED from task/source completion
- require standing evidence for STANDING+
- require admissibility evidence for ADMISSIBLE+
- require integration evidence + activation_proof_ref for ACTIVATED lineage
- reject ACTIVATED with open blockers
- require continuation_owner for blocked ADMISSIBLE
- require credential_authority=TV/TVC and github_token_runtime_authority=false

CURRENT STEGCORE TASK-CONFORMANCE MODEL
- classify newly created governed work as recently_completed, current, or future
- bind work by relationship: develops_capability, integrates_capability, validates_capability, or propagates_capability
- require recently_completed work to retain evidence supporting its claimed phase
- require current work to retain a durable continuation owner
- require future work to declare target_phase and relationship before activation-oriented execution
- require handoff and registry projections to match temporal_class, task_relationship, target_phase, capability_id, capability_version, and phase
- known StegCore capability snapshots may not be represented above or differently from the pinned canonical phase

FUTURE TASKS
- AE policy effective_at: 2026-08-14T17:20:00Z
- StegCore task-conformance effective_at: 2026-08-14T17:28:36Z
- post-AE-policy executable handoffs must carry explicit admissible_existence metadata
- post-task-conformance executable handoffs must additionally carry temporal_class, task_relationship, and target_phase
- the matching Worker Task Registry task must carry the same binding
- new tasks may not silently use legacy projection

RECENT/CURRENT LEGACY RECORDS
- pre-task-conformance records remain immutable provenance rather than being mass-rewritten
- they are classified MIGRATION_REQUIRED until explicitly rebound to the current contract
- historical evidence remains valid evidence
- legacy completion labels cannot create new activation authority or successor activation authority
- explicit migration is permitted and then becomes fully enforced
```

## Explicit binding contract

AE-bound future handoffs and matching registry tasks require:

```json
{
  "admissible_existence": {
    "capability_id": "stegverse:capability:<name>:v1",
    "capability_version": "1.0.0",
    "phase": "ADMISSIBLE",
    "standing_evidence_refs": ["..."],
    "admissibility_evidence_refs": ["..."],
    "integration_evidence_refs": [],
    "activation_proof_ref": null,
    "blockers": ["..."],
    "continuation_owner": "<durable owner>",
    "credential_authority": "TV/TVC",
    "github_token_runtime_authority": false,
    "temporal_class": "current",
    "task_relationship": "integrates_capability",
    "target_phase": "ACTIVATED"
  }
}
```

For ACTIVATED, integration evidence and activation proof are mandatory and blockers must be empty.

## Latest StegCore capability snapshot

The organization policy now explicitly recognizes the newest StegCore registry state:

```text
stegverse:capability:steggate:canonical:v1 -> ACTIVATED
stegverse:capability:sovereign-local-model:v1 -> ADMISSIBLE
stegverse:capability:transaction-discovery:v1 -> ADMISSIBLE
```

Transaction discovery is intentionally not represented as ACTIVATED because consumer/public discovery binding remains unproven under StegCore #83.

The sovereign local model remains source `COMPLETE_RELEASED` while its capability remains ADMISSIBLE until the live same-execution activation evidence defined by its canonical owner exists.

## Current StegFin binding

`STEGFIN-CONTINUITY-CARRIER-007` was explicitly migrated under the earlier AE binding contract in both:

```text
handoffs/STEGFIN-CONTINUITY-CARRIER-007.json
control/worker-registry.d/stegfin-continuity-carrier-007.json
```

It remains valid historical/current AE evidence, but because it predates the stronger StegCore task-conformance cutover it is classified `MIGRATION_REQUIRED` for continuation-authority purposes until its owning worker performs an explicit task-conformance migration. This reconciliation session does not seize that worker-owned task.

Its capability remains:

```text
capability: stegverse:capability:stegfin-base-pretrade:v1
phase: ADMISSIBLE
blocker: WALLET_HANDOFF_READY_NOT_YET_OBSERVED
credential_authority: TV/TVC
github_token_runtime_authority: false
activation_proof_ref: null
```

## Validation evidence

Prior v1.0 validation:

```text
run: 31823853581
job: 94843227958
head: f5f26b8e4181c4c036708f3dfb7a279a6f2141df
conclusion: SUCCESS
```

The v1.1 reconciliation must not be marked complete until the exact PR head and exact merged-main state pass `.github/workflows/org-control-plane-validate.yml`. The resulting run/job/receipt evidence must be recorded here and in issue #129.

## Effect on live execution

This verifier is a structural admission/conformance gate only. It does not replace or compete with current worker ownership.

```text
TVC-CAPABILITY-RUNTIME-002: existing exclusive observer
STEGFIN-CONTINUITY-CARRIER-007: existing machine claim-on-execution
SHWP-STEGFIN-SOVEREIGN-TRADING-001: existing machine-owned-on-admission worker
ECOSYSTEM-CHAT-SOVEREIGN-ACTIVATION: existing resident heartbeat + .github#60 owner
wallet signing/broadcast: USER_ONLY
```

New live receipts must be evaluated against AE semantics before an ACTIVATED claim is accepted. A newly discovered conformance failure is fail-closed and must be reconciled by the owning repository/component rather than being reinterpreted by a chat session.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: ADMISSIBLE-EXISTENCE-CONTROL-PLANE-RECONCILIATION-129
  execution_owner: issue #129 validation/reconciliation lane
  claim_state: CLAIMED_FOR_VALIDATION_RECONCILIATION
  manual_execution_allowed: true
  manual_allowed_role: validation/reconciliation only
  collision_scope: policy/verifier/handoff/reconciliation receipt; no live runtime/provider/wallet authority
  release_condition: exact merged state passes organization control-plane validation and #129 records evidence
  next_executable_action: validate PR, merge if green, validate merged state, release claim
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: CURRENT-LIVE-RUNTIME-AND-TRADING-TASKS
  execution_owner: existing heartbeat/TVC/StegFin workers and claims
  claim_state: MACHINE_OWNED_OR_EXCLUSIVE_VALIDATION
  manual_execution_allowed: false
  manual_allowed_role: observation
  worker_registry_ref: current task-specific handoff/registry records
  collision_scope: live runtime activation, provider operation, trade preparation, wallet action, settlement, custody
  release_condition: task-specific machine-observable receipts
  next_executable_action: canonical workers continue; verifier validates the resulting lifecycle/evidence state
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: AE-CONFORMANCE-AUTHORITY-COLLISION
  execution_owner: StegCore + AE formalism authority + TV/TVC for credential/route semantics
  claim_state: ESCALATED_WHEN_NEEDED
  manual_execution_allowed: false
  manual_allowed_role: NONE
  collision_scope: structural lifecycle/evidence conflicts
  release_condition: canonical owner resolves or supersedes conflicting state
  next_executable_action: fail closed rather than widen authority or infer activation
```

## Completion and archive dependency

The original AE control-plane gate is `COMPLETE_VALIDATED_RELEASED`. Reconciliation #129 is active until exact PR-head and merged-main validation prove v1.1 conforms to the latest StegCore task model. This reconciliation is a distinct support role; it does not make unfinished product capabilities ACTIVATED and does not satisfy the parent trade goal until the required live machine-owned receipts exist.
