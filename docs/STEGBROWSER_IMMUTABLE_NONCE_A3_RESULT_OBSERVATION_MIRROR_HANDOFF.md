# StegBrowser Immutable Nonce A3 Result Observation Mirror Handoff

Updated: 2026-09-20

## Task pointer

- Goal Task ID: `STEG-BROWSER-IMMUTABLE-NONCE-A3-RESULT-OBSERVATION-001`
- Parent/decomposed-from: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Issue: `StegVerse-Labs/.github#2338`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT`
- Immutable invocation nonce: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z`
- Requested invocation count: `1`
- Second invocation allowed: `false`

## Scope

Observe only newly surfaced authentic execution results for the existing immutable StegBrowser request. Source declarations, tests, handoffs, absence of results, and static failure strings are not runtime evidence.

If an authentic result binds this nonce to a WorkerCoordinator `claim_id` and `fencing_token`, continue that same lineage through Interlock/InTr and canonical Master Records. Every successor must close with `state=RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, and exact `receipt_sha256 == reconstructed_receipt_sha256` before further progression.

If an actual cycle result records a deterministic failure before A3, repair only that first defect in the existing path and rerun through the same original request. Do not issue another invocation, infer failure from absence, revisit Healer/device/routing architecture, or add another runtime/authority/custody plane.

## Initial inherited observation

At parent Goal Prompt 20, a final exact-nonce GitHub evidence inspection found no authentic nonce-bound WorkerCoordinator `claim_id` + `fencing_token` and no actual cycle result recording a deterministic pre-A3 failure. Matches were limited to implementation, tests, task records, and handoff declarations. A3 therefore remains `NOT_OBSERVED`, not `FAILED`, and runtime completion is unclaimed.

## Completion predicate

Complete only when either (a) the authentic nonce-bound A3 claim/fence is observed and the state-dependent successor lineage is advanced as far as authentic evidence permits, or (b) an actual deterministic pre-A3 runtime failure is surfaced, repaired on the existing path, and the same immutable request is rerun. Missing evidence alone is neither completion nor failure.

## Manual work

None.


## Goal Prompt 1/20 — Master Records made directly actionable

The controlling evidence question is now explicit: the authoritative A3 evidence belongs in canonical Master Records, not in a broad GitHub evidence search. WorkerCoordinator's existing assignment path creates transition `WORKERCOORDINATOR_CLAIM_FENCE_BOUND` and synchronously submits that claim/fence transition to canonical Master Records before task activation can proceed.

Inspection of `master-records/orchestration` found a concrete read-path defect. The custody table already stores and indexes `subject_or_correlation_id`, but the API exposed reconstruction only by an already-known `receipt_sha256`. Therefore the system could custody a transition yet provide no direct way to ask, "what records exist for this immutable nonce?"

That defect is repaired and merged:

```text
master-records/orchestration#105
exact head: 2c4ab1a058a288cc4645ffbcb5750d98188a7ef3
merge: e88be99fdfa678b19b3d0c52d120d15a60c9557c
Runtime Evidence Validation: 35526500242 PASS
orchestration/custody tests: PASS
```

The existing custody API now supports the authenticated, non-authorizing query:

```text
GET /api/master-records/state-transitions/query
  ?subject_or_correlation_id=STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
  &transition_id=WORKERCOORDINATOR_CLAIM_FENCE_BOUND
```

Each returned record is reconstructed from the existing custody store and carries the canonical receipt/reconstruction digest and required-evidence validation results. No second store, API authority, runtime, credential path, invocation, scheduler, dispatcher, or custody plane was created.

This supersedes the vague phrasing "no claim/fence evidence surfaced." The next classification must come from the authoritative Master Records query:
- one or more matching records -> validate `RECORDED + reconstruction_status=PASS + required_evidence_validation_status=PASS + receipt_sha256 == reconstructed_receipt_sha256`, then continue the same lineage;
- zero matching records -> actionable fact: no `WORKERCOORDINATOR_CLAIM_FENCE_BOUND` transition for this immutable nonce is present in the queried canonical custody store; trace the existing producer path to the first missing transition;
- a retained pre-A3 failure record -> repair only that exact first deterministic failure and rerun through the same original request.

The source repair itself does not prove the authentic runtime store has been queried or that A3 executed.

Manual work: None.


## Goal Prompt 2/20 — canonical runtime loading repaired; target durable store still not evidenced

The requested authenticated nonce query was **not** executed against a substitute GitHub/CI database. Current canonical evidence does not expose an authentic durable Master Records endpoint or runtime advertisement for the target custody store, and the existing Runtime Evidence Validation lane explicitly does not claim a production endpoint.

Tracing the existing Master Records runtime-loading path found the first concrete defect before any authoritative query could be trusted: the workflow launched:

```text
services.master_records_custody_api:app
```

That base app does not install the canonical state-transition custody module, so neither the hash-addressed reconstruction route nor the merged subject/nonce query route from PR #105 was loaded.

The existing service entrypoint was repaired in `master-records/orchestration#106` to launch:

```text
services.canonical_master_records_api:app
```

This reuses the same base Master Records app/store and installs the existing canonical state-transition routes; no second service, runtime, custody store, credential path, or authority plane was introduced. The orchestration contract checker now fails closed if the base-only entrypoint returns.

Exact validation:

```text
PR #106 exact head: 8f891a271ebc070cdd8fb1cb9e7f19d5ba8ff817
Runtime Evidence Validation: run 35527681406 PASS
Start owned authenticated custody service: PASS
Authenticated custody/readback: PASS
Orchestration/custody tests: PASS
all exact-head workflows: PASS
merge: 8804762fb5da5d212aa7c9c448dfcdabac734715
```

The workflow-local service proves the canonical app can load and existing custody behavior remains intact. It does **not** answer the StegBrowser query because that workflow starts a fresh run-scoped database and explicitly does not claim production deployment.

The remaining actionable condition is therefore not "evidence has not surfaced." It is:

```text
AUTHENTIC_DURABLE_CANONICAL_MASTER_RECORDS_RUNTIME_ENDPOINT_NOT_YET_EVIDENCED
```

The next execution path is to trace the existing Master Records durable runtime materialization/source-refresh path, require it to load merge `8804762fb5da5d212aa7c9c448dfcdabac734715`, then execute:

```text
GET /api/master-records/state-transitions/query
  ?subject_or_correlation_id=STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
  &transition_id=WORKERCOORDINATOR_CLAIM_FENCE_BOUND
```

against that actual durable canonical store. Only that result may classify A3 custody.

Manual work: None.


## Goal Prompt 3/20 — resident Master Records source refresh repaired

Tracing the existing durable materialization/source-refresh chain found a specific source-refresh defect:

- StegDeploy already materializes `vendor/master-records-orchestration`.
- the rootless resident source-refresh watcher already watches the canonical local package path for `stegverse-master-records`;
- but the watcher only refreshed `.github` WorkerCoordinator/control-plane source and never materialized the changed Master Records package into the existing resident vendor root.

That meant a resident runtime could remain on stale Master Records source even after `master-records/orchestration` main advanced through `8804762fb5da5d212aa7c9c448dfcdabac734715`.

The defect was repaired on the existing refresh service in `StegVerse-Labs/.github#2352`. The watcher now validates the already-local `stegverse.source-package/v1` object for `stegverse.master-records` and atomically replaces only the existing runtime source projection at `vendor/master-records-orchestration` before resident request dispatch. It performs no network fetch and creates no new runtime, service, scheduler, credential path, custody store, host, or invocation.

Validation history:
- first exact-head run `35528771460`: failed on a concrete missing `tempfile` import;
- defect repaired on the same branch;
- exact-head run `35528813844`: PASS;
- merged as `e3a0f31c1b31b2d0133969bd1409a6218d693e65`.

This repairs the path that is supposed to move current Master Records source into the already-existing resident runtime. It does not itself prove that a resident refresh cycle has consumed the current package or that the durable Master Records process has restarted/reloaded that source. No authoritative nonce query is claimed yet.

Manual work: None.


### Goal Prompt 3/20 supplemental provenance hardening

Concurrent canonical reconciliation established the first existing-path defect for this prompt as the resident source-refresh watcher failing to materialize the watched `stegverse-master-records` package into `vendor/master-records-orchestration`; that repair remains canonical via PR #2352 / `e3a0f31c1b31b2d0133969bd1409a6218d693e65`.

A second, adjacent provenance weakness was repaired without changing that first-defect ordering. The existing sovereign bundle producer still accepted Master Records source if it merely descended from the old SV001 floor `8e33b3e95d3d9e34387fe393031f44bebcdb5d57`, and the protected path set omitted the canonical state-transition custody/API files. Thus a refreshed resident source could still be labelled `VERIFIED_LOCAL_GIT_SOURCE` without proving it contained the query/canonical-app lineage through `8804762fb5da5d212aa7c9c448dfcdabac734715`.

