# HB29 Worker Bootstrap Deadlock Mirror Handoff

This is a bounded subordinate handoff for the HB29→HB30 startup defect. It does not replace `docs/ORG_MIRROR_HANDOFF.md` or `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json`.

```text
goal_id: SHWP-HB29-WORKER-BOOTSTRAP-DEADLOCK-003
originating_goal: Fix the implementation defect preventing machine-owned HB29→HB30 transition execution.
repository: StegVerse-Labs/.github
branch: fix/hb29-worker-bootstrap-deadlock-220-v2
canonical_issue: #220
parent_runtime_handoff: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
organization_handoff: docs/ORG_MIRROR_HANDOFF.md
claim: control/session-implementation-claim-2026-08-18-hb29-worker-bootstrap-deadlock.json
state: IMPLEMENTED_PENDING_VALIDATION
credential_authority: TV/TVC
credential_requirement: NONE
non_tv_tvc_secret_or_token_allowed: false
github_token_runtime_authority: NONE
render_production_authority: NONE
```

## Defect

`WorkerCoordinator.cycle()` requires `control/heartbeat-carrier-runtime-state.json` before worker coordination begins. The first separated-v12 carrier state is HB30, and the canonical producer is `scripts/advance_heartbeat_transition.py`. The normal worker runtime entrypoint previously constructed `WorkerCoordinator` without first ensuring that HB30 existed. Therefore a fresh cutover state at immutable HB29 could fail before any worker execution path capable of producing HB30 was reached.

This is a startup/integration circularity, not a missing transition producer.

## Implemented repair

`scripts/run_worker_runtime.py` now performs a narrow initial-carrier bootstrap before WorkerCoordinator construction when and only when:

- `control/heartbeat-carrier-runtime-state.json` is absent;
- immutable `control/heartbeat-state.json` exists at epoch 29;
- the canonical `scripts/advance_heartbeat_transition.py` producer exists.

The wrapper delegates all state-transition semantics to the existing canonical producer. It forwards only a minimal non-secret environment allowlist. `GITHUB_TOKEN`, `GH_TOKEN`, TVC credential values, provider credentials, Render credentials, wallet credentials, and other secrets are not forwarded.

WorkerCoordinator is constructed only after a `CARRIER_TRANSITION_COMPLETE` receipt exists and an HB30+ separated carrier state is present. If transition execution fails, startup fails closed.

Existing HB30+ state is reused without re-running the bootstrap transition.

## Authority boundary

The repair does not mutate legacy HB29 directly; create another heartbeat, scheduler, WorkerCoordinator, claim, or fence; make GitHub Actions/Render/Vercel/Cloudflare production authority; grant credential, route, provider, wallet, trade, or custody authority; bypass TV/TVC; or make a third-party dependency primary.

The previously released iPhone capsule remains optional supporting physical-initiation evidence. It must not be a coding prerequisite for the machine-owned separated-v12 transition now that the canonical local worker-runtime entrypoint can bootstrap the first carrier state itself.

## Validation

Required exact-head validation:

```text
python -m unittest -q tests.test_hb29_worker_bootstrap_deadlock
python -m unittest -q tests.test_hb29_state_transition_carrier_contract
full heartbeat worker project validation
organization control-plane validation
```

Required predicates:

1. no carrier + immutable HB29 invokes the canonical producer and materializes HB30+;
2. existing HB30+ skips bootstrap;
3. missing/invalid HB29 fails closed;
4. failed producer execution prevents WorkerCoordinator startup;
5. credential-bearing environment variables are not forwarded;
6. legacy HB29 remains immutable;
7. no new authority surface is created.

## Integration and release

After exact-head validation passes, reconcile `docs/ORG_MIRROR_HANDOFF.md` and `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json`, merge the repair while current, release the bounded claim, close #220, and observe the next normal StegVerse-native worker-runtime execution for real HB30+ state and continuity receipt. Live HB30 is not claimed until those runtime surfaces are observed.

## Completion accounting

```text
developed_files: 4/4
scaffolding_or_stubs: 0
missing_required_files: 0
implementation: COMPLETE_ON_BRANCH
validation: 0/4 pending execution
integration: 0/1 pending merge
activation: 0/1 pending real HB30 observation
```
