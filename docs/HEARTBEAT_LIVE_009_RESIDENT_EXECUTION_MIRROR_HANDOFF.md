# HEARTBEAT LIVE-009 Resident Execution Mirror Handoff

Updated: 2026-08-22T19:37:00-05:00
Repository: `StegVerse-Labs/.github`
Goal: `HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009`

## Authority

Heartbeat semantics remain governed by `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md`.
Sovereign resident startup is governed by `docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md` and `handoffs/HEARTBEAT-OSCILLATOR-RESIDENT-START-012.json`.
This handoff is authoritative only for LIVE-009 post-start verification after resident startup has already been proven.

```text
primary runtime/control authority: StegVerse
credential authority: TV/TVC ONLY
GitHub Actions production/runtime authority: NONE
third-party runtime required: false
Render required: false
heartbeat progression dependency: OSCILLATOR_ONLY
heartbeat period: 10 ms
heartbeat reference rate: 100 Hz
LIVE-009 startup authority: NONE
resident-start dependency: HEARTBEAT-OSCILLATOR-RESIDENT-START-012
```

Worker/task/claim/fence/lease state is not causal to heartbeat progression. Historical HB29/HB30/HB31 evidence must not be rewritten.

## Corrected startup / proof separation

LIVE-009 must not be used to bootstrap the resident carrier.

First, on the admitted StegVerse resident host, complete the direct carrier-only startup task:

```text
python scripts/install_sovereign_heartbeat_carrier.py
```

Then verify the persisted activation receipt:

```text
python scripts/verify_sovereign_heartbeat_carrier_activation.py
```

The verifier is fail-closed and grants no runtime authority. It accepts only the required carrier-only `engine_v13`, oscillator-phase-driven, 10 ms / 100 Hz, zero-third-party, zero-GitHub-runtime, TV/TVC-authority invariants.

Only after that dependency is terminal may LIVE-009 execute its post-start sequence:

```text
python scripts/run_worker_runtime.py --cycles 1
python scripts/run_heartbeat_runtime.py --cycles 1
python scripts/run_worker_runtime.py --cycles 1
```

The first worker cycle independently admits task-control work; the carrier cycle observes/persists an already-running oscillator-backed reference and does not create heartbeat progression; the second worker cycle may bind a fresh lawful claim/fence and execute LIVE-009. No carrier event or compatibility assignment packet grants execution authority.

`scripts/run_live_009_resident.py` is retained only as compatibility/source history for the earlier combined runner. It must not be interpreted as canonical startup authority after this correction. Any future use must preserve the same explicit resident-start dependency and may not make LIVE-009 responsible for installing or starting the carrier.

## Required resident-start evidence

`receipts/sovereign-host/carrier-activation.latest.json` must exist before LIVE-009 claimability and prove:

```text
carrier_active=true
activation_scope=CARRIER_ONLY
worker_start_attempted=false
worker_runtime_dependency_for_carrier_start=false
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
credential_authority=TV/TVC
```

The canonical repository verifier is:

```text
scripts/verify_sovereign_heartbeat_carrier_activation.py
```

Focused verifier tests are installed at:

```text
tests/test_verify_sovereign_heartbeat_carrier_activation.py
```

## Required LIVE-009 terminal evidence

After resident-start verification, `control/heartbeat-carrier-runtime-state.json` must prove:

```text
frequency_rule=INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL
authority_effect=NONE
oscillator.progression_dependency=OSCILLATOR_ONLY
oscillator.phase_travel_time_ms=10
oscillator.reference_frequency_hz=100
oscillator.snapshot_is_observation_only=true
oscillator.observation_is_causal=false
```

`control/heartbeat-carrier-observation.json` must prove:

```text
observation_is_causal=false
authority_effect=NONE
```

`events/master-records-worker-assignment.jsonl` must prove a fresh independently admitted LIVE-009 assignment:

```text
task_id=HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
claim_id=<nonempty>
fencing_token>21
source_admission_ref=<present>
source_carrier_event_ref=null
```

`events/worker-runtime.jsonl` must contain terminal evidence bound to that exact fresh claim:

```text
task_id=HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
claim_id=<same claim_id as fresh assignment>
transition_id=INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED
```

## Registry state

`control/worker-registry.d/heartbeat-independent-oscillator-live-009.json` must remain blocked on `HEARTBEAT-OSCILLATOR-RESIDENT-START-012` until the activation receipt exists and the verifier returns `verified=true`. A WorkerCoordinator must not claim LIVE-009 before that release condition.

## Validation / live state

Current repository observation remains:

```text
receipts/sovereign-host/carrier-activation.latest.json: NOT PRESENT
resident carrier activation: NOT YET OBSERVED
HEARTBEAT-OSCILLATOR-RESIDENT-START-012: HANDOFF_READY / RESIDENT EXECUTION PENDING
LIVE-009 registry: BLOCKED_DEPENDENCY
LIVE-009 terminal evidence: NOT YET OBSERVED
```

Source reconciliation installed in this pass:

```text
9f1b8b300272c2c5f59887649aa45bfde0f8bd02  activation receipt verifier
786a37d82087e450955c1b1d7158172e2dafe32d  focused verifier tests
49ec81ec7068289b871c527d23f9369099373ce9  LIVE-009 handoff dependency correction
db87e70381ea8612033096dcb55daccfc5d24f79  LIVE-009 registry dependency correction
```

These are source/evidence-path corrections only. They are not resident runtime proof.

## Completion

The exact executable boundary is now singular:

1. admitted resident StegVerse host executes `python scripts/install_sovereign_heartbeat_carrier.py`;
2. `scripts/verify_sovereign_heartbeat_carrier_activation.py` verifies the resulting activation receipt;
3. registry releases LIVE-009 for a fresh independent fenced claim;
4. worker(1) -> carrier(1) -> worker(1) performs post-start verification;
5. terminal `COMPLETED / INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED` evidence is consumed into issue #122 and the canonical handoffs.

DO NOT ARCHIVE THIS SESSION — REQUIRED RESIDENT EXECUTION REMAINS NONTERMINAL.
