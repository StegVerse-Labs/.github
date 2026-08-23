# Heartbeat Carrier Signal Mirror Handoff

Updated: 2026-08-23T14:33:00-05:00

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

This handoff is authoritative for heartbeat semantics.

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

Every conforming StegVerse observer derives the same reference for the same timestamp from that anchor. A consumer may observe HB_n, miss HB_(n+1)...HB_(n+k-1), and later observe HB_(n+k); the missed references existed independently. Observation, persistence, process liveness, worker state, repository activity, and task-control state do not create heartbeat progression.

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

`HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009` must verify canonical derivability and observation neutrality. It must not wait on resident-start 012 merely to prove that heartbeat references exist.

## Historical provenance

Legacy HB29 and persisted HB30/HB31 remain immutable historical observations. HB32 is the canonical protocol-anchor cutover reference. Historical `GATE_PASSBAND_DERIVED` state does not extend into the anchored protocol sequence and cannot override the anchor.

Historical cutover tests must replay with an explicit pre-anchor timestamp. They must not implicitly use the CI runner wall clock, because after HB32 activation a wall-clock sample correctly derives the current protocol reference rather than historical HB30.

## Full-suite regression found 2026-08-23

The focused HB32 protocol-anchor suite passed 6/6, but the subsequent complete deterministic repository suite exposed two failures in `tests/test_heartbeat_engine_v12_cutover.py`:

```text
test_dry_run_previews_hb30_without_creating_cutover_state
test_first_write_freezes_hb29_and_emits_hb30_separated_schema
observed epoch: 138224
expected historical replay epoch: 30
suite result: 519 tests / 2 failures
```

Root cause: those historical replay tests called `HeartbeatRuntime.cycle()` without `now_ns`, so once the protocol anchor became active they sampled the live wall clock and legitimately entered the post-anchor derivation path. The assertions were historical, but the test input was no longer historical.

Correction commit:

```text
d36e7b330634337d42d9020abfee728aebaa69ca
```

The v12 cutover tests now use an explicit fixed pre-anchor replay instant (`HISTORICAL_CUTOVER_SAMPLE_NS = 2_000_000_000`) for all historical migration operations. This preserves HB29/HB30/HB31 replay semantics without weakening the HB32 protocol anchor.

Do not alter `current_reference()` or allow persisted historical state to override HB32 merely to make the legacy tests pass.

## Communication separation

The communication object remains the **manifest packet + expiration wrapper + data packet**. Heartbeat is reference/synchronization only; it is not application payload, transport, task dispatcher, credential authority, model/provider executor, or Master Records transport.

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
11. historical HB29->HB30 replay uses an explicit pre-anchor timestamp and remains deterministic after protocol activation.

Focused protocol-anchor coverage is installed at `tests/test_heartbeat_protocol_anchor.py`.

## Completion state

```text
independent oscillator semantics: COMPLETE_SOURCE
canonical protocol anchor: INSTALLED
canonical daemon-free derivation: INSTALLED
heartbeat protocol progression: ACTIVE_BY_PROTOCOL_DERIVATION
focused HB32 tests: 6/6 PASS
complete deterministic repository suite: PREVIOUS RUN 519 / 2 FAILURES
historical compatibility regression: PATCHED IN d36e7b330634337d42d9020abfee728aebaa69ca
exact-head complete-suite validation after patch: PENDING CI EVIDENCE
resident sampler: OPTIONAL OBSERVER
resident activation receipt: NOT A HEARTBEAT EXISTENCE PREDICATE
worker-trigger causality: NONE
third-party runtime requirement: NONE
remaining work: obtain exact-head full-suite PASS; then reconcile downstream propagation
archive_ready: false until exact-head full-suite validation is terminal
```

DO NOT REINTRODUCE A RESIDENT-DAEMON REQUIREMENT AS HEARTBEAT PROGRESSION AUTHORITY.
DO NOT CLAIM FULL REPOSITORY VALIDATION UNTIL THE POST-PATCH COMPLETE SUITE PASSES.
