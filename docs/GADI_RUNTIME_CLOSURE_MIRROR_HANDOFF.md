# GADI Runtime Closure Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-Labs/.github`
Goal Task ID: `GADI-RUNTIME-CLOSURE-001`
Parent Goal: `GADI-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1603`
Status: `ACTIVE / SOURCE-REACHABILITY-COMPLETE / REUSABLE-RENDEZVOUS-SOURCE-COMPLETE / CANONICAL-RESIDENT-CARRIER-BOUND / AUTHENTIC-RUNTIME-EVIDENCE-PENDING`

## Canonical identity and runtime truth

The Goal Task remains `GADI-RUNTIME-CLOSURE-001`; componentization does not rename, restart, supersede, or close it. Coordination remains `ACTIVE / CLAIMED_INTEGRATION`; completion remains unclaimed and unvalidated.

PR #1630 merged the portable GADI selector repair at `ac5c59f6226ecfe7696496b7e64f23ee9d4dee0c`. Main admits `gadi_runtime_observation` through the existing portable selector. No authentic `worker-source-refresh.latest.json`, `resident-request-dispatch.latest.json`, `hb-machine-continuation.latest.json`, or `gadi-runtime-observation-request-consumption.latest.json` has been observed. Source/CI/component reuse must not upgrade that runtime evidence class.

## Reusable Task Component Model reconciliation

Canonical model: `data/reusable-task-component-model.json`
Decomposition policy: `data/reusable-task-component-decomposition-policy.json`
Evaluation: `data/reusable-task-component-evaluations/GADI-RUNTIME-CLOSURE-001.json`
Transport profile: `data/goal-task-transport-profiles/GADI-RUNTIME-CLOSURE-001.json`

The decomposition score is 25, requiring componentization before more bespoke orchestration. GADI remains the Goal Task/evidence owner.

## RTC-RESIDENT-RENDEZVOUS-010 source materialization

The reusable resident rendezvous is now source-complete across the existing owners without creating a GADI-specific network adapter:

- `.github` resident-side registered-consumer implementation merged through PR #1724 at `cbbc9bc5...`;
- `StegVerse-org/LLM-adapter` Service Gateway reusable consumer profiles merged through PR #335 at `c120a2d1...`;
- `StegVerse-Labs/Site` browser producer GADI profile merged through PR #1290 at `f36deba49ba5aa30f74e4219c73e5cdcb970f565`;
- Site exact-head validation passed, including canonical ST-017 execution of the GADI browser profile test;
- Site integration claim was terminalized through PR #1291 after validation.

The exact inner request remains `RESIDENT-OBSERVE-GADI-RUNTIME-001`. GADI uses digest-derived `transport-correlation:sha256:<digest>` rather than Node Receipt #1 as user verification. KV/SKAP Vault remains sole user-verification authority; node identity remains routing only.

These merges prove source composition only. They do not prove that a durable Service Gateway rendezvous is deployed, that discovery returns `AVAILABLE`, that the current iPhone resident is polling, that a request was stored/delivered, or that an acknowledgement or GADI consumption receipt exists.

## Current runtime transport boundary

The LLM-adapter resident rendezvous runtime requires both `STEGVERSE_RESIDENT_RENDEZVOUS_ENABLED=true` and a durable `STEGVERSE_RESIDENT_RENDEZVOUS_ROOT`. StegDeploy source config enables these on the sovereign gateway path, but the canonical resident-rendezvous handoff still records production deployment/activation/observation as open. Source/CI without a durable production root is explicitly non-proving.

The historical StegGate quick-tunnel registry is not current evidence. Current StegCore source explicitly states that GitHub-hosted heartbeat workflows are compatibility validation only; resident StegVerse workers own runtime execution and public rendezvous materialization. The Site stable-domain StegGate worker currently proxies only StegGate health/capabilities/self-test/evaluate routes and does not itself expose the resident-rendezvous API.

Therefore the first unresolved transport predicate remains:

`CURRENT_DURABLE_SERVICE_GATEWAY_RESIDENT_RENDEZVOUS_RUNTIME_OBSERVED`

followed by:

`CURRENT_GADI_DISCOVERY_AVAILABLE -> REQUEST_STORED -> RESIDENT_FETCH -> GADI_CONSUMPTION -> CORRELATED_ACK`

No packet is claimed sent through the reusable rendezvous until those runtime surfaces are authentically observed.

## Canonical resident carrier binding

GADI does not own and must not create another runtime carrier, scheduler, resident executor, or hosted production dependency. The existing canonical sovereign carrier is the HeartBeat-separated native `WorkerCoordinator` path already defined by `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md` and `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json`.

