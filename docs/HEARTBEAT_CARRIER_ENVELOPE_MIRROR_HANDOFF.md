# Heartbeat Carrier Envelope Mirror Handoff

Updated: 2026-08-15T19:36:00-05:00

## Authority and goal

```text
goal_id: HEARTBEAT-CARRIER-ENVELOPE-183
originating_goal: calculate and maintain a growth-aware admissible heartbeat carrier envelope, including alternate phase references and observable waveform deviation
repository: StegVerse-Labs/.github
branch: feat/heartbeat-carrier-envelope-phase-183-final
canonical_issue: StegVerse-Labs/.github#183
implementation_claim: StegVerse-Labs/.github#184
parent_semantics: StegVerse-Labs/.github#120 / docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
live_runtime_owner: StegVerse-Labs/.github#122 / HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
```

This handoff is authoritative only for the bounded carrier-envelope source/schema extension. It does not own or grant the live producer/consumer switch, active heartbeat state, worker claims/fences/leases, resident processes, TV/TVC credentials, Master Records action authority, or StegBrain domain execution.

## Carrier model

Heartbeat remains the regulatory carrier/reference frame only.

The runtime must calculate an admissible interval rather than relying on a universal fixed cadence:

```text
I_f = [f_min, f_max]

f_min = max(
  admitted gate/passband lower bounds,
  deadline/return-reference lower bounds,
  growth-adjusted simultaneous throughput floor
)

f_max = min(
  admitted gate/passband upper bounds,
  locally sustainable deterministic carrier-production ceiling
)

require f_min <= f_max
```

A nominal operating point must remain inside the interval with bounded reserve on both edges. The current fixed 10 ms / nominal 100 Hz compatibility value is not normative unless the solver independently derives an interval containing that operating point.

## Capacity and expected growth

```text
L_design = L_current_max_simultaneous * (1 + growth_reserve_ratio)
```

Capacity calculation includes current maximum simultaneous admitted signaling, return/deadline traffic, requested phase opportunities, and explicit reserve for expected architecture growth. Recalculation is required when the admitted signal set, gate/passband, deadline/return path, sustainable carrier capacity, reserve threshold, or persistent carrier deviation changes.

## Phase-capable carrier

The carrier may expose a calculated phase plan:

```text
Phi = {phi_0, phi_1, ... phi_n}
phi_0 = primary carrier phase
phi_i = alternate admitted reference opportunities
```

Alternate phases exist to accommodate off-beat/intermittent subsystem signals without distorting the primary carrier or waiting for an entire primary cycle. They are synchronization/reference opportunities only and never authority channels.

## Deviation observability

The carrier monitor may calculate:

```text
delta_f = f_observed - f_nominal
delta_phi = phi_observed - phi_expected
```

and compare them with deterministic frequency-drift, phase-error, and jitter tolerances. Observable outcomes include:

```text
FREQUENCY_DEVIATION
PHASE_DEVIATION
JITTER_DEVIATION
ENVELOPE_RECALCULATION_REQUIRED
```

Carrier deviation is distinct from ordinary subsystem activity. StegBrain may observe these signals under its separate contract-evaluation authority; heartbeat itself does not remediate, schedule, route, claim, fence, or execute.

## Implemented source surfaces

```text
schemas/heartbeat-carrier-envelope.schema.json
heartbeat_runtime/carrier_envelope.py
tests/test_heartbeat_carrier_envelope.py
schemas/heartbeat-carrier-observation.schema.json
control/runtime-separation-contract.json
heartbeat_runtime/runtime_separation.py
docs/HEARTBEAT_CARRIER_ENVELOPE_MIRROR_HANDOFF.md
```

## Collision boundaries

```text
control/heartbeat-state.json: DO NOT MUTATE
active claims/fences/leases: DO NOT MUTATE
resident worker/carrier processes: DO NOT MUTATE
production carrier switch: OWNED BY #122
StegBrain contract evaluator: OWNED BY StegBrain#860
Master Records active remediation: PROHIBITED
TV/TVC credential authority: UNCHANGED
non-TV/TVC runtime secret/token authority: PROHIBITED
```

## Validation requirements

```text
static/schema validity
unit tests for interval derivation
unit tests for impossible interval fail-closed
unit tests for growth reserve and multi-phase plan
unit tests for frequency/phase/jitter deviation detection
unit tests proving zero authority
existing runtime-separation tests remain PASS
repository workflow PASS before merge
```

## Integration / propagation

After source validation and merge, #122 must consume the envelope calculator/schema during the separately claimed live producer migration. StegBrain#860 may consume deviation observations as evidence. Master Records remains passive custody only. Site/Publisher/wiki propagation is not required until the live carrier contract reaches its release/propagation gate.

## Completion accounting

```text
required developed files: 7
source files implemented: 7
scaffolding/stubs: 0
missing required source files: 0
validation: pending hosted repository validation
integration: source/schema integration complete; live producer integration remains #122-owned
archive condition: merge + validation + claim release + #122 continuation recorded
```
