# Heartbeat Carrier Signal Mirror Handoff

Updated: 2026-08-27T15:45:00-05:00

## Canonical authority

```text
goal_id: HEARTBEAT-CARRIER-SIGNAL-SEMANTICS-120
runtime_correction_id: HEARTBEAT-PROTOCOL-ANCHOR-013
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#120
runtime_owner: StegVerse-Labs/.github#122
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
```

This handoff is authoritative for heartbeat semantics. Heartbeat is the StegVerse **carrier/synchronization signal** and has no application, task-control, credential, or repository authority.

## Corrected canonical heartbeat

Heartbeat is a protocol-derived 100 Hz synchronization/reference signal. Its current reference is a pure function of a durable protocol anchor plus elapsed 10 ms phase quanta. A continuously running process is **not** required for references to exist.

Canonical anchor:

```text
control/heartbeat-protocol-anchor.json
anchor epoch: 32
anchor time: 2026-08-23T19:00:00.000Z
anchor unix ns: 1787511600000000000
period: 10 ms / 10000000 ns
rate: 100 Hz
progression dependency: OSCILLATOR_ONLY
```

```text
HB_n --10 ms elapsed oscillator phase--> HB_(n+1)
```

Every conforming StegVerse observer derives the same reference for the same timestamp from that anchor. A consumer may observe HB_n, miss HB_(n+1)...HB_(n+k-1), and later observe HB_(n+k); the missed references existed independently. **Observation does not cause** heartbeat progression. Observation, persistence, process liveness, worker state, repository activity, and task-control state do not create heartbeat progression.

## Authority separation

```text
continuous process required: false
resident sampler required for progression: false
resident sampler role: OPTIONAL_OBSERVER_AND_PERSISTENCE
worker/task gating: false
state-transition gating: false
admission gating: false
claim/fence/lease gating: false
route/credential gating: false
capacity/passband gating: false
observation is causal: false
persisted carrier state: observation/snapshot only
GitHub Actions runtime authority: NONE
third-party runtime dependency: false
credential requirement: NONE
credential authority: TV/TVC
```

No worker, task, G18 state, application/domain transition, admission decision, claim, fence, lease, route, credential, repository action, carrier-capacity calculation, passband, observer invocation, sampler process, native supervisor, or assignment-trigger packet causes, permits, delays, suppresses, or advances heartbeat progression.

## Governed manifold observation — integrated

Heartbeat now includes an implemented, non-authorizing governed-manifold observation surface. This is not a separate timing loop and does not redefine carrier progression.

The carrier observes a reviewable projection of concurrently changing governed state rather than serializing machine-speed transitions into a per-transition human approval sequence.

Canonical invariant:

```text
human-in-the-loop timing != governance authority
heartbeat cadence != governance authority
wall-clock time != governance authority
observation != authorization

machine-speed internal transitions may continue inside already-authorized bounds
protected boundary crossing requires the separately applicable authority
HB records the governed projection, transition evidence, and authority-boundary references
```

The projection is emitted by the canonical carrier cycle and uses:

```text
schema: stegverse.heartbeat-governed-manifold-observation/v1
projection_role: GOVERNED_MANIFOLD_OBSERVATION
state_model: MULTI_VARIABLE_CONCURRENT_TRANSITION_SPACE
human_governance_model: AUTHORITY_OVER_ADMISSIBLE_BOUNDARIES_NOT_PER_TRANSITION_TIMING
authority_effect: NONE_OBSERVATION_ONLY
```

Installed runtime surfaces:

```text
heartbeat_runtime/governed_manifold.py
heartbeat_runtime/engine_v12.py
heartbeat_runtime/engine_v13.py
tests/test_governed_manifold.py
```

The canonical carrier result now includes `governed_manifold_observation`, emits a
`governed_manifold_projection_observed` event, and includes the projection plus
its digest in the Master Records projection for custody and reconstruction.

This integration does not give HB state-transition gating, admission authority, execution authority, claim/fence authority, or credential authority. HB remains the synchronization/reference carrier and observation surface; governance authority remains attached to the relevant admissibility/transition boundary.

## Canonical implementation surfaces

