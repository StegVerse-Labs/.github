# COSV Heartbeat State Packet Mirror Handoff

Updated: 2026-08-18T08:46:00-05:00
Repository: `StegVerse-Labs/.github`
Branch: `main`

## Goal

`COSV-HEARTBEAT-STATE-PACKET-002` extends released COSV vectors into an authority-neutral packet layer carried/observed on the heartbeat reference frame and suitable as the canonical input surface for later gradient mechanics.

Canonical issue: `#217`
Source claim: `#218`
Handoff tracker: `#219`
Parent COSV handoff: `docs/CANONICAL_OPERATIONAL_STATE_VECTOR_MIRROR_HANDOFF.md`
Heartbeat architecture owners: `#120`, `#122`, `#183`
Gradient/nervous-system owner: `StegVerse-Labs/StegBrain#860` and integration request `StegVerse-Labs/StegBrain#861`

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

Every packet carries:
- schema/mode;
- carrier reference and observation time;
- predecessor packet digest where applicable;
- full state root;
- unchanged-state root for deltas;
- ordered COSV records;
- gradient inputs for changed records;
- exact constraint summary;
- explicit authority invariants;
- packet SHA-256 over canonical JSON excluding the digest field itself.

## Gradient-ready interface

Each changed identity may expose:

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

This is the input plane for gradient mechanics, not gradient authority. StegBrain owns interpretation under its existing contract.

## Canonical source surfaces

```text
management/COSV_HEARTBEAT_STATE_PACKET_CONTRACT.json
schemas/cosv_state_packet.schema.json
scripts/cosv_state_packet.py
tests/test_cosv_state_packet.py
examples/cosv_state_packet_examples.json
receipts/cosv/COSV-HEARTBEAT-STATE-PACKET-002-validation.json
```

## Collision boundaries

Do not mutate `control/heartbeat-state.json`, HB30 carrier state, G18 claim/fence/lease, WorkerCoordinator, worker registry, TV/TVC protected state, model/provider/wallet state, or Master Records custody. Live producer/consumer migration remains with `#122`.

Credential authority: TV/TVC. NON-TV/TVC secret/token allowed: false. GitHub-token runtime authority: NONE. Third-party runtime required: false.

## Validation

Required commands:

```text
python scripts/cosv_state_packet.py self-test
python -m unittest tests.test_cosv_state_packet
```

Source completion does not claim live heartbeat packet emission or StegBrain gradient evaluation.

## Release condition

Release this source claim after all listed surfaces are installed, deterministic validation passes, #122 is recorded as live migration owner, and StegBrain#861 carries gradient-consumer integration. Then close #218/#219 and mark #217 source-complete while leaving live adoption separately owned.