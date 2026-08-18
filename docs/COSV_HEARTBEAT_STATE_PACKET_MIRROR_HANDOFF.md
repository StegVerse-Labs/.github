# COSV Heartbeat State Packet Mirror Handoff

Updated: 2026-08-18T15:00:00-05:00
Repository: `StegVerse-Labs/.github`
Branch: `main`

## Goal

`COSV-HEARTBEAT-STATE-PACKET-002` extends released COSV vectors into an authority-neutral packet layer carried/observed on the heartbeat reference frame and suitable as the canonical input surface for gradient mechanics.

Canonical issue: `#217`
Source claim: `#218` CLOSED COMPLETED
Handoff tracker: `#219` CLOSED COMPLETED
Parent COSV handoff: `docs/CANONICAL_OPERATIONAL_STATE_VECTOR_MIRROR_HANDOFF.md`
Heartbeat architecture/live owner: `#122`
Gradient/nervous-system owner: `StegVerse-Labs/StegBrain#860/#861`
Source state: `COMPLETE_RELEASED`
Live adoption state: `FIRST_LIVE_FULL_PACKET_EMITTED_HB31`
Live integration claim: `control/session-integration-claim-2026-08-18-cosv-live-packet-217.json`
Credential authority: `TV/TVC`
NON-TV/TVC secret/token allowed: `false`
GitHub-token runtime authority: `NONE`
Third-party runtime role: `FALLBACK_ONLY`
StegVerse primary: `true`

## Responsibility split

```text
heartbeat = carrier/reference frame only
COSV packet = state/transition payload + evidence bindings, authority effect NONE
StegBrain = admissibility/coherency/gradient evaluator and typed observation originator
worker/domain subsystem = actor only under separately admitted authority
Master Records = passive custody/evidence
TV/TVC = credential/secret/token authority
```

The packet never grants execution, claim, fence, lease, route, credential, wallet, signing, broadcast, custody, policy, admissibility, coherency, or gradient authority.

## Packet modes

`FULL` packets carry the complete ordered COSV record set for a reference frame.

`DELTA` packets carry only changed COSV records, bind the predecessor packet hash, bind an unchanged-state root, carry the resulting full-state root, and expose deterministic transition/gradient-input records. Record deletion is intentionally fail-closed in v1.

Every packet carries schema/mode, carrier reference and observation time, predecessor packet digest where applicable, full state root, unchanged-state root for deltas, ordered COSV records, gradient inputs for changed records, exact constraint summary, authority invariants, and a packet SHA-256 over canonical JSON excluding the digest field itself.

## First live carrier-bound packet — HB31

Direct live evidence now satisfies the former `#122` release dependency:

```text
control/heartbeat-carrier-runtime-state.json
  activation_state: ACTIVE
  epoch/generation: 31/31
  role: REGULATORY_CARRIER_REFERENCE_FRAME

control/worker-runtime-state.json
  last_observed_carrier_epoch/generation: 31/31
  observation_mode: CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION

receipts/heartbeat-transition-continuity/latest.json
  state: CARRIER_TRANSITION_COMPLETE
  release_state: RELEASE_COMPLETE
  all_carrier_transition_predicates_pass: true
  all_release_predicates_pass: true
```

The first live FULL COSV packet is persisted at:

`receipts/cosv/live/HB31.json`

```text
carrier_ref: heartbeat_epoch:31
packet_sha256: 618ca9d0b8d6a2dbd661378b8ca9814dd9b882efb40d351c0d517bff8f4e17bd
state_root_sha256: b9ae6209961a3cbd85cc9531088ca91531b03c3eaa4ccc53ee46b0dc1937d22a
records: 2 authority-neutral task.v1 state records
critical_blockers: 0
unassigned_work: 0
heartbeat_authority_effect: NONE
packet_authority_effect: NONE
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_used: false
github_token_runtime_authority: NONE
```

Validation receipt:
`receipts/cosv/live/HB31-validation.json`.

The packet was generated from directly observed committed carrier/worker/release evidence and deterministically rechecked for canonical packet digest, state root, vector shape, evidence references, constraint summary, and authority invariants. No hosted-workflow runtime proof is substituted for the live carrier evidence.

## Gradient-ready interface

Each changed identity in a DELTA packet may expose:

```text
identity
level
profile
previous_vector
current_vector
transition_vector
previous_exact_metrics
current_exact_metrics
admissibility_ref
coherency_group_ref
authority_effect=NONE
```

The HB31 packet is intentionally a FULL baseline and therefore has empty `gradient_inputs`. The next admitted carrier reference with a changed state can produce a DELTA packet against HB31; that DELTA is the first eligible live gradient-input surface for `StegVerse-Labs/StegBrain#861`.

## Canonical source surfaces

```text
management/COSV_HEARTBEAT_STATE_PACKET_CONTRACT.json
schemas/cosv_state_packet.schema.json
scripts/cosv_state_packet.py
tests/test_cosv_state_packet.py
examples/cosv_state_packet_examples.json
receipts/cosv/COSV-HEARTBEAT-STATE-PACKET-002-validation.json
receipts/cosv/live/HB31.json
receipts/cosv/live/HB31-validation.json
```

## Collision boundaries

Do not mutate `control/heartbeat-state.json`, carrier runtime state, WorkerCoordinator state, G18 claim/fence/lease, TV/TVC protected state, model/provider/wallet state, or Master Records custody from the packet layer. Live packet observation reads carrier state; it does not become carrier authority.

## Validation

Source validation remains:

```text
self-test: PASS
focused tests: 5/5 PASS
full packet digest verification: PASS
delta reconstruction: PASS
gradient input derivation: PASS
implicit record removal fail-closed: PASS
digest tamper rejection: PASS
non-TVC credential authority rejection: PASS
```

Live integration validation now additionally records:

```text
HB31 live carrier observed: PASS
HB31 independent worker reference observed: PASS
heartbeat transition release predicates: PASS
live FULL packet persisted: PASS
packet canonical digest recomputation: PASS
state-root recomputation: PASS
authority invariants: PASS
hosted workflow claimed as live proof: false
StegBrain live gradient observation claimed: false
```

## Integration / continuation

The packet architecture's first live-adoption requirement is satisfied at HB31. Issue `#217` may close as completed for first-live-packet integration.

Downstream work remains required and is not satisfied by this release:

1. the carrier must advance to another admitted reference with state change;
2. `.github` emits a DELTA packet against `receipts/cosv/live/HB31.json`;
3. `StegVerse-Labs/StegBrain#861` consumes the DELTA `gradient_inputs` and persists the first live gradient observation;
4. `StegVerse-Labs/StegBrain#865` consumes a separately precommitted expectation for the same target reference and persists the first live expectation-residual observation;
5. after at least two ordered live observations, `StegVerse-Labs/StegBrain#863/#865` may persist the first real gradient matrix/residual series and curvature evidence.

## Completion accounting

```text
source required surfaces: 6/6
source developed files: 6/6
live adoption required surfaces for first packet: 2/2
scaffolding/stubs: 0
missing required files: 0
source focused deterministic validation: 5/5 PASS
first-live-packet validation: PASS
first live producer adoption: COMPLETE_AT_HB31
first live gradient observation: PENDING_NEXT_CHANGED_DELTA
packet-layer integration claim: RELEASEABLE
```

## Archive / continuation condition

The packet source and first-live-packet integration are complete. The broader session is not archive-eligible under the governing completion rule while required downstream live gradient, expectation-residual, matrix/trajectory, sovereign inference, propagation, activation, or evidence obligations remain nonterminal. Canonical continuation is `.github#122/#60` plus `StegBrain#861/#863/#865`.