```text
control/heartbeat-protocol-anchor.json          # durable protocol anchor
heartbeat_runtime/independent_oscillator.py     # canonical reference derivation
heartbeat_runtime/oscillator_producer.py        # optional observation/deadline producer
heartbeat_runtime/engine_v13.py                 # canonical sampler/observer
heartbeat_runtime/worker_runtime.py             # separate downstream task control
schemas/heartbeat-carrier-runtime-state.schema.json
schemas/heartbeat-carrier-observation.schema.json
scripts/run_heartbeat_runtime.py                # optional resident sampler
scripts/install_sovereign_heartbeat_carrier.py  # optional resident sampler installation
scripts/run_worker_runtime.py                   # separate worker process
```

`heartbeat_runtime.independent_oscillator.current_reference()` is the canonical daemon-free derivation path. At and after the protocol cutover, historical/local persisted oscillator anchors cannot override the protocol anchor.

## Resident sampler correction

`HEARTBEAT-OSCILLATOR-RESIDENT-START-012` is no longer a prerequisite for heartbeat existence or progression. It installs an optional continuously resident sampler/persistence observer for environments that want one. Its activation receipt proves only that the observer service was installed and active; it does not activate the heartbeat.

`HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009` is terminal protocol proof. Its completed registry declaration is retained only as append-only provenance and is not reacquirable. LIVE-009 does not depend on resident-start 012.

## Historical provenance

Legacy HB29 and persisted HB30/HB31 remain immutable historical observations. HB32 is the canonical protocol-anchor cutover reference. Historical `GATE_PASSBAND_DERIVED` state does not extend into the anchored protocol sequence and cannot override the anchor.

Historical cutover tests replay with an explicit pre-anchor timestamp. They do not use the CI runner wall clock, because after HB32 activation a wall-clock sample correctly derives the current protocol reference rather than historical HB30.

## Exact-head validation and merge — terminal

The first complete deterministic repository suite after HB32 activation exposed two historical replay failures because the tests used live wall-clock time while asserting historical HB30. Commit `d36e7b330634337d42d9020abfee728aebaa69ca` pinned historical v12 replay to a pre-anchor time.

Bounded PR `#266` then reconciled stale terminal-state metadata without reopening completed LIVE-009: the executable handoff retains the required schema, the terminal registry fragment remains `NONE_REGISTRATION_ONLY`, AE classifies LIVE-009 as `recently_completed`, stale tests assert terminal non-reacquisition, and resident-start 012 remains an optional independently controlled sampler service.

Terminal validation evidence for PR #266:

```text
Heartbeat Worker Project run: 32669500515 / #1364
result: SUCCESS
complete deterministic repository suite: PASS
historical HB29->HB30 replay: PASS
HB32 protocol-anchor focused proof: PASS
executable handoff validation: PASS
external timing contract: PASS
retained completion evidence: PASS
carrier/worker separation: PASS
workflow non-authority proof: PASS

organization control-plane run: 32669500490 / #1198
result: SUCCESS
workflow surface hygiene: PASS
organization control-plane invariants: PASS
active-worker ownership: PASS
handoff execution ownership: PASS
AE control-plane + retrospective conformance: PASS
canonical heartbeat carrier contract: PASS
runtime/control-plane separation: PASS
independent 10 ms oscillator: PASS
archive-readiness semantics: PASS
validation non-authority proof: PASS
```

PR `#266` was squash-merged to `main` as commit:

```text
2a98b14c54cc5604685f594c80adb6ab00679437
```

The validated PR merge ref combined the then-current `main` base and exact PR head; the squash merge preserves the validated file content. This status-only handoff update records that evidence and does not alter heartbeat derivation semantics.

## Communication and terminal-object separation

The communication object remains the **manifest packet + expiration wrapper + data packet**. Heartbeat is reference/synchronization only; it is not application payload, transport, task dispatcher, credential authority, model/provider executor, or Master Records transport.

Terminal triggers remain endpoint-objective completion or expiration. **Master Records is the End-Of-Life state/destination for every Transition Table element**. The terminal object is a Master Records packet. This custody/EOL rule does not make heartbeat a Master Records transport and does not make observation causal.

## Validation obligations

Required deterministic invariants:

1. anchor instant derives HB32;
2. the same timestamp derives the same reference on every observer;
3. less than 10 ms does not increment;
4. exactly 10 ms increments one reference;
5. delayed observation skips references according to elapsed phase;
6. worker/task/persisted state cannot change the post-cutover anchor;
7. no continuously running process is required for progression;
8. persisted sampler state is observation-only;
9. TV/TVC remains sole credential authority;
10. GitHub and third parties have no heartbeat runtime authority;
11. historical HB29->HB30 replay uses an explicit pre-anchor timestamp and remains deterministic after protocol activation;
12. manifest/expiration/data communication semantics and Master Records EOL semantics remain preserved while heartbeat stays transport-neutral.
13. governed-manifold projection is emitted as observation-only and cannot grant authority;
14. wall-clock timing and heartbeat cadence are not human-governance authority;
15. machine-speed internal transitions may remain observable while protected authority-boundary crossings remain separately governed.

