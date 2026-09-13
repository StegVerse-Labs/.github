# Site Publication Native Runtime Execution Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-Labs/.github`
Canonical issue: `#1486`
Goal Task ID: `SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001`
Parent Goal Task ID: `KV-CONNECTION-REVALIDATION-WORKER-001`
Child runtime task: `SITE-PUBLICATION-INTR-CONSUMER-001`
COSV: `50000000102000`
Status: `ACTIVE / REUSABLE SOURCE+SCHEDULER OWNERS BOUND / AUTHENTIC PUBLICATION EVIDENCE PENDING`

## Purpose

Own the remaining authentic Site publication runtime/evidence phase. Reuse canonical source refresh, neutral reusable scheduling, WorkerCoordinator, Universal InTr, StegOS publication runtime, runtime observation, and Master Records components rather than introducing task-specific execution substrates.

## Validated source lineage

- PR #1398 merged the independently claimable Site publication worker at `7444aefbdd2c644c46ae105192af4a524ef02172` after Heartbeat `34615815337`, Deterministic Repository Suite `34615815364`, and Organization Control `34615815476` passed.
- Canonical Site source boundary: `StegVerse-Labs/Site@bc1ee7257ebc64f77dab3f0b746bb3a86a279b6c`.
- Existing source-validation lineage identifies materialization `INTR-MAT-0e1ba4786b0ea8a00e1f166e`, packet `INTR-58dec5416bd4358190c11372`, and manifest `sha256:e6bc47580f25296df61d16dfe5a74f3f49fec0dda018c813696195c960e77f09`.
- Parent reconciliation PR #1483 merged at `4ab13a252eed668f1d828c08bd998b00b54e3c43` after its three required validation lanes passed.
- Reusable Task Component reconciliation preserves this Goal identity and its runtime predicates.

None of those source facts is runtime/publication proof.

## Reusable source refresh and scheduling

Source refresh is owned by `RT-SOVEREIGN-SOURCE-REFRESH-001`, consuming `RTC-SOVEREIGN-SOURCE-REFRESH-010` and the existing local-only `scripts/refresh_sovereign_worker_runtime_source.py` implementation. The Goal passes already-local source/runtime roots and consumes the authentic child completion or boundary receipt; no connected-device polling is a prerequisite.

Neutral scheduling is owned by `RT-REUSABLE-TASK-SCHEDULER-001`, contract `data/reusable-task-scheduler-contract.json`, runner `scripts/run_reusable_task_scheduler.py`. Scheduling is conditional orchestration support only and never a Goal completion predicate or authority source.

## Authority boundaries

- Task Registry: coordination only.
- WorkerCoordinator: fresh claim/fence authority.
- Interlock/InTr: governed admission/transition authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- Master Records: observed-reality custody/reconstruction.
- HeartBeat/resident carrier: timing/trigger/liveness only.
- GitHub runtime authority: `NONE`.
- Reusable task/component/scheduler orchestration: non-authorizing.
- No device-verification policy/process, device identity gate, second user-operated device, or hosted-runtime substitute is required.

## Admitted materialization binding

Authentic Universal InTr ingress persists both:

```text
receipts/sovereign-network/site-publication-intr-ingress.latest.json
intr-materialization/<materialization_id>.json
```

The child `SITE-PUBLICATION-INTR-CONSUMER-001` now resolves its opaque materialization id from that write-once local admitted-ingress evidence. The receipt must be `INGRESS_ADMITTED_CANDIDATE_ONLY`, exact-request validated, write-once persisted, non-authorizing, and bound to the exact queued request under the same runtime root.

`STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID` remains an optional correlation input only. When present it must equal the locally admitted id; mismatch fails closed. The environment value cannot substitute for authentic ingress evidence and cannot grant claim/fence, execution, or transition authority.

This supersedes the former manual env-binding step as the publication candidate source of truth.

## Required authentic evidence chain

1. Advance `RT-SOVEREIGN-SOURCE-REFRESH-001` using already-local source/runtime roots and retain its authentic completion/boundary receipt.
2. Require authentic Universal InTr Site-publication ingress to persist the exact candidate and write-once queue entry.
3. Allow existing WorkerCoordinator task discovery to find `SITE-PUBLICATION-INTR-CONSUMER-001` from `worker-registry.d`; fresh independent checkout/admission must mint claim/fence.
4. The worker resolves the materialization id from local admitted-ingress evidence and retains candidate-validation evidence for that same fencing generation.
5. Execute one authentic bounded `EVENT_EPHEMERAL` publication lease through the canonical StegOS/InTr runtime owner.
6. Independently observe `/intr/profile`, exact HTTP byte/path hashes, candidate evidence export, and lease closure.
7. Separately admit the final publication transition through Interlock/InTr.
8. Retain publication evidence through Master Records custody/reconstruction.
9. Only then prove conditional DNS/TLS recovery and public-content equivalence where applicable.

No preceding receipt grants the authority required by a later step.

## Predicates currently false until authentic evidence exists

```text
SOVEREIGN_SOURCE_REFRESH_OBSERVED
FRESH_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
RUNTIME_WORKER_EXECUTION_OBSERVED
BOUNDED_EVENT_EPHEMERAL_LEASE_EXECUTION_OBSERVED
PUBLIC_HTTPS_INTR_PROFILE_OBSERVED
EXACT_HTTP_BYTE_PATH_EQUIVALENCE_OBSERVED
LEASE_CLOSURE_OBSERVED
FINAL_PUBLICATION_TRANSITION_ADMITTED
DNS_TLS_RECOVERY_PROVEN
```

## Next action

Validate and merge the admitted-ingress binding repair. Then advance the existing reusable source-refresh and Site publication component chain and retain authentic receipts. Source merge, scheduler execution source, CI, homepage reachability, or the materialization identifier alone must not be promoted into publication proof.
