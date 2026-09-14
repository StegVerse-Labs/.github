# Evaluator READ_REVIEW Interlock/InTr Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Goal Task ID: `EVALUATOR-INTR-READ-REVIEW-RUNTIME-431`
Machine Task: `SHWP-EVALUATOR-INTR-READ-RUNTIME-001`
Canonical owner: `StegVerse-Labs/.github#431`
Repair branch: `fix/evaluator-intr-event-triggered-callable`
Credential authority: `TV/TVC`
GitHub runtime authority: `NONE`
Authority effect: `NONE_READ_ONLY`

## Current truth

The canonical Universal InTr architecture is event-triggered and continuously callable. It does **not** require an always-on application receiver.

Canonical invariants:

```text
event_triggered = true
always_on_application_receiver_required = false
second_user_device_required = false
receiver_unavailable_disposition = DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION
```

The prior machine-owned evaluator worker violated that lifecycle intent by overriding the evaluator server's bounded default with `--max-requests 0`, persisting a PID, and treating `EVALUATOR_INTR_RECEIVER_READY` as a long-lived prerequisite. That persistent-receiver lifecycle is retired as a generic evaluator/InTr prerequisite by this repair.

## Repaired machine-owned lifecycle

The repaired task performs:

```text
admitted machine-owned invocation
-> validate fresh claim/fence and TV/TVC authority boundary
-> observe declared sovereign node + local Site/StegOS/runtime roots
-> observe admitted evaluator route config
-> if authentic prior round-trip receipt exists: terminalize
-> otherwise materialize one bounded READ_REVIEW call surface
   scripts/serve_evaluator_intr_runtime.py --max-requests 1
-> confirm bounded call surface is callable
-> retain event-receiver.latest.json with:
     event_triggered=true
     persistent_receiver=false
     always_on_application_receiver_required=false
-> one admitted READ_REVIEW request consumes that call surface
-> canonical InTr ingress RECEIVED receipt
-> canonical InTr egress FORWARDED receipt
-> retained write-once round-trip bundle
-> later invocation terminalizes on EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED
```

A still-live one-request call surface may be reused to avoid binding a duplicate listener to the same route. It is not promoted into an always-on receiver and exits after the bounded request is consumed.

## Existing functional evidence retained

A bounded live execution previously used an actual Chromium process, the shared Service Gateway adapter, the evaluator READ_REVIEW runtime, and canonical StegOS Universal InTr receipt generation. The retained evidence established:

```text
browser -> Gateway -> InTr -> evaluator -> egress: OBSERVED_BOUNDED_LIVE_EXECUTION
ingress transition_state: RECEIVED
egress transition_state: FORWARDED
egress prior_receipt_hash: exact ingress receipt hash
```

Retained receipt identities:

```text
ingress receipt_id: EVAL-IN-ec786d5f45f0de7e24bf0d09
ingress receipt_hash: sha256:47349944c04dec1ea0c1fabfbf7eb1b2c1a02fae7bca5cebac822607944ad984
egress receipt_id: EVAL-OUT-097598820e03794bd150594c
egress receipt_hash: sha256:14b15dd4f65e2be0ec0b045daf8a3b57c6d15453a739544057cccb19ecd04615
```

That bounded live proof remains evidence that the READ_REVIEW function and receipt lineage can execute. It is not evidence that a permanently available service is required.

## Canonical reusable transport

Evaluator request/projection validation remains evaluator-specific. InTr packet construction and receipt semantics use the canonical StegOS profile:

```text
profile = evaluator-read-review
source = DEVICE_SYSTEM / Site:EvaluatorReview
destination = STEGOS_ECOSYSTEM / SDK:EvaluatorReviewIngress
backbone = stegos.intr_backbone.CanonicalInTrConnector
always_on_receiver_required = false
second_user_device_required = false
```

The Site device-local Universal InTr service worker independently advertises `SDK:EvaluatorReviewIngress` through `/intr/profile` with `event_triggered=true` and `always_on_application_receiver_required=false`, and its evaluator path accepts canonical Node materialization triggers at `/intr/materialization`.

## Repair source

Changed on `fix/evaluator-intr-event-triggered-callable`:

- `workers/evaluator_intr_read_runtime_worker.py`
  - replaces `ensure_receiver()` persistent lifecycle with `ensure_callable()`;
  - replaces `--max-requests 0` with `--max-requests 1`;
  - replaces persistent readiness state with `EVALUATOR_INTR_EVENT_RECEIVER_CALLABLE`;
  - records `event_triggered=true`;
  - records `persistent_receiver=false`;
  - records `always_on_application_receiver_required=false`;
  - preserves terminalization only on authentic `EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED` evidence.
- `tests/test_evaluator_intr_read_runtime_worker.py`
  - protects one-request event materialization;
  - rejects regression to persistent receiver semantics;
  - verifies an already-live bounded call surface is reused rather than creating a duplicate listener;
  - preserves hosted-runtime and credential fail-closed behavior.
- `handoffs/SHWP-EVALUATOR-INTR-READ-RUNTIME-001.json`
  - removes durable receiver readiness as a success predicate;
  - makes bounded event-triggered callability the nonterminal state.

