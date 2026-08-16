# Heartbeat External Timing Match Mirror Handoff

Updated: 2026-08-15T21:22:00-05:00

## Authority and goal

```text
goal_id: HEARTBEAT-EXTERNAL-TIMING-MATCH-191
originating_session_goal: Generalize clock and waveform matching when StegVerse establishes a connection with any exterior system while preserving a constant StegVerse logical heartbeat and treating min/max as workload-health bounds.
repository: StegVerse-Labs/.github
branch: feat/external-timing-match-191
canonical_issue: StegVerse-Labs/.github#192
parent_runtime_owner: StegVerse-Labs/.github#122 / HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION
canonical_task_owner: this bounded source/schema lane until merge/release; #122 remains live producer owner
implementation_claim: CLAIMED_FOR_IMPLEMENTATION
validation_claim: SAME_BOUNDED_BRANCH_AFTER_IMPLEMENTATION
claim_created_at: 2026-08-15T21:22:00-05:00
claim_expires_at: 2026-08-15T23:22:00-05:00 unless renewed with execution evidence
claim_release_condition: source/schema/matcher/tests/integration contract merged or claim explicitly released/superseded
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
render_dependency: PROHIBITED
```

## Canonical semantics

- The StegVerse logical heartbeat cadence is constant after timing-profile selection/lock.
- Heartbeat min/max are workload-health bounds per pulse, not an allowable variable heartbeat-frequency band.
- Exterior timing sources are observed and profiled; they never become StegVerse authority.
- S/NS topology is explicit authenticated metadata and is never inferred from carrier frequency or waveform.
- Phase/waveform matching may assist synchronization, rapid recognition, drift detection, and bridging, but grants no execution, credential, claim, routing, custody, governance, consent, intent, or semantic authority.
- Bounded re-profile/re-lock is allowed only when the exterior timing source materially changes; it must not silently mutate the selected StegVerse logical cadence.

## Authoritative source surfaces

```text
docs/HEARTBEAT_EXTERNAL_TIMING_MATCH_MIRROR_HANDOFF.md
schemas/external-timing-capability.schema.json
heartbeat_runtime/external_timing_match.py
control/external-timing-match-contract.json
tests/test_external_timing_match.py
```

## Required behavior

1. Normalize an arbitrary exterior timing observation into an authority-neutral capability profile containing clock-source class, monotonic/timing resolution, wakeup/timer floor, observed jitter, sustainable fixed logical period, phase capacity, waveform family/signature, and workload capacity.
2. Select a single fixed StegVerse logical period compatible with that profile and preserve it while locked.
3. Compute deterministic clock offset, phase error, jitter, drift, and lock/loss-of-lock observations without conflating timing deviation with subsystem workload.
4. Maintain a separate workload-health envelope per pulse with UNDERLOAD, NORMAL, ELEVATED, SATURATED, and OVERLOADED states.
5. Permit adapters for OS clocks, hardware clocks, network time sources, buses, radios, sensors, industrial controllers, BCI/device interfaces, and other exterior systems through the same matching contract.
6. Emit no authority-bearing result.

## Cross-repository consumers

- `StegVerse-Labs/.github#122`: production carrier/runtime consumption after this source lane is merged and released.
- `StegVerse-Labs/StegBrain#860`: may observe typed timing deviation under separate contract-evaluation authority.
- `StegVerse-Labs/StegNeuro`: BCI consumer notation exists in `STEGNEURO_MIRROR_HANDOFF.md` and `research/bci-evidence-consumer.json`; timing matching may support cross-device temporal normalization and closed-loop timing evidence but does not grant neural READ/WRITE authority.
- `StegVerse-org/StegVerse-SDK#13`: may consume generalized device timing capability contracts where physical-device discovery requires them; no duplicate timing authority is created.

## Collision boundaries

```text
control/heartbeat-state.json: DO NOT MUTATE
active claims/fences/leases: DO NOT MUTATE
resident heartbeat/carrier processes: DO NOT MUTATE
production carrier switch: OWNED BY #122
TV/TVC protected values: DO NOT READ/WRITE HERE
provider/model/wallet state: OUT OF SCOPE
Master Records custody mutation: PROHIBITED
```

## Validation commands

```text
python -m unittest -v tests.test_external_timing_match
python -m compileall -q heartbeat_runtime
python - <<'PY'
import json
for p in ('schemas/external-timing-capability.schema.json','control/external-timing-match-contract.json'):
    json.load(open(p, encoding='utf-8'))
print('EXTERNAL_TIMING_JSON_PASS')
PY
```

## Integration and propagation obligations

- #122 must explicitly consume this contract before live carrier migration can claim generalized exterior timing compatibility.
- Existing `heartbeat_runtime/carrier_envelope.py` is a pre-clarification compatibility implementation whose frequency-envelope semantics must not be treated as normative for the fixed-cadence architecture after this goal merges.
- Site/Publisher/wiki propagation is not required until the live carrier contract reaches its release/publication gate.

## Session-consolidation state

```text
MCP production-artifact execution: canonical continuation remains StegVerse-org/StegVerse-SDK/tasks/SDK-MCP-CANONICAL-VALIDATION-009.json; this lane does not duplicate it.
Sovereign local model/runtime discovery-launch-proof: COMPLETE_RELEASED in StegVerse-002/micro-node-runtime under docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md and prior PRs #28/#29; do not duplicate.
Formal local structured-generation model development: COMPLETE_VALIDATED_MERGED in StegVerse-002/micro-node-runtime PRs #33/#34; live activation remains in existing .github#144/TVC/LLM-adapter chain.
Trade/wallet work: separate canonical StegFin sessions/workers; no duplicate wallet implementation from this lane.
StegNeuro BCI timing notation: COMPLETE in StegVerse-Labs/StegNeuro commits f3cac1987421088cd37b720616c0d8fd79c2e689 and 56ac0e2f7cbb6eedf43598d900510cb8c26bec9a.
```

## Completion accounting

```text
required developed files: 5
complete developed files: 1
scaffolding/stubs: 0
missing required files: 4
validation: 0/4
integration: 0/2
goal_activation: 10%
session_consolidation: 4/5 session goals durably transferred or complete; this source implementation remains active
```

## Archive conditions

This bounded source lane is archive-safe only after the implementation claim is released, all five authoritative surfaces are merged or superseded, validation evidence is retained, #122 has an explicit consumption reference, and no unique session requirement remains only in chat.

## Next executable action

Implement `heartbeat_runtime/external_timing_match.py`, schema, control integration contract, and focused tests on this branch; run the strongest available no-token validation; merge/release if green; then transfer live runtime consumption to #122.
