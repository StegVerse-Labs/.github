# Execution Spine Regression Reconstruction — 2026-09-19

Status: REGRESSION_RECONSTRUCTION_COMPLETE / ACTIVE-GOAL-REPLAY_FROZEN_PENDING_MINIMAL_AUTHENTIC_CHAIN

## Scope

This reconstruction freezes new architecture, predicate, runtime, scheduler, dispatcher, carrier, authority-plane, custody-store, validator, and device dependencies while tracing the existing StegVerse execution spine against these established invariants:

1. governed work progresses by state-dependent transitions;
2. each successor consumes its immediately preceding canonical closure where that state-dependent contract applies;
3. HeartBeat and all HB sub-signals remain non-authorizing carrier/synchronization/runtime-environment surfaces and initiate work only where no predecessor state transition is available;
4. WorkerCoordinator owns executable assignment / claim / fence;
5. Interlock/InTr owns governed transition admission;
6. Master Records owns observed reality, custody, and reconstruction, not transition authority;
7. StegDB compares durable/index state with Master Records;
8. StegHealth classifies health consequences and derives/reuses remediation only after coordinated comparison.

This document does not add a completion predicate to any existing Goal Task.

## Reconstruction result

There is no single historical commit at which the entire current execution spine simultaneously implemented all eight invariants correctly. Recovery therefore cannot safely be a whole-tree rollback.

The evidence separates into:
- independently correct architectural fixes that must be preserved;
- identifiable regressions with first-introduction commits;
- missing shared behavior that was never implemented globally and therefore has no historical good commit to restore.

## Invariant history

### HB / sub-signal authority separation — preserve

Relevant history:
- `afc383452fdf8e0cddedfb3d29b7025e43f5891a` — 2026-08-18 — decoupled heartbeat continuity from worker execution.
- `41bfee42f0f078c4ba147dcfa9afd3941ef59e96` — 2026-08-23 — removed resident-daemon progression dependency and established protocol-derived oscillator/reference semantics.
- `23d84389e8141b5ce78861348f3aad1057509643`, `ea09c87106b63fab8bba29872213a91c4e2cf82e`, `7bba6e0461ba131b3a04f32c84c3b393d22e14d0`, `927a57094acdf1916c2bdd419887b23a8e106e08` — 2026-08-31 — generalized HB-derived InTr carrier/sub-signal transport while retaining non-authority.

Disposition: PRESERVE. No later commit reviewed here establishes HB authority over WorkerCoordinator, InTr, or Master Records.

### Canonical Task Registry selection — regression identified and repaired

First regression:
- `5548599dacd1b073b7c50c57caf9a80bf9771466` — 2026-09-13 — introduced the registry-first Canonical Work selector with `machine_ingress_candidate()` restricted to `coordination_state == PROPOSED`.

Consequence:
- a task already `ACTIVE / CHECKED_OUT` with a valid state-dependent `INGRESS_ADMITTED` successor could not be selected by the shared cycle;
- later resident/goal-context repairs operated above this restriction and therefore could not cure it.

Dependent history includes:
- `306eaf033cf2ddec1c5f964090c95977b3c08b5e`
- `c7278a6e9cb1819df7360dfb4ee789495984ea5c`
- `8f1fca373ffff278a1151af4135315d187a79280`
- `a3aaf67bcff91734e882fe1706e39affe3312136`
- `3ecf0737be9c20c530c2c47d7d51dad6359dfa7`

Current repair:
- `ae26ef1e017abaadf2cee82dd52377ed27c71710` — allows `ACTIVE / CHECKED_OUT` state-transition carriage where `INGRESS_ADMITTED` is explicitly allowed.

Disposition: PRESERVE CURRENT REPAIR; DO NOT REINTRODUCE PROPOSED-ONLY SELECTION.

### Worker-return / StegDB + Master Records + StegHealth coordination — regression identified and repaired

First contract/evaluator introduction:
- `0f6905903e03d71dc52eb158b5c7111ecdb564e2` — worker-return observation contract.
- `19e28eb7a8c76c26d6f6612d50b8c9cbea267549` — health evaluator.

Regression:
- missing Master Records return after an expected-return deadline could be classified without requiring the coordinated StegDB comparison;
- `claim_ref` alone could contribute to checkout inference even without a WorkerCoordinator fence.

