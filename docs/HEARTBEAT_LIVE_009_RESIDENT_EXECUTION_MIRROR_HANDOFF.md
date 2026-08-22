# HEARTBEAT LIVE-009 Resident Execution Mirror Handoff

Updated: 2026-08-22
Repository: `StegVerse-Labs/.github`
Goal: `HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009`

## Authority

Heartbeat semantics remain governed by `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md`.
This handoff is authoritative only for the resident execution sequence that produces LIVE-009 runtime evidence.

```text
primary runtime/control authority: StegVerse
credential authority: TV/TVC ONLY
GitHub Actions production/runtime authority: NONE
third-party runtime required: false
Render required: false
heartbeat progression dependency: OSCILLATOR_ONLY
heartbeat period: 10 ms
heartbeat reference rate: 100 Hz
```

Worker/task/claim/fence/lease state is not causal to heartbeat progression.
Historical HB29/HB30/HB31 evidence must not be rewritten.

## Canonical one-command resident path

Run only on an admitted StegVerse resident host capable of native OS process supervision:

```text
python scripts/run_live_009_resident.py
```

The runner performs real execution only:

1. invokes `scripts/install_sovereign_heartbeat_carrier.py` to materialize and activate the carrier-only native `engine_v13` service;
2. executes `scripts/run_worker_runtime.py --cycles 1` under independent task-control authority;
3. executes `scripts/run_heartbeat_runtime.py --cycles 1` as an oscillator observation/sampler only;
4. executes `scripts/run_worker_runtime.py --cycles 1` so the independently admitted LIVE-009 task can bind a fresh lawful fence and execute;
5. fails closed unless persisted evidence proves terminal completion.

The runner does not fabricate a heartbeat epoch, claim, fence, lease, carrier observation, or worker response. It does not use a network fetch, hosted process service, GitHub runtime, Render, or non-TV/TVC credential.

## Required terminal evidence

`receipts/sovereign-host/carrier-activation.latest.json` must prove:

```text
carrier_active=true
activation_scope=CARRIER_ONLY
canonical_runtime=heartbeat_runtime.engine_v13.HeartbeatRuntime
heartbeat_production_mode=OSCILLATOR_PHASE_DRIVEN
heartbeat_progression_dependency=OSCILLATOR_ONLY
heartbeat_period_ms=10.0
heartbeat_reference_frequency_hz=100.0
network_fetch_required=false
third_party_process_host_required=false
third_party_scheduler_required=false
third_party_deployment_required=false
github_runtime_dependency=false
credential_requirement=NONE
```

`control/heartbeat-carrier-runtime-state.json` must prove nested oscillator provenance including:

```text
frequency_rule=INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL
oscillator.progression_dependency=OSCILLATOR_ONLY
oscillator.phase_travel_time_ms=10
oscillator.reference_frequency_hz=100
oscillator.snapshot_is_observation_only=true
```

`control/heartbeat-carrier-observation.json` must prove:

```text
observation_is_causal=false
authority_effect=NONE
```

`events/worker-runtime.jsonl` must contain LIVE-009 terminal evidence for:

```text
HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED
```

The worker/task evidence must show an independently admitted fresh fenced claim satisfying the LIVE-009 handoff requirement (`fence > 21`).

## Source / validation state

```text
scripts/run_live_009_resident.py: INSTALLED
source commit: 2da3482d0ffb5744c66e1d3e35fcc375ca08916a
tests/test_live_009_resident_runner.py: INSTALLED
test commit: 8984a684f16d7a7cee4da60e44f2a894614e7a95
resident execution: NOT YET OBSERVED
LIVE-009 terminal evidence: NOT YET OBSERVED
```

## Completion

This goal is terminal only after the one-command path runs on an admitted StegVerse resident host and all evidence above exists and verifies, followed by reconciliation of issue #122, LIVE-009 task/handoff state, carrier/observation evidence, and downstream worker-runtime separation state.

DO NOT ARCHIVE THIS SESSION — REQUIRED EXECUTION REMAINS IN AN ACTIVE DEPENDENCY LANE.