That durable-runtime handoff is already release-complete for downstream admission and explicitly classifies the historical G18/fence18 projection as stale housekeeping only. G18 terminalization, another physical machine, or a continuously connected external device may not gate GADI. The current reusable carrier observation remains runtime-unproven: `SHWP-SV002-ORG-RUNTIME-ACTIVATION-001` is still `REQUESTED`, and the expected authentic `receipts/sovereign-host/sv002-org-runtime-activation.latest.json` terminal receipt is absent from canonical `main`.

For GADI, this carrier evidence is not a new completion predicate and does not confer authority. It is the existing sovereign observation surface through which durable Gateway/runtime presence may be established. GADI must reuse it rather than inventing an alternate carrier.

Third-party process hosts, GitHub Actions, and compatibility deployment providers cannot satisfy sovereign resident proof and are excluded from GADI runtime-carrier reasoning, fallback, or completion evidence. The native StegDeploy launcher itself rejects hosted-runtime environments and records `third_party_runtime_required=false`; local readiness still does not prove a public production route.

## Component map

- Runtime observation — existing canonical GADI/runtime owners; required; current same-node discovery/readback/presence/freshness/binding evidence only.
- Canonical resident carrier — existing HeartBeat-separated native WorkerCoordinator; reused, not owned by GADI; runtime evidence pending; no G18 downstream gate.
- `RTC-RESIDENT-RENDEZVOUS-010` — source-complete; runtime-evidence-pending; conditional when local resident delivery is not authentically available; authority NONE.
- `RTC-GOVERNED-PROCESSING-002` — required; non-final processing only.
- `RTC-ROUNDTRIP-003` — required for controlled action/effect/reassessment/termination observations.
- `RTC-INTERLOCK-INTR-TRANSPORT-008` — required; Interlock/InTr owns admission/transition.
- `RTC-STEGVERSE-EGRESS-007` — required when action crosses the local StegVerse state boundary.
- `RTC-FARSIDE-FINAL-009` — conditional on the external controlled test surface.
- `RTC-EVIDENCE-CUSTODY-004` — required; Master Records owns custody/readback/reconstruction.

Not selected: `RTC-MANIFEST-001`, `RTC-PUBLISHER-005`, `RTC-SDK-RETURN-006`.

## Authority invariants

Task Registry: coordination only. WorkerCoordinator: claim/fence. Interlock/InTr: governed admission/transition. TV/TVC: credential/provider/release. KV/SKAP Vault: sole user verification. StegOS devices: interchangeable transport/execution nodes, never user verifiers. Master Records: observed-reality custody/reconstruction. HeartBeat: timing/freshness/liveness/state correlation/observability only. GitHub: no runtime authority.

No runtime subject, node identity, Secure Enclave identity, transport identity, or device identity may become user-verification authority.

## Remaining Goal Task-specific predicates

1. Current retained StegBrowser/StegOS node discovery observed.
2. Current persisted current-iPhone receipt readback observed for the same node.
3. Current same-node presence/liveness/supervision/freshness and GADI runtime binding observed.
4. Authentic GADI resident request delivery/consumption observed through local delivery or reusable rendezvous as applicable.
5. Authentic Interlock/InTr defensive admission observed.
6. Authentic WorkerCoordinator claim/fence observed.
7. Authentic resident defensive action observed.
8. External safe-state effect observed.
9. Adaptive reassessment after strategy change observed.
10. Termination after threat end observed.
11. Full intervention receipt chain valid.
12. Authentic Master Records reconciliation and exact confrontation reconstruction observed.
13. Only then may `GADI_RUNTIME_CLOSURE_COMPLETE` be claimed.

## Next admissible work

Do not add another rendezvous implementation or runtime carrier. Resolve the current authentic runtime surface through the existing sovereign carrier in this order:

1. observe the existing HeartBeat-separated native WorkerCoordinator carrier through authentic resident dispatch/runtime receipts; do not wait on stale G18 housekeeping and do not use a hosted provider substitute;
2. from that existing carrier, observe a durable Service Gateway instance with resident rendezvous enabled and durable storage;
3. observe a current resident poll/advertisement for `consumer=gadi_runtime_observation`;
4. require discovery `AVAILABLE` for exactly one canonical routing node;
5. submit the exact canonical GADI request once, with digest-derived transport correlation and no blind retry;
6. require resident fetch/materialization, `gadi-runtime-observation-request-consumption.latest.json`, and a correlated bounded acknowledgement;
7. then continue same-node runtime binding -> InTr admission -> WorkerCoordinator claim/fence -> controlled action/effect/reassessment/termination -> Master Records reconstruction.

If local authentic resident delivery becomes observable before rendezvous activation, use the local path instead; the rendezvous is conditional, not mandatory.

No second user-operated device is required. No connected-device discovery is a prerequisite. No device verification is permitted.

## README impact

README semantics were reviewed for this reconciliation. No README change is required because the canonical resident-carrier and authority boundaries are already repository-wide contracts; this change only binds GADI to the existing carrier.

## Manual work

None.
