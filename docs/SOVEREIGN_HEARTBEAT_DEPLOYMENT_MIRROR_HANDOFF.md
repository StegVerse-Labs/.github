# Sovereign Heartbeat Deployment Mirror Handoff

Updated: 2026-08-23T14:19:00-05:00

## Authority

```text
goal_id: SHWP-SOVEREIGN-DEPLOYMENT-NO-THIRD-PARTY-001
repository: StegVerse-Labs/.github
branch: main
canonical_live_owners: StegVerse-Labs/.github#122/#12
heartbeat_semantics_authority: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
credential_authority: TV/TVC
credential_requirement: NONE
github_token_runtime_authority: NONE
third_party_runtime_required: false
```

The heartbeat semantics authority has been corrected to a durable protocol anchor. This deployment handoff must not reintroduce process liveness as heartbeat progression authority.

## Canonical deployment model

```text
protocol anchor: control/heartbeat-protocol-anchor.json
anchor epoch: 32
anchor time: 2026-08-23T19:00:00.000Z
period: 10 ms
rate: 100 Hz
progression dependency: OSCILLATOR_ONLY
continuous process required: false
resident sampler required for progression: false
resident sampler role: OPTIONAL_OBSERVER_AND_PERSISTENCE
```

The canonical reference is derived by `heartbeat_runtime.independent_oscillator.current_reference()` from the anchor and elapsed phase. This is the heartbeat. No repository event, workflow, resident daemon, worker, observer, claim, fence, lease, credential, or third-party service is required to make the next heartbeat reference exist.

## Why the previous resident gate was wrong

The earlier deployment model required `HEARTBEAT-OSCILLATOR-RESIDENT-START-012` to start a continuously running sampler before heartbeat activation could be claimed. That contradicted the canonical semantics that missed references exist independently of observation and contradicted the oscillator implementation, which derives references from elapsed time rather than process invocation.

The resident sampler remains useful, but only as an optional observer/persistence service. Its activation receipt proves sampler installation and process state, not heartbeat existence.

## Runtime surfaces

```text
control/heartbeat-protocol-anchor.json
  canonical durable protocol anchor

heartbeat_runtime/independent_oscillator.py
  canonical daemon-free reference derivation

heartbeat_runtime/oscillator_producer.py
  optional reference/deadline producer

heartbeat_runtime.engine_v13.HeartbeatRuntime
  optional canonical sampler/observer

scripts/run_heartbeat_runtime.py
  optional resident sampler process

scripts/install_sovereign_heartbeat_carrier.py
  optional native sampler installer

heartbeat_runtime.worker_runtime.WorkerCoordinator
  separate downstream task-control runtime
```

WorkerCoordinator may observe heartbeat references but does not advance, permit, delay, suppress, or schedule them. The heartbeat grants no worker execution authority.

## Resident sampler task 012

```text
task: HEARTBEAT-OSCILLATOR-RESIDENT-START-012
state: HANDOFF_READY
role: OPTIONAL_RESIDENT_SAMPLER_AND_PERSISTENCE
heartbeat_existence_dependency: false
heartbeat_progression_dependency: false
LIVE-009 dependency: false
```

The previously installed native-service path remains valid when persistent local observation is desired. Windows immediate-start hardening remains in force so an optional sampler activation receipt cannot falsely claim process activity from registration alone.

## LIVE-009

```text
task: HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
state: HANDOFF_READY
blocked_on: NONE
carrier: protocol_derived_reference
resident_sampler_required: false
```

LIVE-009 now proves the actual heartbeat contract: HB32 at the protocol anchor, deterministic same-time reference, <10 ms stability, exactly-10-ms increment, skipped unobserved references, post-cutover anchor immutability, and absence of resident/worker/GitHub/third-party causality.

## Historical state

HB29, HB30, and HB31 remain immutable historical observations. Their persisted state is not current oscillator authority. HB32 begins the canonical protocol-anchor sequence at `2026-08-23T19:00:00.000Z`.

## Current state

```text
canonical protocol anchor: INSTALLED
canonical protocol derivation: INSTALLED
protocol heartbeat: ACTIVE_PROTOCOL_DERIVABLE
continuous process required: false
resident sampler: OPTIONAL / NOT AN ACTIVATION GATE
resident sampler receipt: OPTIONAL EVIDENCE ONLY
LIVE-009: HANDOFF_READY / UNBLOCKED
worker task-capable runtime: SEPARATE LANE
GitHub runtime authority: NONE
third-party runtime requirement: NONE
```

## Validation and completion

The remaining heartbeat-specific completion sequence is:

1. run exact-head deterministic validation including `tests/test_heartbeat_protocol_anchor.py`;
2. prove the canonical anchor derives HB32 and subsequent 10 ms references without persisted state;
3. persist terminal LIVE-009 verification evidence;
4. reconcile issues #12/#122 and any stale heartbeat documentation/registries;
5. propagate the corrected semantics to downstream heartbeat consumers.

Optional resident sampler installation is not in this completion predicate.

## Installed correction lineage

```text
45bece02a0bd887082b1936034c6a56dee705b11  canonical protocol anchor
25d258b99471636d37f2e0ee576bf3c73c934543  daemon-free canonical derivation
06ad548ec8ada7fa72cb28ece8a3ee39ccaf8544  protocol-anchor deterministic tests
41bfee42f0f078c4ba147dcfa9afd3941ef59e96  heartbeat semantics handoff correction
4f62de91a37481d292a22c8a1a56c3372675b4d3  live status correction
27b55cfb9071cc1ea14d15a91d1799045114a397  LIVE-009 registry release
a99bdbed2cfa36e3a02b7da76c6d580477f7c48b  LIVE-009 handoff correction
d83acd630b4ce732a4ad56848e3a2341ec6190b6  resident sampler registry reclassification
```

Do not manufacture sampler receipts. Do not make GitHub Actions runtime authority. Do not restore a resident-daemon prerequisite for heartbeat progression.

DO NOT ARCHIVE UNTIL EXACT-HEAD VALIDATION AND LIVE-009 TERMINAL RECONCILIATION COMPLETE.
