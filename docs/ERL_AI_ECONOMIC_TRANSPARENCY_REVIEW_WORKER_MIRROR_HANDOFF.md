# ERL AI Economic Transparency Review Worker Mirror Handoff

Status: SOURCE IMPLEMENTED — RESIDENT REVIEW EXECUTION PENDING

Canonical research owner: `StegVerse-Labs/Executive_Rhetoric_Ledger#104`
Worker task: `SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001`
Implementation owner: `StegVerse-Labs/.github#927`

This worker exists only to execute the fixed independent-review package for finalized OpenAI, Anthropic, and DeepSeek consumer/non-account-attributed transparency findings.

It grants no research-promotion, activation, publication, provider, credential, repository-writeback, heartbeat-state, claim, fence, wallet, or trade authority.

Installed source:
- `workers/erl_ai_economic_transparency_review_worker.py`
- `handoffs/SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001.json`
- `control/worker-registry.d/erl-ai-economic-transparency-review-001.json`
- `control/process-worker-adapters.d/erl-ai-economic-transparency-review-001.json`
- `control/task-vectors/SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001.json`

Runtime success requires an authentic fenced resident execution receipt. Source merge, CI success, registry presence, heartbeat progression, or handoff readiness do not satisfy the independent-review gate.

Terminal review output must be a bounded recommendation receipt with `APPROVE` or `REVISE`; activation/publication decisions remain separate ERL governance actions.


## 2026-09-03 control-plane reconciliation

Initial reviewer integration exposed two validation defects rather than a runtime failure:

1. missing post-policy Admissible-Existence binding;
2. missing COSV task-vector / denominator projection.

They were repaired in:
- PR #930 / merge `0f4214b13373741124ef79dd37774b0585f0721b` — AE binding + retrospective conformance;
- PR #931 / merge `ddebfc0aa31a58c4b41e02fc871d254af1813133` — COSV index + denominator/coverage projection.

Current source/control posture:
- worker source: installed;
- executable handoff: HANDOFF_READY;
- AE phase: ADMISSIBLE;
- COSV vector: `50000000101000`;
- resident execution receipt: not observed;
- independent-review completion: not claimed;
- user/device action: none.

This validation branch exists only to obtain post-repair repository validation evidence against the reconciled main state. Hosted validation remains non-authorizing and cannot satisfy the resident review gate.


## 2026-09-03 self-contained review package

Issue: #940

The prior cross-repository local-source dependency has been removed from the normal resident execution path.

A byte-preserving review-input package is now stored under:
`review-packages/erl-ai-economic-transparency-001/`

Its manifest binds every copied ERL input by both source Git blob identity and SHA-256. The reviewer verifies SHA-256 before using the bundled package. A hash failure causes the bundled package to be rejected rather than reviewed.

The worker still accepts an independently materialized canonical ERL source tree as a fallback. No network checkout is permitted.

As a result, the remaining blocker is no longer “ERL source/package not locally materialized.” The bounded task is source-ready inside the resident worker repository; the remaining unsatisfied condition is authentic fenced resident execution and its receipt.

This package does not alter the research findings, independently approve them, activate the research, or authorize publication.


## 2026-09-03 resident dispatch integration

Issue: #949

The reviewer is now wired into the existing resident request-dispatch path without creating a second scheduler or authority plane.

Installed:
- `control/resident-execution-request.d/erl-ai-economic-transparency-review-001.json`
- `scripts/consume_erl_ai_economic_transparency_review_request.py`
- dispatcher registration under selector `erl_ai_economic_transparency_review`

The source refresh path now copies `review-packages/` and the new consumer into resident runtime, and the rootless filesystem watcher observes `review-packages/` changes.

The request/consumer grants no claim, fence, credential, heartbeat, research-promotion, activation, publication, or repository-writeback authority. It only asks the already-authorized WorkerCoordinator to attempt the existing admitted task.

Runtime completion still requires authentic fresh claim/fence execution and the bounded review receipt.


## 2026-09-03 portable targeted-dispatch addressability repair

Live main-state inspection found one remaining source/control addressability defect after the resident dispatch integration: the generic dispatcher registered `erl_ai_economic_transparency_review`, but `scripts/refresh_and_dispatch_resident_requests.py` did not admit that selector in its exact-consumer allowlist.

The defect was repaired in PR #951 / merge `f0ad65023b5ec8d9b1b5787492efb3f27af5fc2f` by adding only the already-existing ERL selector to the portable bridge allowlist.

Effect of the repair:
- the existing portable local refresh + exact-consumer dispatch bridge can now target `erl_ai_economic_transparency_review` directly;
- no second scheduler, heartbeat, worker registry, credential path, claim/fence authority, or runtime owner was created;
- no review-completion, activation, publication, or repository-writeback authority was added;
- no runtime execution is inferred from the merge.

