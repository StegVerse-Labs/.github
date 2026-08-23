# Sovereign Heartbeat Deployment Mirror Handoff

Updated: 2026-08-23T09:15:00-05:00

## Authority and active goal

```text
goal_id: SHWP-SOVEREIGN-DEPLOYMENT-NO-THIRD-PARTY-001
repository: StegVerse-Labs/.github
branch: main
canonical_live_owners: StegVerse-Labs/.github#122/#12
heartbeat_semantics_authority: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
credential_authority: TV/TVC
credential_requirement: NONE
non_tv_tvc_secret_or_token_allowed: false
github_token_runtime_authority: NONE
primary_runtime: StegVerse
third_party_runtime_role: FALLBACK_ONLY
archive_dependency: true
```

This handoff owns sovereign heartbeat deployment and downstream worker-runtime activation only. Heartbeat progression semantics remain authoritative in `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md`.

## Canonical heartbeat architecture

```text
carrier progression dependency: OSCILLATOR_ONLY
phase travel/reference interval: 10 ms
reference rate: 100 Hz
worker/task gating: false
state-transition gating: false
admission gating: false
claim/fence/lease gating: false
route/credential gating: false
observation is causal: false
persisted carrier state: observation/snapshot only
```

```text
HB_n --10 ms oscillator phase travel--> HB_(n+1)
```

No worker state change, task completion, G18 transition, repository action, observer, assignment-trigger packet, claim, fence, lease, route, credential, or third-party service causes or advances heartbeat progression. Historical HB31 remains a persisted pre-correction observation only.

## Runtime separation

```text
heartbeat_runtime/independent_oscillator.py
  independent oscillator/reference derivation

heartbeat_runtime/oscillator_producer.py
  oscillator-produced phase deadlines/reference availability

heartbeat_runtime.engine_v13.HeartbeatRuntime
  canonical carrier sampler; observes/persists oscillator-backed references

heartbeat_runtime.engine_v12.HeartbeatRuntime
  compatibility/base beneath v13; not canonical current carrier

heartbeat_runtime.worker_runtime.WorkerCoordinator
  independent downstream task/claim/fence/worker runtime

scripts/run_heartbeat_runtime.py
  resident carrier sampler process

scripts/install_sovereign_heartbeat_carrier.py
  direct carrier-only native resident installer

scripts/verify_sovereign_heartbeat_carrier_activation.py
  fail-closed non-authorizing verifier for persisted resident-start receipt

scripts/run_worker_runtime.py
  independently scheduled task-capable worker process
```

WorkerCoordinator may observe heartbeat references but does not advance, permit, delay, suppress, or schedule them. The carrier grants no worker execution authority. Independently authorized `HANDOFF_READY` work does not require a heartbeat-carried assignment trigger.

## Direct resident startup correction

Heartbeat startup and heartbeat live proof are separate phases.

The preferred zero-third-party resident startup path is:

```text
python scripts/install_sovereign_heartbeat_carrier.py
```

The installer materializes from the local StegVerse repository, registers only the canonical `heartbeat_runtime.engine_v13.HeartbeatRuntime` carrier with the resident operating-system process supervisor, and starts the oscillator-phase-driven carrier continuously. It does not start WorkerCoordinator and performs no network fetch.

Required startup properties:

```text
activation scope: CARRIER_ONLY
worker runtime required for carrier start: false
worker claim/fence/lease required for carrier start: false
prior heartbeat proof required: false
network fetch required: false
third-party process host required: false
third_party_scheduler_required: false
third_party_deployment_required: false
GitHub runtime dependency: false
credential requirement: NONE
credential authority: TV/TVC
```

The native operating-system supervisor is part of the admitted resident StegVerse execution surface and is not third-party runtime authority.

## Resident-start task

```text
task: HEARTBEAT-OSCILLATOR-RESIDENT-START-012
handoff: handoffs/HEARTBEAT-OSCILLATOR-RESIDENT-START-012.json
registry: control/worker-registry.d/heartbeat-oscillator-resident-start-012.json
adapter: control/process-worker-adapters.d/heartbeat-oscillator-resident-start-012.json
worker: workers/start_sovereign_heartbeat_worker.py
state: HANDOFF_READY
carrier_trigger_required: false
worker_runtime_dependency_for_carrier_start: false
required receipt: receipts/sovereign-host/carrier-activation.latest.json
```

