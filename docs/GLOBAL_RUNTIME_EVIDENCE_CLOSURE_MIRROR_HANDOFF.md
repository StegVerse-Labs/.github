# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
COSV: `50000000100000`
Status: `ACTIVE / 18 HB32 PROFILE-DERIVED NODES / MEASUREMENT HARDENING MERGED / MEASUREMENT CHILD ACTIVE / CURRENT-IPHONE STATIC BOOTSTRAP FRESH SITE ALLOCATION REGISTERED`

## Canonical runtime model

```text
runtime/node profile
-> profile-derived retained StegOS node
-> immutable source-device HB lineage + current HB observation
-> ephemeral request consumption
-> ephemeral WorkerCoordinator claim/fence
-> ephemeral Interlock/InTr admission
-> ephemeral transport/provider/lease
-> component execution
-> exact receipt commitment
-> Master Records reconstruction
-> downstream propagation
```

Node identity/evidence/HB lineage persist. Claims/fences, InTr calls, transports, credentials, provider/browser/model/action sessions, and execution processes remain bounded and ephemeral. HB remains observability/freshness/correlation only.

## Merged implementation state

- StegBrowser retained-node/HB-lineage implementation: merged.
- StegOS profile-derived retained node, outward source-HB lineage, and receipt-to-transition implementation: merged.
- 18 HB32 runtime-node profiles plus profiled convergence runner: merged.
- StegClaw executable profile: merged.
- VACC executable profile: merged.
- typed ten-stage first-failure responses: PR #1292 merged at `e64c5d518af05dac6b9d09c3355d38d75bc27295`.
- definitive measurement hardening: PR #1293 merged at `44c6d88abb42351ec26a576e3136caec3400a613`.
- measurement ingress source repair: PR #1296 merged at `607cedc2fed1c81cf20ff6250fa3421089284a8a`.
- current-iPhone same-device WASM signer source: StegOS PR #312 merged at `4692ab506838affcf39a628c4e01dc9994abbb7b`.
- current-iPhone TVC provider client: StegOS PR #313 merged at `b98fad08b1491f6d7c243b6d23d497cf9c00d62b`.
- narrow TVC browser transport exposure: TVC PR #373 merged at `01fbf9bcb22857db01e421bcc27e6eab6ec7488c`.

## Definitive measurement contract

`workers/runtime_convergence_measurement.py` freezes one measurement identity before execution containing a unique run ID, start timestamp, local source head where available, exact runtime-node-profile and partial-solution hashes, `measurement_only=true`, `same_run_remediation_allowed=false`, `automatic_retry_after_first_failure=false`, and per-profile before/after snapshots of known canonical-work/subject receipts and retained node/HB/state/transition commitments.

`run_global_runtime_node_profile_convergence.py` distinguishes `PASS_CURRENT_RUN`, `PASS_HISTORICAL_EVIDENCE`, `FAILED_CURRENT_RUN`, and `NOT_REACHED`. Historical evidence is retained without being promoted to current-run passage. Readiness/liveness states are not terminal completion.

## Current source-device condition

The dedicated child `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001` is now the execution owner for the one-pass authentic measurement. Two observations after its ingress repair still produced no frozen run ID and no `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json`; the ten-stage visitor therefore has not yet been entered authentically.

The first unresolved condition is pre-loop, not one of the ten component stages:

`PRE_LOOP_AUTHENTIC_SOURCE_DEVICE_RESIDENT_NOT_MATERIALIZED`

The next concrete source condition inside that prerequisite is:

`CURRENT_IPHONE_SIGNER_WASM_NOT_MATERIALIZED_IN_SERVED_BOOTSTRAP_DISTRIBUTION`

The validated browser package is retained by StegOS successor `release/current-iphone-site-projection/successors/current-iphone-testflight-static-bootstrap.json`, including exact SHA-256/byte bindings for the WASM signer, bindgen glue and unsigned IPA plus the signer/executor/TVC/TestFlight modules.

## Fresh Site allocation continuation — 2026-09-09

The successor explicitly forbids reactivation of the terminal `TASK-2026-0008` Site allocation and requires a fresh monotonic allocation before destination mutation.

Fresh destination work is now instantiated as:

- Site issue `StegVerse-Labs/Site#1180`;
- organization task `TASK-2026-0010`;
- requested Site branch `claim/site-current-iphone-testflight-static-bootstrap-r1`;
- exact scope: the 14 successor destination mappings plus Site README, scoped handoff, task projection and claim receipt;
- authority ceiling unchanged: package/manifest grants no Site mutation, publication, execution, signing, TestFlight, credential, Interlock/InTr, claim/fence, or custody authority; TV/TVC remains credential/provider authority and WorkerCoordinator remains claim/fence authority.

Registration is coordination only. Site mutation must wait for the fresh canonical allocator claim/fencing evidence and a re-observed destination baseline.

## Next execution sequence

1. merge the `TASK-2026-0010` registry addition after repository validation;
2. run the existing organization allocator for the fresh Site scope and retain its new claim/fence evidence;
3. re-observe current Site `main` and bind that exact destination baseline;
4. project all 14 exact successor files into the claimed Site branch and verify source/destination hashes/bytes;
5. update Site README and `docs/CURRENT_IPHONE_TESTFLIGHT_STATIC_BOOTSTRAP_SITE_PROJECTION_MIRROR_HANDOFF.md` in the same functional change;
6. merge the validated Site projection and update the StegOS successor package with fresh task/claim/fence and destination merge evidence;
7. observe the static assets from the current iPhone through the served bootstrap;
8. activate/observe the already-built TVC primary provider runtime through its authority-owned path;
9. execute current-iPhone TVC app-resource resolution, provisioning, ephemeral signing, same-session verification, and native Build Upload;
10. install through TestFlight and obtain authentic retained-node materialization, same-device discovery, source-HB lineage, and receipt-to-transition evidence;
11. materialize the canonical measurement source into that retained node and execute exactly one measurement-only convergence pass;
12. require a frozen run ID and `global-runtime-node-profile-convergence.latest.json`, preserve it, then remediate measured lane failures only in later executions.

DE-006 remains expected to expose exact parent rebinding/re-execution once the authentic visitor is entered; readiness must not hide that stage if observed.

## README impact

The organization README already defines fresh-task derivation, canonical allocator/WorkerCoordinator authority, COSV continuation, non-authorizing HeartBeat, and the functional-change README invariant. Registering this scoped successor task does not change those repository semantics. Site README mutation is required with the actual static bootstrap projection.

## Manual work

None for the current source/coordination continuation.
