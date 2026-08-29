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
