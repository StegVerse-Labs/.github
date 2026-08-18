# Canonical Operational State Vector (COSV) Mirror Handoff

Updated: 2026-08-18T08:29:00-05:00
Repository: `StegVerse-Labs/.github`
Branch: `main`

## Active goal

```text
goal_id: COSV-ARCHITECTURE-001
originating_goal: Canonically encode task, goal, component, subsystem, system, and ecosystem operational state as compact numeric vectors for fast algorithmic reading while retaining deterministic links to full evidence.
canonical_owner: StegVerse-Labs/.github
claim_state: CLAIMED_FOR_IMPLEMENTATION
claimant: chatgpt-session-cosv-architecture-20260818
claim_created_at: 2026-08-18T08:29:00-05:00
claim_release_condition: architecture/profile/schema/encoder-validator-aggregator/tests/examples are installed and deterministic validation passes; ownership is then released to repository-native continuation.
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
third_party_runtime_required: false
render_required: false
```

## Design invariant

COSV is a fast operational index, not a replacement for evidence. Every vector MUST resolve to a canonical identity and evidence references. Missing or unknown evidence MUST remain visible as unknown/fail-closed state rather than being rounded into success.

The architecture has two canonical vector families:

1. `task.v1` — direct operational disposition and ownership state for one executable task.
2. `aggregate.v1` — factor aggregate for goal/component/subsystem/system/ecosystem nodes.

A third structure, `transition.v1`, deterministically compares two compatible vectors and records per-position change classes.

## Numeric domains

```text
ternary truth digit:
0 = false
1 = true
2 = unknown / not established

quantity digit:
0..8 = exact count
9 = 9-or-more (saturated fast-path count; exact count remains in evidence metadata)

factor digit:
0 = 0%
1 = 1-12%
2 = 13-24%
3 = 25-37%
4 = 38-49%
5 = 50-62%
6 = 63-74%
7 = 75-87%
8 = 88-99%
9 = 100%

lifecycle digit:
0 UNKNOWN
1 UNCLAIMED
2 CLAIMED_IMPLEMENTATION
3 CLAIMED_VALIDATION
4 CLAIMED_INTEGRATION
5 MACHINE_OWNED
6 BLOCKED
7 COMPLETE
8 SUPERSEDED
9 MERGED_INTO_CANONICAL_WORKSTREAM
```

## Canonical task vector

`task.v1` is exactly 14 digits in this order:

```text
L R U I V G O C M T B E A P
```

```text
L lifecycle                  lifecycle digit
R archive_ready              ternary
U unassigned_work            quantity
I chat_owned_implementation  quantity
V chat_owned_validation      quantity
G chat_owned_integration     quantity
O chat_owned_observation     quantity
C chat_owned_credentials     quantity
M canonical_owner_installed  ternary
T thread_required            ternary
B blocker_count              quantity
E evidence_complete          ternary
A activated                  ternary
P propagated                 ternary
```

Example from the session-consolidation state:

```text
MERGED_INTO_CANONICAL_WORKSTREAM
archive_ready=true
all chat-owned/unassigned counts=0
canonical owner installed=true
thread_required=false
blockers=0
evidence_complete=true
activated=false
propagated=unknown

=> 91000000100102
```

The final digits intentionally distinguish session-consolidation completeness from product activation.

## Canonical aggregate vector

`aggregate.v1` is exactly 14 digits for goals and every higher aggregation level:

```text
L D V I P A R O E B X U S T
```

```text
L lifecycle factor/state          lifecycle digit
D developed factor                factor digit
V validation factor               factor digit
I integration factor              factor digit
P propagation factor              factor digit
A activation factor               factor digit
R release/readiness factor        factor digit
O ownership completeness factor   factor digit
E evidence completeness factor    factor digit
B critical blocker count          quantity
X conflicting claim count         quantity
U unassigned work count           quantity
S stale claim count                quantity
T thread_required                 ternary
```

The same profile is used for `goal`, `component`, `subsystem`, `system`, and `ecosystem`; the node `level` is carried outside the vector so the fixed-width vector remains comparable.

## Aggregation

Each child contributes factor values and optional integer weights. Aggregation is deterministic:

- factor fields use weighted arithmetic mean over exact underlying percentages when supplied; otherwise weighted mean over canonical factor midpoints;
- lifecycle is derived from child lifecycle and hard constraints, not averaged;
- blocker/conflict/unassigned/stale quantities are summed then saturated at 9 for the vector while exact totals remain in metadata;
- ownership/evidence factors are weighted like other factors;
- `thread_required` is true if any canonical child requires the thread, false only if all known children are false, otherwise unknown;
- a critical blocker or conflicting active claim prevents aggregate lifecycle `COMPLETE`/`MERGED` unless the profile explicitly identifies the node as a consolidation-only aggregate and all remaining work is canonically owned.

Criticality weights are integers 1..9. Weight 9 is highest. Weight values affect factors but never erase blockers or unknown authority.

## Transition vectors

`transition.v1` compares vectors with the same profile and width. Each position receives one transition digit:

```text
0 unchanged
1 improved
2 regressed
3 became_known
4 became_unknown
5 ownership_transfer
6 entered_blocked
7 exited_blocked
8 terminalized
9 semantic_change_requires_evidence_review
```

Field directionality is profile-defined. For counts, lower is normally better; for factors, higher is better; ternary fields use explicit semantic rules; lifecycle uses the lifecycle transition table.

## Evidence binding

Every canonical record MUST include:

```text
identity
profile
level
vector
evidence_refs[]
source_hash or source_commit when available
observed_at
exact_metrics{} for unsaturated quantities/percentages
```

The vector is therefore an index into the evidence graph. It must never be treated as self-authenticating evidence.

## Required repository surfaces

```text
docs/CANONICAL_OPERATIONAL_STATE_VECTOR_MIRROR_HANDOFF.md
management/COSV_PROFILE_V1.json
schemas/cosv_record.schema.json
scripts/cosv.py
tests/test_cosv.py
examples/cosv_examples.json
```

## Validation commands

```text
python scripts/cosv.py self-test
python -m unittest tests.test_cosv
python scripts/cosv.py validate examples/cosv_examples.json
```

## Cross-repository integration

Initial owner is organization control plane `StegVerse-Labs/.github`. Consumers SHOULD import the profile rather than define competing digit semantics. Candidate first consumers after release are the heartbeat worker/task registry, Site session-work claims, TV/TVC machine tasks, StegFin task-state records, and Master Records reconstruction/indexing. No propagation is claimed until a consumer imports and validates the profile.

## Completion accounting

```text
required_files: 6
developed_files: 1/6
scaffolding_or_stubs: 0
missing_required_files: 5
validation: 0/3
integration: 0/1
activation: 15%
session_consolidation: 0/1
```

## Archive condition

This goal is not archive-ready until all six surfaces are installed, deterministic self-tests pass, example records validate, the active implementation claim is released, and a repository-native continuation/consumer boundary is recorded. Product-level COSV adoption across every StegVerse repository is not required for this architecture slice to release; such adoption must be tracked as separate integration work.