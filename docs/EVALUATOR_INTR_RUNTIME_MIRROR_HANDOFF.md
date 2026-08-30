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


## Surface-independence / provenance clarification — 2026-08-29

The evaluator runtime admits a transported interaction; it does not derive canonical authority from the browser, hostname, Site mirror, operating system, or device that carried the interaction.

The runtime distinction is:

```text
canonical instruction/provenance
  = repository/path/revision/hash governing the operation

interaction surface
  = replaceable projection where the interaction was observed

browser network origin
  = optional web transport-security fact

receiving authority
  = canonical receiving subsystem / policy boundary
```

Accordingly, `https://stegverse.org` MUST NOT become a prerequisite for evaluator authority or runtime semantics. A browser-origin check may protect a particular web ingress adapter, but equivalent admitted ingress through StegOS, a native application, a local/offline UI, a sovereign device/node surface, or another future transport must remain possible without changing the underlying governance contract.

No interaction surface, hostname, operating system, device class, network presentation layer, or third-party platform may become a condition for StegVerse authority, provenance, admissibility, or continuity.

This is a terminology/current-lane reconciliation only; it does not create a new authority source.


## Healer shared-Gateway route projection — 2026-08-29

The resident evaluator route materializer already writes a non-secret exact loopback configuration at the deployment-local sovereign surface. This branch wires that state into the existing Healer shared-Gateway worker without creating a second transport or configuration authority.

Projection rule:

```text
materialized evaluator route config
  schema = stegverse.evaluator-intr-route-config/v1
  host = 127.0.0.1
  valid admitted port
  credential_authority = TV/TVC
  github_token_runtime_authority = NONE
  public_tls_terminated_by = STEGVERSE_SHARED_SERVICE_GATEWAY

-> Healer child env:
   STEGVERSE_EVALUATOR_INTR_ENABLED=true
   STEGVERSE_EVALUATOR_INTR_UPSTREAM=http://127.0.0.1:<port>/intr/evaluator
```

Any missing, malformed, remote-host, authority-drifted, or non-shared-Gateway config projects:

```text
STEGVERSE_EVALUATOR_INTR_ENABLED=false
STEGVERSE_EVALUATOR_INTR_UPSTREAM=
```

The config file path itself is not forwarded to Healer. TLS/private-key locators remain excluded from the worker boundary and continue through same-host TVC receipt discovery.

This projection does not infer evaluator listener liveness, public Gateway activation, or browser receipt observation. It only removes the configuration gap that would otherwise keep the merged native Gateway evaluator route disabled after lawful route materialization.


## Durable resident READ_REVIEW receiver — 2026-08-29

The prior evaluator worker used a one-request foreground listener. That was sufficient for bounded proof but not for an operational public Gateway because a browser request could arrive while no listener existed.

Issue #449 changes the machine-owned lifecycle to:

```text
route predicates satisfied
-> start persistent same-host loopback READ_REVIEW receiver
-> GET /intr/evaluator/readiness = READY
-> persist receiver.latest.json
-> worker remains ACTIVE / EVALUATOR_INTR_RECEIVER_READY
-> shared Gateway may forward admitted browser requests
-> runtime persists authentic ingress/egress bundle
-> later worker cycle observes bundle
-> terminal EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED
```

Readiness and transport proof remain distinct:

```text
EVALUATOR_INTR_RECEIVER_READY != EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED
```

The receiver remains:

- loopback-only under the current route materializer;
- behind the shared Service Gateway for public TLS;
- READ_REVIEW only;
- hosted-runtime forbidden;
- GitHub/non-TV-TVC credential forbidden;
- authority_effect=NONE;
- persistent until resident lifecycle control stops/restarts it.

The runtime now exposes a bounded authority-neutral GET readiness surface and accepts `--max-requests 0` for persistent serving. A real READ_REVIEW request is still required before the task can terminalize.


## Canonical reusable backbone migration — 2026-08-30

Issue #556 migrates the evaluator runtime from connector-local transport
construction to the merged StegOS reusable backbone:

```text
profile: evaluator-read-review
backbone: stegos.intr_backbone.CanonicalInTrConnector
StegOS backbone merge: c4182a696b33c6bbaaa8ec0c5382f83fc4befc2c
transition-state extension merge: 948916ff15efeef45a36fcd6d9af46e587c35cc9
```

Evaluator request/projection validation remains evaluator-specific. Intent
construction, exact-packet hashing, hop-receipt issuance, complete-chain
validation, reverse response construction, authority invariants, and receiver
availability semantics now come from the canonical backbone/profile registry.

Local validation:

```text
runtime unit tests: 6/6 PASS
evaluator + current StegOS integration: PASS
ingress RECEIVED: PASS
egress FORWARDED: PASS
egress prior-hash linkage: PASS
write-once canonical profile/result bundle: PASS
```

This migration does not supersede or manufacture the retained 2026-08-29
bounded live observation. Public HTTPS, resident production activation, and
Master Records custody remain separately unobserved.
