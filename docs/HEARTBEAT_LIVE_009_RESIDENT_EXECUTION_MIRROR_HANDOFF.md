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

1. resolves the canonical resident runtime root using the sovereign installer default or an explicit `--runtime-root`;
2. invokes `scripts/install_sovereign_heartbeat_carrier.py --runtime-root <resident-root>` from the source checkout to materialize and activate the carrier-only native `engine_v13` service;
3. executes the first `run_worker_runtime.py --cycles 1` from and against the materialized resident runtime root under independent task-control authority;
4. executes `run_heartbeat_runtime.py --cycles 1` from and against the same resident root as an oscillator observation/sampler only;
5. executes the second resident-root worker cycle so the independently admitted LIVE-009 task can bind a fresh lawful fence and execute;
6. verifies all activation/carrier/observation/worker evidence from that same resident runtime root and fails closed unless terminal completion is present.

The runner does not fabricate a heartbeat epoch, claim, fence, lease, carrier observation, or worker response. It does not use a network fetch, hosted process service, GitHub runtime, Render, or non-TV/TVC credential.

### Resident-root correction

Direct inspection found that the original one-command runner installed the carrier into the resident runtime root but then executed both worker cycles, the carrier sample, and evidence verification against the source repository checkout. That path could not produce valid resident completion evidence even on a correctly admitted host.

Corrected on `main`:

```text
4098dab52d70e5922b980308ec8d00b9b537c443
  scripts/run_live_009_resident.py
  - resolves the actual resident runtime root
  - passes that root explicitly into carrier installation
  - runs worker(1) -> carrier(1) -> worker(1) from the materialized resident root
  - verifies terminal evidence from the resident root rather than the source checkout

ecae3d01f276ea07e3342e0132480ffc05d5e406
  tests/test_live_009_resident_runner.py
  - asserts installation originates from the source checkout
  - asserts all runtime cycles target the resident root
  - retains fail-closed activation and terminal-evidence checks
```

An independent local validation attempt could not clone the public repository because the available validation container had no DNS resolution for `github.com`. Therefore these exact commits are source-installed but this handoff does not claim an independently executed test PASS from that container. GitHub-hosted validation would be validation evidence only and would not count as resident runtime proof.

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
scripts/run_live_009_resident.py: INSTALLED / RESIDENT-ROOT CORRECTED
current source commit: 4098dab52d70e5922b980308ec8d00b9b537c443
tests/test_live_009_resident_runner.py: INSTALLED / RESIDENT-ROOT ASSERTIONS ADDED
current test commit: ecae3d01f276ea07e3342e0132480ffc05d5e406
independent exact-head test execution: UNAVAILABLE (validation container DNS failure)
resident execution: NOT YET OBSERVED
LIVE-009 terminal evidence: NOT YET OBSERVED
```

## Completion

This goal is terminal only after the one-command path runs on an admitted StegVerse resident host and all evidence above exists and verifies, followed by reconciliation of issue #122, LIVE-009 task/handoff state, carrier/observation evidence, and downstream worker-runtime separation state.

DO NOT ARCHIVE THIS SESSION — REQUIRED EXECUTION REMAINS IN AN ACTIVE DEPENDENCY LANE.
