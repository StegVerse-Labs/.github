# Ecosystem receipt HB creation/recording stamp mirror handoff

Updated: 2026-09-20
Goal Task ID: `ECOSYSTEM-RECEIPT-HB-CREATION-RECORDING-STAMP-001`
Parent Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
COSV ID: `50000000100000`
Status: `ACTIVE / CHECKED OUT / CORE PROPAGATION IN PROGRESS`

## Goal

Every newly created StegVerse receipt must retain a canonical HeartBeat observation stamp at creation. When a receipt is first recorded by canonical Master Records, Master Records must independently sample and retain a second HB stamp for the recording event.

The two stamps answer different questions:

```text
hb_at_creation  = where the exact receipt originated in StegVerse continuity
hb_at_recording = where canonical Master Records first accepted that receipt
```

Neither stamp grants authority.

## Authority boundary

- HB: observation/correlation only.
- WorkerCoordinator: claim/fence authority where applicable.
- Interlock/InTr: transition authority.
- TV/TVC: credential authority where applicable.
- Master Records: custody/reconstruction authority only.

No HB value may admit, execute, authorize, repair, infer, or replace a transition.

## Canonical stamp fields

Both stages use `stegverse.receipt-heartbeat-stamp/v1` and retain:

- `stage`
- `heartbeat_id`
- `heartbeat_epoch`
- `heartbeat_generation`
- `reference_frame`
- `observed_at`
- `heartbeat_grants_authority=false`
- `authority_effect=NONE_OBSERVATION_ONLY`

## Work completed in this slice

- Registered this canonical child Goal.
- Added `control/receipt-hb-stamping-contract.json`.
- Began canonical Python state-transition receipt propagation: `workers/canonical_state_transition_custody.py::build_state_receipt` now samples `hb_at_creation` from the canonical independent oscillator.

## Required next propagation

1. Master Records canonical state-transition custody must independently sample and persist `hb_at_recording` on first record and return/reconstruct the same stamp on replay.
2. Site browser canonical custody must generate the same canonical `hb_at_creation` stamp before submission.
3. Inventory every remaining receipt emitter across StegVerse and propagate the same creation stamp contract; do not fabricate stamps for historical receipts.
4. Add fail-closed validation for new receipts only after each canonical emitter family is migrated, to avoid converting rollout order into false runtime failure.

## Evidence boundary

This goal does not claim ecosystem-wide completion until the emitter inventory is closed and every current receipt family is validated. Historical receipts remain valid historical evidence and are not retroactively stamped.