Dependent health work:
- `317ff34636d33c759074fee9a75dfecaba68f92f`
- `d15866b7b67125797d6bf21fa83e7f9e8546ef8f`

Current repair:
- `ae26ef1e017abaadf2cee82dd52377ed27c71710` requires StegDB comparison before runtime-failure classification, keeps absence-only cases at `RECONCILIATION_REQUIRED`, preserves canonical-registry truth over stale shards, and requires WorkerCoordinator authority + claim + fence for claim-based checkout inference.

Disposition: PRESERVE CURRENT REPAIR.

### Master Records canonical custody — preserve architecture; downstream adoption lag was real

Canonical custody task introduced:
- `b66f4040219aa4e94b019e97139e8d827b845c50` — 2026-09-17.

Its invariant was already correct: every observed governed transition emits a canonical state receipt; Master Records is custody/reconstruction only; missing transitions cannot be fabricated.

Observed downstream inconsistency:
- the Healer scheduler still declared `continuity.master_records_required=false` until `8f97aad113df909fc089a40b9420e9f6b0c9b0f1` on 2026-09-18.

Disposition: PRESERVE canonical custody architecture and corrected consumer adoption. Treat similar downstream mismatches as stale-consumer regressions, not reasons to add custody layers.

### State-dependent immediate-predecessor chaining — correct in specialized paths, never globally implemented in shared coordinator

Strong explicit implementations now exist in:
- MIR Aileash witness reconciliation;
- SDK TT purpose-bound worker lifecycle / four-case graph;
- SDK TT Richard seam atomic transition.

Relevant SDK history:
- `4e93385520ebe3070668793add36cb70396cd7ba` — claim/fence Master Records progression gate;
- `79da747181023f39f5feb2f890c41122c1c44129` — per-phase lifecycle custody gate;
- `c0c1e7be32717e0d5e8ef025fa622e5a380f9e17` — fully state-dependent four-case graph.

However, the shared Canonical Work selector still selects only tasks whose next transition is `INGRESS_ADMITTED`. It does not generically consume an arbitrary valid predecessor Master Records closure and evaluate the declared successor edge.

Disposition: NO HISTORICAL WHOLE-SYSTEM REVERT EXISTS FOR THIS GAP. Do not invent a second successor engine. Reconcile the shared coordinator to the already-proven state-dependent semantics only after the minimal authentic chain below is observed.

## Previously observed false dependencies already corrected

These historical repairs are evidence of the same regression family and should remain removed:
- Test 3 stale carrier prerequisite removed by `52b3dbb84ce404a12df0420e21bf795260ca3e81`;
- Test 3 next runtime dependency corrected to fresh WorkerCoordinator claim/fence by `0f0e0ee0c12b9943e470c0f5a5c44ac04850688a`;
- StegBrowser artificial Healer prerequisite removed by `cc13725c6b056481e8ec5d2a33c75c6bca3ceee8`.

## Minimal-chain proof status

The smallest existing source-semantic chain is the SDK TT Richard seam:

```text
HANDOFF_READY T / no authoritative W
-> fresh WorkerCoordinator claim/fence
-> Master Records closure of claim/fence
-> TV/TVC warrant/policy verification
-> Interlock/InTr ACTIVATE(T)+CREATE_AND_BIND(W,T)
-> Master Records RECORDED
   + reconstruction PASS
   + required-evidence PASS
   + receipt/reconstruction digest equality
-> ACTIVE T <-> W
-> invocation
-> CLOSE(T)+RETIRE(W,T)
-> Master Records terminal closure
-> no continued authority
-> records-only reconstruction
```

Source-semantic proof already exists:
- dedicated Test 3 acceptance run `35452251194` passed;
- it validates ordering and fail-closed source semantics only.

Authentic end-to-end runtime proof is NOT established by CI or source validation.

Therefore:
- ACTIVE-GOAL REPLAY REMAINS FROZEN;
- no source/CI result may be promoted into authentic runtime proof;
- the freeze ends only when this existing minimal chain produces authentic retained receipts through the existing WorkerCoordinator -> TV/TVC -> Interlock/InTr -> Master Records path.

## Nonclaims

- No new architecture was created by this reconstruction.
- No new completion predicate was added to an existing Goal.
- No new runtime, scheduler, dispatcher, carrier, authority plane, custody store, validator, credential path, host dependency, or device dependency is introduced.
- GitHub/CI remains validation/evidence transport only.