Focused protocol-anchor coverage is installed at `tests/test_heartbeat_protocol_anchor.py`.

## Completion state

```text
independent oscillator semantics: COMPLETE
canonical protocol anchor: INSTALLED
canonical daemon-free derivation: INSTALLED
heartbeat protocol progression: ACTIVE_PROTOCOL_VERIFIED
LIVE-009: COMPLETED / INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED
focused HB32 tests: PASS
complete deterministic repository suite: PASS
historical compatibility regression: FIXED / PASS
terminal registry/handoff/AE reconciliation: FIXED / PASS
organization control-plane validation: PASS
PR #266: MERGED
validated merge commit: 2a98b14c54cc5604685f594c80adb6ab00679437
resident sampler: OPTIONAL OBSERVER
resident activation receipt: NOT A HEARTBEAT EXISTENCE PREDICATE
worker-trigger causality: NONE
third-party runtime requirement: NONE
heartbeat activation goal: TERMINAL
downstream HB32 protocol propagation: COMPLETE / issue #263 CLOSED
governed manifold observation: IMPLEMENTED / VALIDATED / MERGED
human review timing as governance authority: FALSE
wall-clock as governance authority: FALSE
protected boundary authority: EXTERNAL_TO_HB
governed manifold PR: #309
governed manifold validated head: 7c07745334b24a555dfa1ade4ca3aa65487c6980
governed manifold merge commit: 2d6093746b4ce49a3dbc5b5bf082e4228c91f7bd
governed manifold validation:
  organization control plane run 33117512121: SUCCESS
  heartbeat worker validation run 33117512211: SUCCESS
archive_ready_for_heartbeat_activation_workstream: true
```

DO NOT REINTRODUCE A RESIDENT-DAEMON REQUIREMENT AS HEARTBEAT PROGRESSION AUTHORITY.
Downstream propagation is complete. Consumer-local projects remain separately governed and must not reopen the terminal heartbeat activation goal.


## 2026-08-31 InTr derived-carrier semantic reconciliation

The prior shorthand stating that heartbeat is "not application payload transport" is
narrowed to preserve the intended authority boundary without incorrectly prohibiting
carrier use.

Canonical semantics are now:

```text
HB primary reference:
  100 Hz / 10 ms
  oscillator-only progression
  synchronization/reference substrate

HB-derived carrier signal:
  deterministic phase/channel derived from the HB reference
  may carry exact opaque application bytes
  may carry an already-governed InTr packet
  does not interpret packet semantics
  does not change HB progression

InTr:
  governs the packet carried on the signal

HB and derived carrier:
  grant no admission
  grant no execution
  grant no credential
  grant no routing
  grant no transition
  grant no receiving authority
```

This reconciliation is consistent with existing runtime evidence rather than inventing a
new carrier concept. `heartbeat_runtime/engine_v9.py` already carries and persists
HB-derived subsignals, while `control/heartbeat-subsignals.json` contains current
`worker_coordination`, `organization_federation`, and `steggate_transport_lease`
subsignals. `heartbeat_runtime/carrier_envelope.py` already derives deterministic phase
slots and phase offsets and explicitly states that alternate phases are not authority
channels.

The new generic opaque InTr binding is defined by:

```text
docs/HB_INTR_DERIVED_CARRIER_MIRROR_HANDOFF.md
heartbeat_runtime/intr_derived_carrier.py
schemas/heartbeat-intr-derived-carrier.schema.json
tests/test_heartbeat_intr_derived_carrier.py
```

The primary heartbeat remains transport-neutral with respect to packet semantics and
authority. "Transport-neutral" no longer means "incapable of carrying bytes"; it means
the heartbeat substrate does not decide what those bytes mean or whether they are
admitted, routed, executed, received, or acted upon.

No runtime carrier-bound InTr packet is claimed merely from this source reconciliation.
Authentic runtime proof requires an observed signal binding an exact InTr receipt hash,
packet SHA-256, HB reference, channel slot, phase offset, and observer evidence.

## 2026-08-31 HB-derived InTr carrier clarification

