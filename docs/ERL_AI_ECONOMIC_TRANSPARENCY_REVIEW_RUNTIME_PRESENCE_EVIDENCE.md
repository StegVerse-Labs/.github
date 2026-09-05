# ERL AI Economic Transparency Review — Runtime Presence Evidence

Canonical reviewer handoff: `docs/ERL_AI_ECONOMIC_TRANSPARENCY_REVIEW_WORKER_MIRROR_HANDOFF.md`

Task: `SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001`

## 2026-09-04 carrier-owned presence emission repair

Live source inspection found that the canonical runtime-presence projector was source-complete and the carrier already supervised WorkerCoordinator presence, but no durable presence projection was emitted automatically from that existing supervision path.

StegVerse-Labs/.github PR #1001 / merge `5187346ce0c1c8da144c1a3743ff063c09501af4` closes that gap without adding a scheduler or authority plane:

- `scripts/repair_resident_worker_presence.py` now persists `receipts/sovereign-host/runtime-presence.latest.json` using `heartbeat_runtime/runtime_presence_projection.py` after reusing or repairing WorkerCoordinator presence;
- the carrier-owned supervision receipt binding was corrected from obsolete `heartbeat_runtime.engine_v12.HeartbeatRuntime` to canonical `heartbeat_runtime.engine_v13.HeartbeatRuntime`;
- the projector accepts `receipts/sovereign-host/ephemeral-process.latest.json` only as a bounded fallback when carrier and worker are active, the v13/WorkerCoordinator bindings match, no third-party process host is required, HB grants no execution authority, and the supervision authority effect is `NONE_SUPERVISION_ONLY`;
- `present_worker_runtime_observed=true` still requires a fresh task-capable `worker-runtime-state.json:last_cycle_at`; supervision receipt presence alone is insufficient;
- the shared `management/HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT.json` now registers `receipts/sovereign-host/runtime-presence.latest.json` as the canonical resident-runtime-presence evidence slot;
- tests cover canonical service evidence, carrier self-heal evidence, obsolete-v12 rejection, stale worker rejection, no duplicate worker process, durable presence emission, and observation-only authority semantics.

Executive_Rhetoric_Ledger PR #124 / merge `1fb04d7e00c57504b5237cd9f2aee88a2a3de4be` binds the ERL runtime-evidence record to this canonical presence receipt.

This source repair does not prove that a resident WorkerCoordinator is currently alive. It only ensures that the existing carrier supervision path can now produce one durable canonical observation when authentic fresh presence exists.

The current evidence order remains:

`runtime-presence.latest.json` with `present_worker_runtime_observed=true`
→ `resident-request-dispatch.latest.json`
→ ERL request-consumption receipt
→ `resident-targeted-execution.latest.json`
→ authentic fenced independent-review receipt
→ ERL activation group 9 reconciliation
→ separately governed activation group 10 evaluation.

No review completion, activation, publication, credential, claim/fence, heartbeat authority, second-machine dependency, or repository-writeback authority is created by this repair.
