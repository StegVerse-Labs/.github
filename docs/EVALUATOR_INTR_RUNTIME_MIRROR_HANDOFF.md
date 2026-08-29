# Evaluator READ_REVIEW Interlock/InTr Runtime Mirror Handoff

Updated: 2026-08-29
Repository: StegVerse-Labs/.github
Issue: #431
Branch: feat/evaluator-intr-runtime-431

goal_id: EVALUATOR-INTR-READ-REVIEW-RUNTIME-431
state: SOURCE_IMPLEMENTED_MACHINE_OWNER_REGISTERED_VALIDATION_PENDING
site_browser_owner: StegVerse-Labs/Site#643 / PR#644
stegos_transport_owner: StegVerse-Labs/StegOS#94 / PR#95 / merge 93fb030e0d1203197b11d07a77440c3ec788ee91
sdk_ingress_owner: StegVerse-org/StegVerse-SDK#96 / PR#97
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: NONE_READ_ONLY

## First operational milestone

browser exact public projection bootstrap
-> exact test/version/manifest-hash bound READ_REVIEW request
-> browser Interlock Connector
-> InTr DEVICE_SYSTEM -> STEGOS_ECOSYSTEM
-> sovereign READ_REVIEW runtime
-> exact same canonical Site projection
-> InTr STEGOS_ECOSYSTEM -> DEVICE_SYSTEM
-> browser manifest/receipt report

Ingress runtime evidence is transition_state=RECEIVED.
Egress evidence returned with the response is transition_state=FORWARDED.
No later receive acknowledgement is inferred.

## Source

scripts/serve_evaluator_intr_runtime.py is a bounded server:
- only POST /intr/evaluator;
- only READ_REVIEW;
- exact origin, transport header, authorization reference, and body SHA-256 binding;
- exact allowed Site projection path only;
- exact test/version/manifest hash matching;
- StegOS canonical Universal InTr intent and receipt construction;
- write-once runtime receipt bundle;
- no hosted runtime or GitHub-token authority;
- loopback by default; non-loopback requires explicit TLS certificate/key;
- one request by default.

## Non-claims

Source/CI/merge cannot establish a real browser request, real InTr hop, live listener, ingress receipt, egress receipt, public reachability, Master Records custody, approval, freeze, execution, or activation.

## Remaining gates

server source: IMPLEMENTED_ON_BRANCH
focused tests: IMPLEMENTED_ON_BRANCH
resident-runtime task/refresh binding: IMPLEMENTED_ON_BRANCH
validation: PENDING
merge: PENDING
live sovereign listener: NOT OBSERVED
browser connector configuration: NOT OBSERVED
authentic ingress receipt: NOT OBSERVED
authentic egress receipt: NOT OBSERVED
manifest/receipt UI OBSERVED state: NOT OBSERVED


## Machine-owner registration

Installed on this branch:
- workers/evaluator_intr_read_runtime_worker.py
- handoffs/SHWP-EVALUATOR-INTR-READ-RUNTIME-001.json
- control/worker-registry.d/evaluator-intr-read-runtime-001.json
- control/process-worker-adapters.d/evaluator-intr-read-runtime-001.json
- control/task-vectors/SHWP-EVALUATOR-INTR-READ-RUNTIME-001.json
- cost-basis/worker-runtime/evaluator-intr-read-runtime.json
- source-refresh carriage for scripts/serve_evaluator_intr_runtime.py

The worker is fenced independent task control. It treats absent sovereign route configuration/TLS material as machine-observable RoutePending, not as a request for a second user machine. Public bind is prohibited without explicit TLS cert/key paths and boundary identity. Hosted or GitHub-credential-bearing execution fails closed.


## Resident request dispatch integration — 2026-08-29

Follow-on issue: #433.

Installed:
- control/resident-execution-request.d/evaluator-intr-read-runtime-001.json
- scripts/materialize_evaluator_intr_route_config.py
- scripts/consume_evaluator_intr_resident_execution_request.py
- dispatcher registration in scripts/dispatch_resident_execution_requests.py
- native bootstrap/source-refresh carriage
- focused route materialization + consumer tests

Operational topology is now intentionally split:

shared Service Gateway public HTTPS
-> loopback 127.0.0.1 evaluator runtime
-> canonical StegOS Universal InTr

The evaluator runtime no longer owns a second public TLS surface. Its route config contains no secret material; public TLS remains exclusively under the shared Service Gateway / TVC CMC-029 boundary.

The resident request remains retryable while local Site/StegOS roots, node identity, runtime root, or Gateway-side route predicates are absent. Only EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED is terminally consumed.


## Bounded live execution observation — 2026-08-29

Evidence issue: #440
Evidence: `evidence/evaluator-intr/bounded-live-observation-20260829.json`

A bounded live execution used an actual Chromium process, the shared Service Gateway transport adapter, the sovereign evaluator READ_REVIEW runtime, and canonical StegOS Universal InTr receipt generation.

Observed:

```text
browser -> Gateway -> InTr -> evaluator runtime -> egress: OBSERVED_BOUNDED_LIVE_EXECUTION
authentic ingress receipt: OBSERVED_BOUNDED_LIVE_EXECUTION
authentic egress receipt: OBSERVED_BOUNDED_LIVE_EXECUTION

ingress:
  receipt_id: EVAL-IN-ec786d5f45f0de7e24bf0d09
  DEVICE_SYSTEM -> STEGOS_ECOSYSTEM
  transition_state: RECEIVED
  receipt_hash: sha256:47349944c04dec1ea0c1fabfbf7eb1b2c1a02fae7bca5cebac822607944ad984

egress:
  receipt_id: EVAL-OUT-097598820e03794bd150594c
  STEGOS_ECOSYSTEM -> DEVICE_SYSTEM
  transition_state: FORWARDED
  prior_receipt_hash: sha256:47349944c04dec1ea0c1fabfbf7eb1b2c1a02fae7bca5cebac822607944ad984
  receipt_hash: sha256:14b15dd4f65e2be0ec0b045daf8a3b57c6d15453a739544057cccb19ecd04615
```

Both receipt hashes were independently recomputed and the egress prior-receipt link exactly matches the ingress receipt hash. CI validation is installed in `tests/test_evaluator_intr_bounded_live_evidence.py`.

The proof harness used Chromium origin `null` because the container browser could not establish the production HTTPS navigation context. That exception is test-harness-only and is explicitly prohibited from production projection. The production Origin-forwarding defect discovered during activation was fixed separately in `StegVerse-org/LLM-adapter#218/#219`, merge `a723f10a0597742a58ccf5fd10565221019f2b35`.

These observations do NOT establish:

```text
production public Internet route: NOT OBSERVED
public WebPKI hostname verification: NOT OBSERVED
resident sovereign production-host activation: NOT OBSERVED
Master Records custody: NOT OBSERVED
review approval: NOT OBSERVED
freeze: NOT OBSERVED
test execution authority: NOT OBSERVED
```

The transport/receipt implementation has therefore crossed from source-only to bounded live observation. Production route activation remains a separate runtime gate.