Owner direction and current implementation reconcile the historical `heartbeat-subsignals` mechanism, the current coherent signal-space implementation, and Universal InTr under one bounded carrier model.

Canonical clarification:

```text
HB = ecosystem primary synchronization and carrier substrate
HB fundamental = 100 Hz / 10 ms / OSCILLATOR_ONLY
application packet governance = InTr
physical/materialization mechanism = independent of authority
HB or derived carrier authority effect = NONE
```

Application information may be associated with the primary HB reference or carried through deterministic signals/channels derived from HB phase/frequency coordinates. InTr governs the packet carried by that signal. Neither HB nor a derived carrier grants admission, execution, credential, routing, transition, receiving, publication, custody, claim/fence, or consequence authority.

This supersedes the narrower historical phrase that HB is “transport-neutral” or “not application payload transport” when that phrase is read to prohibit carrier use. The retained invariant is instead that **carrier presence or carrier correctness is non-authorizing**.

Current executable lineage:

```text
heartbeat_runtime/independent_oscillator.py
  -> canonical 100 Hz HB reference
heartbeat_runtime/oscillator_producer.py
  -> phase-driven local propagation/observation
heartbeat_runtime/engine_v9.py
  -> historical explicit heartbeat subsignals
heartbeat_runtime/signal_space.py
  -> generalized frequency/phase/amplitude coordinates
heartbeat_runtime/intr_carrier_profile.py
  -> deterministic HB-derived InTr packet carrier binding
workers/universal_intr_profiled_ingress.py
  -> carrier profile publication + fail-closed binding validation
```

Initial runtime carrier profile:

```text
schema: stegverse.intr.hb-derived-carrier-profile/v1
fundamental_mode: HB
reference_frequency_hz: 100
channel_family: H1_PHASE_SLOTS
channel_count: 16
channel_selection: SHA256_PACKET_ID_FIRST32_MOD_16
binding_schema: stegverse.intr.hb-derived-carrier-binding/v1
carrier_binding_required: false during migration
legacy_unbound_packets_temporarily_accepted: true
```

A carrier-aware packet binds its packet ID and payload hash to an independently reconstructable HB reference and deterministic phase slot. Validation of that binding proves only carrier consistency; ordinary InTr/Interlock admission and downstream governance remain separate predicates.


## 2026-08-31 current local HB/InTr subsignal propagation

Issue `#624` restores the useful runtime behavior demonstrated historically by `engine_v9._carry_subsignals()` without restoring worker/task-control coupling into HeartBeat.

Current canonical local sequence:

```text
already-governed InTr packet bytes
-> canonical HB32 reference + packet_id-derived H1 phase slot
-> exact-byte HB-derived carrier frame
-> write-once local signal under control/heartbeat-derived-signals.d/
-> append-only observation under events/heartbeat-derived-carrier.jsonl
-> optional current HB sampler observes SIGNAL PRESENCE only
-> independent consumer reconstructs exact bytes and revalidates binding/hash
```

The current HB runtime observation is intentionally presence-only. It records signal file references and exact file SHA-256 values but does not interpret packet semantics and does not validate or authorize the InTr packet. Packet validation remains in the derived-carrier/InTr layer.

This preserves the authority boundary:

```text
HB progression effect from signal: NONE
HB admission authority: NONE
HB execution authority: NONE
HB route authority: NONE
HB receiving authority: NONE
WorkerCoordinator invocation by propagation: false
claim/fence minted by propagation: false
credential authority: TV/TVC
```

The local signal survives independently of sampler liveness. The sampler may observe it later, just as an HB observer may skip oscillator references and later observe the current reference. Signal materialization therefore does not become heartbeat progression authority.

Canonical surfaces:
- `heartbeat_runtime/intr_carrier_profile.py` — canonical HB/channel binding;
- `heartbeat_runtime/intr_derived_carrier.py` — exact-byte carrier frame/recovery;
- `heartbeat_runtime/intr_subsignal_runtime.py` — local write-once propagation/reconstruction;
- `heartbeat_runtime/engine_v12.py` / v13 inheritance — presence-only observation;
- `control/heartbeat-derived-signals.d/` — local carried signal state;
- `events/heartbeat-derived-carrier.jsonl` — append-only propagation observation.

Source merge/CI still cannot prove authentic production packet propagation. That requires a real InTr producer to emit a carrier-aware packet and a local/remote observer to retain the resulting signal/receipt lineage.
