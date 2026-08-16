# Heartbeat Carrier Envelope Mirror Handoff

Updated: 2026-08-15T19:40:00-05:00

## Authority and goal

```text
goal_id: HEARTBEAT-CARRIER-ENVELOPE-183
originating_goal: calculate and maintain a growth-aware admissible heartbeat carrier envelope, including alternate phase references and observable waveform deviation
repository: StegVerse-Labs/.github
branch: main
canonical_issue: StegVerse-Labs/.github#183 CLOSED_COMPLETED
canonical_pr: StegVerse-Labs/.github#188 MERGED
merge_commit: 365b2835394523f46feb9b24633c265738af2a2a
implementation_claim: StegVerse-Labs/.github#184 COMPLETE_RELEASED
parent_semantics: StegVerse-Labs/.github#120 / docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
live_runtime_owner: StegVerse-Labs/.github#122 / HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
status: SOURCE_COMPLETE_VALIDATED_MERGED_RELEASED
```

This handoff is authoritative only for the bounded carrier-envelope source/schema extension. It does not own or grant the live producer/consumer switch, active heartbeat state, worker claims/fences/leases, resident processes, TV/TVC credentials, Master Records action authority, or StegBrain domain execution.

## Carrier model

Heartbeat remains the regulatory carrier/reference frame only.

The runtime calculates an admissible interval rather than relying on a universal fixed cadence:

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

The deterministic source selects a nominal operating point inside the interval with bounded reserve on both edges. The fixed 10 ms / nominal 100 Hz compatibility value is not normative unless the solver independently derives an interval containing that operating point.

## Capacity and expected growth

```text
L_design = L_current_max_simultaneous * (1 + growth_reserve_ratio)
```

Capacity includes current maximum simultaneous admitted signaling, return/deadline traffic, requested phase opportunities, and explicit reserve for expected architecture growth. Recalculation triggers are installed for admitted-signal changes, gate/passband changes, deadline/return-path changes, sustainable-capacity changes, reserve-threshold exhaustion, and persistent carrier deviation.

## Phase-capable carrier

The calculator emits a deterministic phase plan:

```text
Phi = {phi_0, phi_1, ... phi_n}
phi_0 = primary carrier phase
phi_i = alternate admitted reference opportunities
```

Alternate phases accommodate off-beat/intermittent subsystem signals without distorting the primary carrier or waiting an entire primary cycle. They are synchronization/reference opportunities only and never authority channels.

## Deviation observability

The source calculates:

```text
delta_f = f_observed - f_nominal
delta_phi = phi_observed - phi_expected
```

and evaluates deterministic frequency-drift, phase-error, and jitter tolerances. Observable zero-authority outcomes include:

```text
FREQUENCY_DEVIATION
PHASE_DEVIATION
JITTER_DEVIATION
ENVELOPE_RECALCULATION_REQUIRED
```

Carrier deviation is distinct from ordinary subsystem activity. StegBrain may observe these signals under its separate contract-evaluation authority; heartbeat itself does not remediate, schedule, route, claim, fence, or execute.

## Installed source surfaces

```text
schemas/heartbeat-carrier-envelope.schema.json
heartbeat_runtime/carrier_envelope.py
tests/test_heartbeat_carrier_envelope.py
schemas/heartbeat-carrier-observation.schema.json
control/runtime-separation-contract.json
heartbeat_runtime/runtime_separation.py
docs/HEARTBEAT_CARRIER_ENVELOPE_MIRROR_HANDOFF.md
```

## Validation evidence

```text
PR: #188
validated head: 8b626678cca19d166dd3c1625100f00673c50039
merge: 365b2835394523f46feb9b24633c265738af2a2a
Heartbeat Worker Project run: 31917660037 SUCCESS
complete deterministic repository suite: 281/281 PASS
carrier-envelope tests: 6/6 PASS
canonical JSON parse: PASS
executable handoff validation: PASS
heartbeat dry-run non-persistence: PASS
ephemeral projection validation: PASS
workflow non-authorizing proof: PASS
Organization Heartbeat Validation run: 31917660045 SUCCESS
```

Organization control-plane run `31917660057` failed before heartbeat-specific validation on an unrelated existing `TASK-2026-0004` unknown-flag set (`fail-closed-claim-gate`, `no-render`, `phone-sovereign`, `trade-readiness`, `tv-tvc-only`). It is explicitly not used as positive validation evidence for this goal. The complete deterministic repository suite and heartbeat-specific validation paths passed.

## Collision boundaries

```text
control/heartbeat-state.json: NOT MUTATED
active claims/fences/leases: NOT MUTATED
resident worker/carrier processes: NOT MUTATED
production carrier switch: OWNED BY #122
StegBrain contract evaluator: OWNED BY StegBrain#860
Master Records active remediation: PROHIBITED
TV/TVC credential authority: UNCHANGED
non-TV/TVC runtime secret/token authority: PROHIBITED
```

## Integration / propagation

The source/schema/calculator integration is complete. The separately claimed #122 live migration must consume the envelope calculator/schema when replacing the legacy combined producer. That live producer must emit carrier phases independently of worker/control-plane execution and observe residual frequency/phase/jitter without making those observations authority-bearing.

StegBrain#860 may consume deviation observations as evidence. Master Records remains passive custody only. Site/Publisher/wiki propagation is not required until the live carrier contract reaches its release/propagation gate.

## Completion accounting

```text
required developed files: 7
complete developed files: 7
scaffolding/stubs: 0
missing required source files: 0
source validation: COMPLETE
source integration: COMPLETE
live producer integration: PENDING / #122 MACHINE-OWNED
source claim: RELEASED
archive dependency from this source lane: NONE
```

## Next executable action

`StegVerse-Labs/.github#122` / `HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION` consumes the merged envelope implementation under its fresh authorized runtime claim and produces immutable live carrier evidence. This source lane must not compete with that claim.