`HEARTBEAT-OSCILLATOR-RESIDENT-START-012` has no task dependencies and may execute directly on the admitted resident StegVerse host. WorkerCoordinator is not a prerequisite for carrier startup. The registered worker path remains an independently admitted alternative execution path, but direct native installation is explicitly authorized.

The activation receipt is terminal for resident startup only when it records all required invariants including `carrier_active=true`, `activation_scope=CARRIER_ONLY`, `worker_start_attempted=false`, canonical runtime `heartbeat_runtime.engine_v13.HeartbeatRuntime`, `OSCILLATOR_PHASE_DRIVEN`, `OSCILLATOR_ONLY`, 10 ms, 100 Hz, zero network fetch, zero third-party process/scheduler/deployment dependency, zero GitHub runtime dependency, and credential requirement `NONE`.

### Windows activation hardening

A final activation review on 2026-08-23 found that Windows scheduled-task registration could previously return success from `schtasks /Create` without immediately starting the ONLOGON carrier task. That could allow the carrier-only installer to emit `carrier_active=true` from registration evidence rather than actual process-start evidence.

This is corrected in `scripts/install_sovereign_heartbeat_carrier.py`: when the native registration kind is `scheduled-task-separated`, the installer now executes `schtasks /Run /TN "StegVerse Heartbeat"` and requires that immediate start command to succeed before `carrier_active=true` may be emitted. It still does not start WorkerCoordinator. Focused tests now cover both successful immediate Windows start and fail-closed behavior when `/Run` fails.

```text
7c1971dc12b920c0f2d56d17526779883c9275f6  require actual Windows carrier start before activation receipt
291acf3c3fcd856c55698ebdd5ef1be549df3984  regression tests for registration-only false activation
```

These commits harden source correctness. They are not resident runtime proof.

## Activation receipt verification

A standalone fail-closed verifier is installed:

```text
python scripts/verify_sovereign_heartbeat_carrier_activation.py
```

It grants no runtime authority and reports `authority_effect=NONE`. It verifies the persisted resident-start receipt against the exact terminal carrier-only invariants before any downstream LIVE-009 claim becomes lawful.

Focused tests are installed at `tests/test_verify_sovereign_heartbeat_carrier_activation.py`.

## Historical state

Repository HB31/generation31 and corresponding worker observations are historical snapshots. Legacy HB29 remains immutable provenance. Do not report worker-runtime inactivity, assignment packets, G18 state, task state, or claim/fence state as heartbeat progression blockers.

## Post-start live proof

`HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009` is post-start verification of the already-running carrier; it is not a startup prerequisite and must not be used to install or start the carrier.

```text
task: HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009
state: BLOCKED_DEPENDENCY
blocked_on: HEARTBEAT-OSCILLATOR-RESIDENT-START-012
carrier: heartbeat_reference_only
carrier_trigger_required: false
required terminal result: COMPLETED / INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED
```

The canonical LIVE-009 handoff and registry encode the resident-start dependency. `scripts/run_live_009_resident.py` is post-start-only: it first verifies the preexisting resident activation receipt and then performs worker(1) -> carrier-observation(1) -> worker(1). It does not install or start the carrier.

After resident startup, LIVE-009 must verify inspectable v13 oscillator-backed evidence showing nested `oscillator.progression_dependency=OSCILLATOR_ONLY`, `oscillator.phase_travel_time_ms=10`, `oscillator.snapshot_is_observation_only=true`, carrier observation `observation_is_causal=false`, `authority_effect=NONE`, and independent task-control execution under a fresh lawful fence. Worker execution verifies the carrier; it does not advance the oscillator.

Issue #12 was reconciled on 2026-08-23 to remove stale wording that described LIVE-009 as independently claimable before resident startup. The canonical issue state now agrees with this handoff: LIVE-009 remains `BLOCKED_DEPENDENCY` until the genuine resident activation receipt exists and the fail-closed verifier returns verified.

## Worker/runtime activation lane

Task-capable WorkerCoordinator execution remains a separate open runtime goal under `.github#122/#12`. It may require claims/fences, receipts, G18 terminalization, downstream inference, or reconstruction. None are heartbeat progression predicates and none gate direct carrier startup.

