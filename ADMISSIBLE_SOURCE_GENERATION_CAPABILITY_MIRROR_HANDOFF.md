# Admissible Source-Generation Capability Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs
repository: .github
branch: feat/admissible-source-generation-capability-137
goal_id: ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-ACTIVATION-001
issue: #137
parent_goal: FORMALISM-OWNER-MUTATION-EXECUTOR-001
formalism_authority: Admissible-Existence/AE + RTG + GTG + TT + STCM
canonical_runtime_authority: StegVerse-Labs/StegCore / stegcore.steggate.evaluate_admissibility
capability_lifecycle_authority: StegVerse-Labs/StegCore
local_model_owner: StegVerse-002/micro-node-runtime
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_TV_TVC_secret_or_token_allowed: false
archive_ready: false
```

This lane binds source generation to the newest StegCore Admissible-Existence capability lifecycle and the least-stable execution principle. It does not create a parallel evaluator, a second model/runtime, a credential path, repository transport authority, merge authority, publication authority, or continuity custody authority.

## Originating session goal

Complete the generalized recursive build path without requiring another chat session:

```text
discover gap
-> reconcile
-> admit canonical owner
-> activate explicitly admitted source-generation capability
-> emit exact owner-source-generation packet
-> validate owner mutation scope
-> TVC bounded repository operation
-> owner validation/merge
-> reconciliation re-observes gap removed
```

## Canonical architecture

Source generation is itself a governed capability. Model availability, heartbeat observation, worker availability, coherence, gradient state, repository presence, or reconciliation output cannot grant source-generation authority.

The intended lifecycle is:

```text
DECLARED
-> STANDING
-> ADMISSIBLE
-> ACTIVATED only with integration evidence + activation proof
-> bounded execution
-> source packet externalized
-> teardown/reconstruct unless stronger persistence is separately admitted
```

Every capability transition remains subordinate to canonical StegGate. Structural validation may only block and may not widen canonical disposition.

## Least-stable execution requirement

The capability MUST request the smallest execution shape sufficient to produce one admitted owner source packet. Preferred posture is a one-shot or short-lived local worker using the already-released sovereign local model/runtime. Persistent residency is not presumed. If persistent execution is ever required, the justification, TTL/lease, state externalization, reconnect policy, teardown condition, and authority ceiling must be machine-readable and separately admitted.

## Inputs

```text
owner implementation work manifest:
  stegverse.owner-implementation-work-manifest/v0.1
source-generation output contract:
  stegverse.owner-source-generation-packet/v0.1
canonical owner-mutation consumer:
  SHWP-FORMALISM-OWNER-MUTATION-EXECUTOR-001
local model/runtime source:
  StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
StegCore AE capability registry/conformance:
  StegVerse-Labs/StegCore/docs/ADMISSIBLE_EXISTENCE_CAPABILITY_MODEL_MIRROR_HANDOFF.md
  StegVerse-Labs/StegCore/docs/AE_HANDOFF_TASK_CONFORMANCE_MIRROR_HANDOFF.md
organization AE enforcement:
  docs/ADMISSIBLE_EXISTENCE_CONTROL_PLANE_MIRROR_HANDOFF.md
```

## Required source packet bindings

A valid packet must bind at minimum:

```text
source_generation_authorized=true
generator_capability_id
generator_existence_hash
generator_phase=ACTIVATED
generator_activation_proof_ref
generator_integration_evidence_refs
generator_authority_ref
generator_profile_ref
owner_repository
owner_handoff_ref
delta_id
base_ref
base_sha
changed_paths
expected_source_hashes
replacement_contents_or_content_hashes
model_runtime_proof_ref
execution_identity
teardown_or_reconstruction_evidence_ref
credential_authority=TV/TVC
github_token_runtime_authority=false
```

The downstream owner-mutation executor continues to enforce handoff-first ordering, admitted path scope, exact hashes, and exact TVC inspection binding.

## Authority boundary

```text
source generation authority: only explicit AE capability activation
admissibility authority: canonical StegGate only
credential authority: TV/TVC only
repository credential transport: TVC #19/#20 only
heartbeat role: carrier/synchronization observation only
worker control plane: separate from heartbeat semantics
Master Records: custody/EOL/reconstruction only under its own contracts
wallet signing/broadcast: USER_ONLY where applicable
coherence/gradient/manifold observations: evidence only
```

## Active implementation claim

```text
claim_ref: control/session-implementation-claim-2026-08-14-admissible-source-generation-capability.json
claimant: current ChatGPT continuation session
role: CLAIMED_FOR_IMPLEMENTATION
claim_created_at: 2026-08-14T15:58:00-05:00
claim_expires_at: 2026-08-14T18:58:00-05:00
collision_exclusions:
  - canonical StegCore AE/StegGate semantics
  - TVC #19/#20 credential transport
  - .github #122 heartbeat/control-plane refactor
  - live worker claim/fence/lease/runtime state
release_condition: implementation is merged/validated or durably transferred to a proven active executor with machine-observable release conditions
```

## Required implementation surfaces

```text
ADMISSIBLE_SOURCE_GENERATION_CAPABILITY_MIRROR_HANDOFF.md
control/admissible-source-generation-capability.json
control/session-implementation-claim-2026-08-14-admissible-source-generation-capability.json
handoffs/SHWP-ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-001.json
control/worker-registry.d/admissible-source-generation-capability-001.json
control/process-worker-adapters.d/admissible-source-generation-capability-001.json
workers/admissible_source_generation_capability_worker.py
tests/test_admissible_source_generation_capability_worker.py
data/admissible-source-generation-capability/task-state.json
```

## Validation contract

```text
1. capability declaration/existence identity is deterministic;
2. source generation cannot proceed below ACTIVATED;
3. ACTIVATED requires integration evidence + activation proof;
4. future/planned work cannot pre-claim ACTIVATED;
5. model/worker/heartbeat availability cannot infer authority;
6. one-shot/short-lived execution is default and teardown/reconstruction evidence is required after bounded generation;
7. emitted packet exactly binds owner work/base/path/source hashes;
8. credential-bearing environment is empty; no GitHub/provider/wallet/TVC secret reaches the worker;
9. TVC transport is represented only as a downstream non-secret warrant boundary;
10. canonical HANDOFF + Worker Task Registry AE verifier passes for this task.
```

## Current dependencies

```text
StegCore AE lifecycle/registry/conformance: COMPLETE_VALIDATED_RELEASED
organization HANDOFF/Worker Registry AE conformance: COMPLETE_VALIDATED_RELEASED
sovereign local model source/runtime: COMPLETE_RELEASED, phase ADMISSIBLE pending live activation
owner mutation executor source: COMPLETE_VALIDATED_RELEASED
TVC repository broker: validation/admission pending under TV/TVC-owned continuation
resident first-cohort reconciliation: pending observation
```

## Exact next executable action

Implement the machine-readable capability policy, task/claim/registry/adaptor, fail-closed worker and deterministic tests without modifying any collision-owned surface. Hosted validation may prove source/control-plane conformance but cannot prove live source-generation activation. Resident activation proof must be produced by an authorized local execution using the canonical model/runtime path.

## Archive condition

This session remains active while this claim exists and no other proven active executor owns completion. Archive is prohibited until the capability implementation is merged/validated and the remaining resident recursive-build proof is either completed or transferred to an active executor that can actually advance it without this chat.
