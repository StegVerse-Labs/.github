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

## 2026-09-05 ephemeral resident v13 identity alignment

Follow-up inspection confirmed that the single-host ephemeral resident mode launches both `run_heartbeat_runtime.py --continuous` and `run_worker_runtime.py --continuous`, so it traverses the same existing carrier supervision path that can emit the canonical runtime-presence receipt. The remaining defect was stale identity metadata: both its process receipt and its activation/service receipt still declared `heartbeat_runtime.engine_v12.HeartbeatRuntime`.

StegVerse-Labs/.github PR #1005 / merge `f564aeec9eb8a5bf195a59f2f00a458c3a50fa23` removes that stale binding:

- `scripts/restart_sovereign_ephemeral_node.py` now emits canonical v13 carrier identity while preserving the separate WorkerCoordinator process and task-capable tick requirement;
- `scripts/run_sovereign_ephemeral_console.py` now emits v13 `canonical_runtime` and `canonical_carrier_runtime`, and explicitly states that HB grants no execution authority;
- `heartbeat_runtime/runtime_presence_projection.py` accepts an ephemeral-console activation receipt only when carrier and worker are both active, processes are separated under StegVerse supervision, canonical v13/WorkerCoordinator identities match, no third-party process host is required, and HB authority is explicitly false;
- stale v12 ephemeral-console receipts now fail closed rather than being eligible runtime-liveness evidence;
- tests verify continuous carrier/worker reachability, v13 identity, and stale-v12 rejection.

This repair changes source identity and observability validity only. It does not prove that an ephemeral or native resident runtime is presently alive and does not advance ERL review state.

The current evidence order remains:

`runtime-presence.latest.json` with `present_worker_runtime_observed=true`
→ `resident-request-dispatch.latest.json`
→ ERL request-consumption receipt
→ `resident-targeted-execution.latest.json`
→ authentic fenced independent-review receipt
→ ERL activation group 9 reconciliation
→ separately governed activation group 10 evaluation.

No review completion, activation, publication, credential, claim/fence, heartbeat authority, second-machine dependency, or repository-writeback authority is created by these repairs.