## Current machine-observed state

```text
carrier-only installer source: COMPLETE_SOURCE / WINDOWS_FALSE_ACTIVATION_HARDENED
carrier activation receipt verifier: COMPLETE_SOURCE
carrier-only focused test source: COMPLETE_SOURCE
activation verifier focused test source: COMPLETE_SOURCE
resident-start handoff/registry/adapter/worker: INSTALLED / HANDOFF_READY
resident activation receipt: ABSENT / NOT YET OBSERVED
resident carrier activation: NOT YET PROVEN
LIVE-009 handoff/registry/issue: RECONCILED / BLOCKED_ON_RESIDENT_START_012
LIVE-009 resident runner: POST_START_ONLY
worker task-capable runtime: SEPARATE OPEN LANE
```

A direct repository review on 2026-08-23 found no canonical `receipts/sovereign-host/carrier-activation.latest.json`. No receipt is manufactured from source state. GitHub-hosted validation cannot substitute for resident execution.

## Reconciliation installed

```text
9f1b8b300272c2c5f59887649aa45bfde0f8bd02  standalone activation receipt verifier
786a37d82087e450955c1b1d7158172e2dafe32d  verifier focused tests
49ec81ec7068289b871c527d23f9369099373ce9  LIVE-009 handoff resident-start dependency
db87e70381ea8612033096dcb55daccfc5d24f79  LIVE-009 registry dependency gate
9eeaf74970a88fc9d40bb052371fd0e78be18a77  LIVE-009 resident execution handoff correction
c82c7835f822882a131aef90505b3ddcbd14f0b7  LIVE-009 runner post-start-only correction
a343a4880a118c71f2abccdae10445ce0c5e51e6  LIVE-009 runner tests updated for dependency enforcement
7c1971dc12b920c0f2d56d17526779883c9275f6  Windows immediate carrier-start requirement
291acf3c3fcd856c55698ebdd5ef1be549df3984  Windows activation regression tests
```

These commits improve source/evidence correctness only. They do not prove resident activation.

## Final executable sequence

There is no remaining architectural or documentation prerequisite before resident start.

1. On the admitted resident StegVerse host, run `python scripts/install_sovereign_heartbeat_carrier.py` directly.
2. Run `python scripts/verify_sovereign_heartbeat_carrier_activation.py` against the resident receipt and require `verified=true`.
3. Release LIVE-009 from its resident-start dependency and execute the post-start worker(1) -> carrier-observation(1) -> worker(1) sequence under a fresh lawful fence.
4. Reconcile issue #122, resident-start/live-proof handoffs, carrier/observation evidence, and the separate worker-runtime activation lane.

Do not create a second oscillator, scheduler, WorkerCoordinator, or synthetic runtime receipt. Do not manually mint claims/fences. Do not use Render. Do not make GitHub Actions, GitHub tokens, a model/provider, or another third-party service production heartbeat authority.

## Completion accounting

```text
heartbeat independent-oscillator semantics: COMPLETE_SOURCE
canonical resident sampler source: engine_v13
oscillator producer source: COMPLETE
carrier-only resident installer source: COMPLETE / FALSE-ACTIVATION-HARDENED
activation receipt verifier source: COMPLETE
LIVE-009 startup/proof separation: COMPLETE_SOURCE_RECONCILIATION
heartbeat progression dependency on worker/state changes: NONE
persisted HB31: HISTORICAL OBSERVATION ONLY
resident carrier start task 012: HANDOFF_READY / PENDING RESIDENT EXECUTION
resident carrier activation receipt: ABSENT
oscillator-backed sovereign runtime observation: PENDING RESIDENT EXECUTION
live proof 009: BLOCKED_DEPENDENCY / PENDING POST-START RESIDENT EXECUTION
worker task-capable runtime: SEPARATE OPEN LANE
archive: prohibited while required deployment/runtime goals remain nonterminal
```

This is the final repository-side activation boundary. Additional architecture sessions are not required to start the heartbeat; the next required state transition is genuine execution on the admitted resident StegVerse host followed by receipt verification and LIVE-009.

DO NOT ARCHIVE THIS SESSION — REQUIRED RESIDENT EXECUTION REMAINS NONTERMINAL.