## Validation requirements

The repair is valid only when exact-head tests establish all of the following:

```text
worker invocation claim/fence validation: PASS
missing route remains machine-retryable: PASS
public route without explicit TLS fails closed: PASS
prior authentic round-trip terminalizes without new listener: PASS
new evaluator call surface uses --max-requests 1: PASS
event_triggered=true: PASS
persistent_receiver=false: PASS
always_on_application_receiver_required=false: PASS
live bounded call surface is reused without duplicate listener: PASS
hosted execution fails closed: PASS
existing evaluator runtime/receipt tests remain green: PASS
```

Source, CI, merge, and a `CALLABLE` record do not by themselves prove a fresh production request traversed the route. Fresh runtime completion remains authentic receipt evidence only.

## Post-repair observation attempt — 2026-09-14

After merge `eb0f2687265c62a7e621dd22d10cd5da3c2bf591`, the canonical Task Registry and this handoff were re-read before attempting runtime execution.

Observed canonical state:

```text
SHWP-EVALUATOR-INTR-READ-RUNTIME-001 = HANDOFF_READY
worker status = AVAILABLE
fresh runtime completion evidence = NOT OBSERVED
fresh EVALUATOR_INTR_EVENT_RECEIVER_CALLABLE receipt = NOT OBSERVED
fresh EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED receipt = NOT OBSERVED
```

An authorized remote-runtime execution attempt from the current session could not reach a resident device because the connected remote execution surface reported no available device. This is an **observation/execution-surface limitation**, not evidence that the StegVerse resident runtime is absent or broken. No CI, source, historical receipt, or connector error is promoted into runtime proof.

The first exact unresolved goal predicate therefore remains:

```text
FRESH_AUTHENTIC_POST_REPAIR_READ_REVIEW_INVOCATION_OBSERVED = false
```

Required next authentic evidence is unchanged:

```text
one admitted post-repair READ_REVIEW invocation
-> event-triggered one-request call surface
-> exact request/manifest binding
-> ingress transition_state=RECEIVED
-> egress transition_state=FORWARDED
-> egress prior_receipt_hash == ingress receipt_hash
-> retained EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED bundle
```

No additional listener, runtime plane, scheduler, credential authority, or second user-operated device is authorized by this observation gap.

## Existing carrier/bootstrap reconciliation — 2026-09-14

The next execution-first pass verified that the evaluator lane itself is already wired into the existing resident carrier:

```text
control/resident-execution-request.d/evaluator-intr-read-runtime-001.json = REQUESTED
scripts/bootstrap_sovereign_runtime.py carries evaluator consumer/materializer
scripts/dispatch_resident_execution_requests.py routes evaluator_intr
scripts/consume_evaluator_intr_resident_execution_request.py targets SHWP-EVALUATOR-INTR-READ-RUNTIME-001
```

No missing evaluator registration, dispatcher, listener, runtime plane, or credential path was found.

The first concrete runtime predicate before evaluator claim/fence is the existing standing Healer scheduler carrier. Its canonical registry currently records:

```text
SHWP-HEALER-SOVEREIGN-SCHEDULER-001 = HANDOFF_READY
claim_id = null
heartbeat_timing = null
last_seen_at = null
worker status = AVAILABLE
archive reason includes HEALER_NO_TOKEN_SOVEREIGN_SCHEDULER_NOT_YET_LIVE_PROVEN
```

The standing Healer request self-materialization source repair already exists and expressly preserves WorkerCoordinator claim/fence authority. Therefore no additional source implementation was authorized or necessary in this pass.

The first failing runtime predicate is now classified as:

```text
EXISTING_HEALER_STANDING_CARRIER_FRESH_CLAIM_FENCE_OBSERVED = false
```

Bounded owner remains the already-existing `SHWP-HEALER-SOVEREIGN-SCHEDULER-001` carrier; this does not create a new evaluator dependency task or parallel remediation lane. Required evidence is one authentic resident scheduler cycle that produces its normal live scheduler receipt and then allows the existing evaluator standing request to proceed into its own fresh WorkerCoordinator claim/fence.

The absence of an externally connected remote-control device is not the blocker classification and does not imply a second user-operated device requirement.

## README disposition

Root `README.md` was reviewed for this repair. It already documents the organization-owned Universal InTr ingress as event-triggered and describes event materialization through the shared profile. No repository-wide semantic rewrite is required; this repair removes the contradictory evaluator-specific persistent-receiver lifecycle so the task conforms to those existing README semantics.

## Remaining runtime predicate

After merge, the task remains machine-owned and nonterminal until one authentic post-repair READ_REVIEW round trip is observed and retained:

```text
EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED
```

The immediate upstream release condition is now the existing Healer standing carrier producing a fresh authentic claim/fence cycle and scheduler receipt; after that, the evaluator standing request remains the same authorized owner for the READ_REVIEW invocation.

No production activation, public WebPKI reachability, review/approval/freeze/execution authority, or Master Records custody is inferred from source validation.
