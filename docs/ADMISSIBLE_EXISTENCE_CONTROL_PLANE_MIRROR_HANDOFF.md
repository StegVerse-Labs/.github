# Admissible-Existence Control-Plane Mirror Handoff

Updated: 2026-08-14T12:22:00-05:00

## Authority and goal

```text
goal_id: ADMISSIBLE-EXISTENCE-CONTROL-PLANE-CONFORMANCE-001
repository: StegVerse-Labs/.github
branch: main
canonical_owner: StegVerse-Labs organization control plane
formalism_authority: Admissible-Existence/AE
canonical_runtime_authority: StegVerse-Labs/StegCore / stegcore.steggate.evaluate_admissibility
canonical_structural_model: StegVerse-Labs/StegCore/src/stegcore/admissible_existence.py
canonical_registry_model: StegVerse-Labs/StegCore/src/stegcore/capability_registry.py
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

This handoff establishes the canonical verification procedure that binds executable HANDOFF records and the Worker Task Registry to the current StegCore Admissible-Existence lifecycle without creating a second policy evaluator or a second execution authority.

## Why this exists

StegCore now distinguishes capability development from capability existence/activation:

```text
DECLARED -> STANDING -> ADMISSIBLE -> ACTIVATED
```

with SUSPENDED, SUPERSEDED and TERMINATED successor semantics. A completed source task does not by itself prove an ACTIVATED capability. ACTIVATED requires explicit integration evidence and activation proof; blocked ADMISSIBLE capability state requires a continuation owner; ACTIVATED may not retain unresolved activation blockers.

The organization control plane therefore must verify both:

1. the executable handoff that defines what may execute, why, under what authority, and what terminal evidence is required; and
2. the Worker Task Registry record that admits/schedules the task and binds it to the exact handoff.

## Canonical installed surfaces

```text
control/admissible-existence-control-plane-policy.json
scripts/validate_admissible_existence_control_plane.py
docs/ADMISSIBLE_EXISTENCE_CONTROL_PLANE_MIRROR_HANDOFF.md
.github/workflows/org-control-plane-validate.yml
```

StegCore source bindings:

```text
capability lifecycle merge: 7d94908be562f9f9ace05877d4507dc68c984e06
capability registry merge: c63b4cce408bc8b3a9c33c6417d96d959678ac19
StegCore handoff: docs/ADMISSIBLE_EXISTENCE_CAPABILITY_MODEL_MIRROR_HANDOFF.md
```

## Canonical verification procedure

Every control-plane validation run executes the AE conformance verifier after the ordinary control-plane and handoff validators.

The verifier performs these checks:

```text
A. HANDOFF discovery
   - inspect handoffs/*.json with schema stegverse.executable-handoff/v0.1
   - verify task identity, canonical authority envelope and exact worker-registry binding
   - preserve TV/TVC credential authority
   - prohibit GitHub-token runtime/production authority

B. Worker Task Registry discovery
   - inspect control/worker-registry.json
   - inspect control/worker-registry.d/*.json
   - bind task_id -> exact handoff_ref
   - treat fragment definitions as the repository-native source when they override the aggregate snapshot

C. Admissible-Existence semantics
   - COMPLETED task state never implies ACTIVATED capability state
   - STANDING requires standing evidence
   - ADMISSIBLE requires standing + admissibility evidence
   - blocked ADMISSIBLE requires continuation_owner
   - ACTIVATED lineage requires integration evidence + activation_proof_ref
   - ACTIVATED may not retain blockers
   - AE metadata cannot grant external execution, receipt minting, credential, signing, broadcast, custody or route authority

D. Future-task gate
   - handoffs created at/after policy effective_at must carry explicit admissible_existence metadata
   - their matching worker-registry task must carry the same capability_id, capability_version and phase
   - future tasks cannot silently fall back to legacy inference

E. Legacy/recent/current projection
   - pre-policy executable handoffs and registry tasks are still scanned for exact handoff/registry binding and authority invariants
   - they are not rewritten solely to satisfy migration mechanics
   - any explicit AE metadata on a legacy/current record is fully validated
   - current activation claims remain what their evidence proves, not what a task state label suggests
```

## Explicit binding contract for future tasks

A post-policy handoff and its matching worker-registry task must carry:

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
    "continuation_owner": "<exact durable owner>",
    "credential_authority": "TV/TVC",
    "github_token_runtime_authority": false
  }
}
```

For `ACTIVATED`, `integration_evidence_refs` and `activation_proof_ref` must be present and `blockers` must be empty.

## Effect on recently completed/current StegFin work

The verification process does not reinterpret source-complete work as activation.

```text
formal sovereign local model/runtime source: COMPLETE_RELEASED
AE capability state: ADMISSIBLE until live same-execution activation proof exists
STEGFIN-SOVEREIGN-CAPSULE-MATERIALIZATION-008: COMPLETE_VALIDATED_RELEASED_SOURCE_SUPPORT
live carrier consumption: not inferred from source completion
TVC-CAPABILITY-RUNTIME-002: exclusive live observer remains canonical
STEGFIN-CONTINUITY-CARRIER-007: machine execution remains gated on exact READY receipt
WALLET_HANDOFF_READY: not inferred until the machine-owned terminal receipt exists
```

This preserves the current trade-readiness path while making its completion/activation claims structurally consistent with StegCore.

## Collision and authority boundary

```text
policy evaluation authority: canonical StegGate only
AE structural verifier: may block conformance; may not widen canonical disposition
credential authority: TV/TVC only
GitHub token runtime authority: NONE
provider secret export: prohibited
wallet signing/broadcast: USER_ONLY where applicable
worker claims/fences: existing registry/runtime owners only
```

No new provider executor, wallet executor, runtime observer, heartbeat, credential route, or continuity receipt authority is created by this verifier.

## Validation command

```text
python scripts/validate_admissible_existence_control_plane.py
```

It is also a mandatory step in `.github/workflows/org-control-plane-validate.yml`.

## Machine-observable success condition

```text
AE_CONTROL_PLANE_VALIDATION_PASS
```

The receipt line includes executable handoff count, worker-registry task count, explicit AE binding count, legacy projection count, and the exact StegCore capability-registry commit used by policy.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: ADMISSIBLE-EXISTENCE-CONTROL-PLANE-CONFORMANCE-001
  execution_owner: organization control-plane validation lane
  claim_state: COMPLETE_SOURCE / VALIDATION_ACTIVE_BY_WORKFLOW
  manual_execution_allowed: true
  manual_allowed_role: validation/reconciliation only
  worker_registry_ref: control/worker-registry.json + control/worker-registry.d/*.json
  collision_scope: conformance policy, verifier, evidence-only reconciliation; no live provider/wallet/runtime authority
  release_condition: canonical validator and workflow gate are installed and pass against repository state
  next_executable_action: run canonical verifier whenever handoff/registry state changes
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
  next_executable_action: existing canonical workers continue; AE verifier only validates resulting state/evidence
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: AE-CONFORMANCE-AUTHORITY-COLLISION
  execution_owner: StegCore + AE formalism authority + TV/TVC for credential/route semantics
  claim_state: ESCALATED_WHEN_NEEDED
  manual_execution_allowed: false
  manual_allowed_role: NONE
  worker_registry_ref: applicable canonical owner records
  collision_scope: conflicts between structural lifecycle claims and canonical authority/evidence
  release_condition: canonical owner resolves or supersedes conflicting state
  next_executable_action: fail closed rather than reinterpret evidence or authority
```

### COMPLETED / SUPERSEDED

```text
The former practice of equating source/task completion with capability activation is superseded.
Pre-policy records remain valid provenance and are verified through legacy projection unless they are explicitly migrated.
```

## Archive condition

This control-plane subgoal is complete only after the policy, verifier, workflow gate and this handoff are committed and the strongest available validation run is inspected. It does not make unfinished product capabilities ACTIVATED and does not authorize archiving a session whose operational goal still lacks its required activation receipt.