The exact required review receipt remains unobserved:
`receipts/erl-ai-economic-transparency-review/SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001.json`

Current blocker remains `RESIDENT_EXECUTION_RECEIPT_PENDING`. No user action is presently required.


## 2026-09-03 portable-selector regression guard

The targeted-dispatch repair is now protected by a deterministic regression assertion in:
`tests/test_erl_ai_economic_transparency_review_resident_bridge.py`

PR #970 / merge `8ccb5cff24d9b6b69e2da37dd950095eee616a23` verifies that `erl_ai_economic_transparency_review` remains present in `ALLOWED_TARGET_CONSUMERS` while preserving the existing consumer, source-refresh, review-package, and credential-boundary checks.

This regression guard proves only source/control wiring. It does not prove resident execution, independent-review completion, activation, publication, or repository writeback.

The exact authentic review receipt remains the sole substantive completion gate for this reviewer lane:
`receipts/erl-ai-economic-transparency-review/SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001.json`


## 2026-09-04 functional exact-dispatch verification

The portable selector is now also covered by a behavioral exact-consumer test:
`tests/test_erl_ai_economic_transparency_portable_exact_dispatch.py`

PR #978 / merge `c8f7861dfac86979fe6ed540f3ca903a9a73b7d2` verifies that the portable refresh+dispatch bridge passes `--only-consumer erl_ai_economic_transparency_review`, observes exact selector isolation, dispatches no unrelated consumer, forwards no GitHub credential, performs no network source fetch, and mints no claim/fence or runtime authority.

The rootless source-refresh watcher independently invokes the generic resident dispatcher after refresh, and WorkerCoordinator discovers `control/worker-registry.d/*.json` task fragments at runtime. The ERL review task therefore remains addressable through both the normal generic resident request visit and the bounded portable exact-consumer path without mutation of the monolithic runtime registry.

This is deterministic source/control verification only. It is not authentic resident review execution and does not satisfy independent review, activation, or publication.

Current blocker remains `RESIDENT_EXECUTION_RECEIPT_PENDING`; the required authentic receipt is:
`receipts/erl-ai-economic-transparency-review/SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001.json`


## 2026-09-04 runtime-evidence boundary refinement

Live evidence inspection moved the earliest unproven boundary earlier than resident request dispatch.

The canonical native worker entry point already visits `scripts/dispatch_resident_execution_requests.py` every 100 WorkerCoordinator logical ticks when running normally, and the dispatcher/ERL consumer wiring is source-complete. However, the only checked-in worker runtime state is historical:

- `control/worker-runtime-state.json`
- `last_cycle_at`: `2026-08-18T19:47:00Z`
- `runtime_tick`: `2`
- `observation_mode`: `CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION`

That historical state is not evidence of a presently running resident WorkerCoordinator. No current resident-dispatch, ERL request-consumption, targeted-execution, or independent-review receipt is observed.

The bounded ERL evidence record was therefore refined in Executive_Rhetoric_Ledger PR #123 / merge `2d166928843f149020e7e9bd03fb9009b81944e4` to identify:

`RESIDENT_WORKER_RUNTIME_PRESENCE`

as the earliest unproven runtime boundary.

This does not claim that the worker is absent; it records only that present runtime presence is unproven. Source, merge, CI, heartbeat/carrier reference progression, and historical worker state remain insufficient substitutes.

No new scheduler, heartbeat, worker registry, claim/fence path, credential path, second machine, activation authority, publication authority, or repository-writeback authority is introduced. No user action is currently required.


## 2026-09-04 fail-closed worker-presence freshness

Live inspection of `heartbeat_runtime/runtime_presence_projection.py` found that `task_capable_worker_observed` was structural only: it accepted any non-observation-only worker state with an integer runtime tick and did not evaluate whether `last_cycle_at` was fresh. A stale historical worker state could therefore be structurally task-capable without proving present WorkerCoordinator runtime presence.

PR #992 / merge `da51e1f7bcdaa993e627b1af2739195c24bf95ae` hardens the canonical projector while preserving backward compatibility:

- `task_capable_worker_observed` remains the existing structural predicate;
- new `present_worker_runtime_observed` requires direct native-service/continuous-runtime activation predicates, structural task capability, and a parseable `last_cycle_at` within a declared freshness window;
- stale, missing, future-dated, or malformed cycle timestamps fail closed for present-runtime observation;
- the projection exposes `worker_last_cycle_at`, `worker_cycle_age_seconds`, `worker_cycle_fresh`, and `worker_freshness_window_seconds` so the freshness basis is inspectable;
- tests cover both fresh and stale WorkerCoordinator state.

This improves runtime observability only. It does not create runtime presence, execute the ERL reviewer, mint authority, or satisfy the independent-review receipt gate. Present resident WorkerCoordinator runtime presence remains unobserved until fresh runtime-local state and direct activation predicates are authentically present.