PR #2354, merged as `5b37c88a0ec6dcb9d5d8289b025e8d80418106cf`, hardens the same existing source-proof path by:
- requiring Master Records source history to contain `8804762fb5da5d212aa7c9c448dfcdabac734715`;
- protecting `services/canonical_state_transition_custody.py`;
- protecting `services/canonical_master_records_api.py`.

Exact-head validations passed: KV AI Memory Resident Binding run `35528815067`; DeepSeek resident run `35528814989`.

This supplemental repair does not create a new runtime or change the Goal Prompt count. Authentic resident refresh/materialization, durable runtime advertisement, and the authoritative nonce query remain unobserved.


## Goal Prompt 4/20 — recurring Master Records package materialization repaired

Registry generation entering this continuation: `163`.

A second concrete defect remained in the same existing resident source-refresh path after PR #2352. The watcher correctly monitored the already-local `stegverse-master-records` package, and the installer could materialize that package into `vendor/master-records-orchestration`, but the recurring systemd service cycle invoked only `refresh_sovereign_worker_runtime_source.py` before resident dispatch. Therefore package changes after watcher installation could wake the path unit while leaving the resident Master Records vendor root stale.

The bounded repair merged in `StegVerse-Labs/.github#2436`:

```text
exact head: 0af38b780416b786dee9a4965af547577f811d86
validation: Cross-Framework Current-Basis Resident Request Validation (Non-Authorizing)
run: 35600016501 PASS
merge: 00c44a53ab684a1c5abde5cf23cb93be6daa37e3
```

The same existing refresh service now invokes the existing Master Records package materializer in a materialize-only mode before resident request dispatch on every path-triggered refresh cycle. The mode does not reinstall the watcher and adds no runtime, scheduler, dispatcher, observer, device prerequisite, credential path, custody store, invocation, or authority plane.

This is source-path repair evidence only. It does **not** prove that an authentic resident refresh cycle has consumed the current package, that a durable canonical Master Records runtime is active on the refreshed source, that the immutable-nonce query has executed, or that A3 claim/fence evidence exists.

The next admissible progression remains:

```text
observe authentic existing resident refresh
-> require materialized Master Records source at 8804762f... or later
-> observe durable canonical Master Records runtime using that source
-> query the durable canonical store for
   subject_or_correlation_id=STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
   transition_id=WORKERCOORDINATOR_CLAIM_FENCE_BOUND
-> if matching record exists require RECORDED + reconstruction_status=PASS
   + required_evidence_validation_status=PASS
   + exact receipt/reconstruction digest equality
-> otherwise trace the first missing custody producer transition
```

Manual work: None.


## Goal Prompt 5/20 — retained refresh evidence and source proof merged; authentic cycle still required

Canonical registry generation entering this continuation: `169`.

Two subsequent existing-path repairs are already merged on canonical main:

- PR `#2465` / merge `c3de84f2d4e8dc6c587b53a73f9eba5f7ac5033d` retains each materialize-only Master Records refresh result at `receipts/sovereign-host/master-records-source-refresh.latest.json` using schema `stegverse.master-records-resident-source-refresh/v1`.
- PR `#2472` / merge `0c8256e024867199ff065eb19f1277158c9f1635` binds the existing Master Records source package to local Git ancestry proof. The resident materializer now fails closed unless `package_provenance.source_proof` reports `state=VERIFIED_LOCAL_GIT_SOURCE`, repository `master-records/orchestration`, source floor `8804762fb5da5d212aa7c9c448dfcdabac734715`, `source_floor_present=true`, and a valid 40-hex source head.

Repository search still exposes the retained receipt path only as implementation/test contract; no authentic resident copy of the receipt is tracked in GitHub. No authorized resident computer/runtime surface is connected to this continuation. That access condition is not treated as evidence of runtime absence and is not a device prerequisite.

Therefore the first unsatisfied predicate is now:

```text
AUTHENTIC_RETAINED_MASTER_RECORDS_SOURCE_REFRESH_WITH_VERIFIED_SOURCE_PROOF
```

Do not trust a durable Master Records runtime advertisement until the authentic retained refresh receipt proves `state=MATERIALIZED_VERIFIED` and carries the required source proof. Only after that may the existing durable canonical runtime be queried for:

```text
subject_or_correlation_id=STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
transition_id=WORKERCOORDINATOR_CLAIM_FENCE_BOUND
```

No A3 claim/fence, nonce-query result, durable runtime state, or runtime completion is claimed by these source/evidence repairs.

Manual work: None.
