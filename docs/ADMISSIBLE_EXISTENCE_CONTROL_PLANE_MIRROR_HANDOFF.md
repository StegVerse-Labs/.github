# Admissible-Existence Control-Plane Mirror Handoff

Updated: 2026-08-14T12:25:00-05:00

## Authority and state

```text
goal_id: ADMISSIBLE-EXISTENCE-CONTROL-PLANE-CONFORMANCE-001
repository: StegVerse-Labs/.github
branch: main
state: COMPLETE_VALIDATED_RELEASED
canonical_owner: StegVerse-Labs organization control plane
formalism_authority: Admissible-Existence/AE
canonical_runtime_authority: StegVerse-Labs/StegCore / stegcore.steggate.evaluate_admissibility
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

This is the canonical procedure for verifying that executable HANDOFF records and the Worker Task Registry conform to the current StegCore Admissible-Existence capability lifecycle without creating a parallel policy evaluator or execution authority.

## Canonical StegCore bindings

```text
capability lifecycle merge: 7d94908be562f9f9ace05877d4507dc68c984e06
capability registry merge: c63b4cce408bc8b3a9c33c6417d96d959678ac19
StegCore lifecycle: src/stegcore/admissible_existence.py
StegCore registry: src/stegcore/capability_registry.py
StegCore handoff: docs/ADMISSIBLE_EXISTENCE_CAPABILITY_MODEL_MIRROR_HANDOFF.md
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

FUTURE TASKS
- policy effective_at: 2026-08-14T17:20:00Z
- post-policy executable handoffs must carry explicit admissible_existence metadata
- the matching Worker Task Registry task must carry the same capability_id, capability_version and phase
- new tasks may not silently use legacy projection

RECENT/CURRENT LEGACY RECORDS
- pre-policy records remain immutable provenance rather than being mass-rewritten
- they are still checked for exact handoff/registry binding and authority invariants
- any explicit AE metadata is fully validated
- explicit migration is permitted and then becomes fully enforced
```

## Explicit binding contract

Future handoffs and matching registry tasks require:

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
    "github_token_runtime_authority": false
  }
}
```

For ACTIVATED, integration evidence and activation proof are mandatory and blockers must be empty.

## Current StegFin binding

`STEGFIN-CONTINUITY-CARRIER-007` has been explicitly migrated in both:

```text
handoffs/STEGFIN-CONTINUITY-CARRIER-007.json
control/worker-registry.d/stegfin-continuity-carrier-007.json
```

It is represented as:

```text
capability: stegverse:capability:stegfin-base-pretrade:v1
phase: ADMISSIBLE
blocker: WALLET_HANDOFF_READY_NOT_YET_OBSERVED
continuation_owner: stegfin-continuity-carrier-worker + TV/TVC runtime authority/observer as selected at execution
credential_authority: TV/TVC
github_token_runtime_authority: false
activation_proof_ref: null
```

This deliberately prevents the machine-ready source path from being represented as live ACTIVATED before `WALLET_HANDOFF_READY` evidence exists.

The sovereign local model remains source `COMPLETE_RELEASED` while its StegCore capability remains ADMISSIBLE until the live same-execution activation evidence defined by its canonical owner exists.

## Validation evidence

Canonical workflow:

```text
run: 31823853581
job: 94843227958
head: f5f26b8e4181c4c036708f3dfb7a279a6f2141df
conclusion: SUCCESS
```

Observed validator output:

```text
AE_CONTROL_PLANE_VALIDATION_PASS
handoffs=24
registry_tasks=25
explicit_bindings=1
legacy_projections=23
stegcore_registry_commit=c63b4cce408bc8b3a9c33c6417d96d959678ac19
```

The same job also passed organization control-plane invariants, active-worker ownership, handoff execution ownership, cross-repository dependency collision tests, JSON/JSONL validation, and the no-authority workflow check.

Durable receipt:

```text
receipts/admissible-existence-control-plane/AE-CONTROL-PLANE-VALIDATION-20260814.json
```

## Effect on live execution

This verifier is a structural admission/conformance gate only. It does not replace or compete with current worker ownership.

```text
TVC-CAPABILITY-RUNTIME-002: existing exclusive observer
STEGFIN-CONTINUITY-CARRIER-007: existing machine claim-on-execution
SHWP-STEGFIN-SOVEREIGN-TRADING-001: existing machine-owned-on-admission worker
wallet signing/broadcast: USER_ONLY
```

New live receipts must be evaluated against AE semantics before an ACTIVATED claim is accepted. A newly discovered conformance failure is fail-closed and must be reconciled by the owning repository/component rather than being reinterpreted by a chat session.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: ADMISSIBLE-EXISTENCE-CONTROL-PLANE-CONFORMANCE-001
  execution_owner: organization control-plane validation lane
  claim_state: COMPLETE_VALIDATED_RELEASED
  manual_execution_allowed: true
  manual_allowed_role: validation/reconciliation only
  worker_registry_ref: control/worker-registry.json + control/worker-registry.d/*.json
  collision_scope: conformance policy/verifier/evidence only; no live runtime/provider/wallet authority
  release_condition: validator remains green against canonical StegCore binding
  next_executable_action: rerun automatically whenever handoff/registry/control-plane state changes
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
  worker_registry_ref: applicable canonical owner records
  collision_scope: structural lifecycle/evidence conflicts
  release_condition: canonical owner resolves or supersedes conflicting state
  next_executable_action: fail closed rather than widen authority or infer activation
```

### COMPLETED / SUPERSEDED

```text
Source/task completion => capability activation inference is superseded.
Future unbound AE lifecycle records are rejected by the organization validation gate.
```

## Completion and archive dependency

This conformance subgoal is `COMPLETE_VALIDATED_RELEASED`. It remains a permanent automated control-plane gate. It does not make unfinished product capabilities ACTIVATED and does not satisfy the parent trade goal until the required live trade-ready receipt exists.
