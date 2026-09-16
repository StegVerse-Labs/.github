# SDK Elyria Interlock/InTr Adapter Mirror Handoff

Updated: 2026-09-16
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-ELYRIA-INTR-ADAPTER-001`
COSV: `71000000100112`
Status: `ACTIVE / COMPONENTIZED / SOURCE CURRENT / OWNER-OPERATED PUBLIC ENDPOINT NOT DISCOVERED`

## Canonical Goal Task identity

The Goal Task remains `SDK-ELYRIA-INTR-ADAPTER-001`; no restart, rename, successor, or prompt-count reset is justified. Canonical issue remains `#1607`. The task remains ACTIVE because authentic two-way public Elyria transport evidence has not been observed.

## Reusable Task Component Model reconciliation

Canonical model and policy:

```text
data/reusable-task-component-model.json
data/reusable-task-component-decomposition-policy.json
scripts/evaluate_reusable_task_componentization.py
```

Goal-specific component profile:

```text
data/goal-task-component-profiles/SDK-ELYRIA-INTR-ADAPTER-001.json
```

The decomposition score is `25`: task-specific orchestration growth must stop and reusable composition must be used. This changes composition, not Goal Task identity or authority.

Selected components:

```text
RT-EXTERNAL-ADAPTER-ESTABLISH-001  Elyria endpoint translation only
RTC-MANIFEST-001                   manifest intake/binding
RTC-GOVERNED-PROCESSING-002       existing governed processing path
RTC-ROUNDTRIP-003                  public Elyria request/response cycle
RTC-EVIDENCE-CUSTODY-004           evidence custody/readback/reconstruction
RTC-SDK-RETURN-006                 normalized return assembly
RTC-STEGVERSE-EGRESS-007           governed StegVerse-side egress
RTC-INTERLOCK-INTR-TRANSPORT-008   governed packet movement and return
```

Not selected: `RTC-PUBLISHER-005`, `RTC-FARSIDE-FINAL-009`, recurring endpoint monitoring, a new credential/session path, or device-local user verification. Replay and no-bind observations may reuse the round-trip component conditionally; they are not forced into the minimal completion path.

## Source state and validation

Framework-specific source is merged in `StegVerse-org/StegVerse-SDK` PR `#222`:

```text
final head: aeb07d41d83c2a6ae5d84d1a2d8db5cbdc4f540b
merge commit: 41f7c18eaed260d36492e0dd0bcae9c232fb3c77
exact-head validation run: 34709179523
conclusion: SUCCESS
```

The SDK handoff was reconciled to the component model in PR `#225`:

```text
head: 4ed637c34c684463b8617e4d1c5fb3ae71666936
exact-head validation run: 34730774011
conclusion: SUCCESS
merge commit: 5ecb19944019af4bf2432b0a1dad3bda04f9019c
```

The SDK root README already states the generic external-framework manifested processing and governed-interlock model, so no task-specific README mutation is needed.

## Public Elyria endpoint resolution

Canonical public framework source remains:

```text
repository: Kamanaka5502/elyria-admission-runtime
verified public release: v0.8.2-public
assessment route: POST /movements/assess
health route: GET /healthz
```

The public repository exposes local/container reviewer execution and the assessment API surface, but current public discovery still does not identify a separately advertised owner-operated public assessment base URL. Source availability, CI, local execution, injected transport, or repository publication do not satisfy the remaining authentic public round-trip predicate.

Owner direction now explicitly excludes standing up a new third-party reviewer-hosted instance for this task. That path must not be resurfaced as manual work or treated as a prerequisite.

The next admissible transport source is therefore limited to either:

```text
OWNER_OPERATED_PUBLIC_ELYRIA_ENDPOINT
EXISTING_STEGVERSE_SOVEREIGN_PUBLIC_EXECUTION_SURFACE_CAPABLE_OF_AUTHENTIC_EXTERNAL_ROUND_TRIP
```

No new task-specific protocol, transport stack, credential flow, or second user-operated machine may be introduced merely to manufacture the missing observation.

## Authority separation

```text
Task Registry       = coordination only
WorkerCoordinator   = claim/fence authority
Interlock/InTr      = governed admission/state-transition authority
TV/TVC              = credential/provider/release authority
KV/SKAP Vault       = user-verification authority
StegOS devices      = interchangeable transport/execution nodes, not user verifiers
Master Records      = observed-reality custody/reconstruction
HeartBeat           = timing/freshness/liveness/correlation/observability only
GitHub              = source/evidence coordination only
Elyria adapter      = NONE_TRANSLATION_ONLY
```

Elyria verdicts, signatures, replay observations, no-bind material, and route-closure assertions remain foreign observations; they do not become StegVerse authority.

## Predicate state

Satisfied:

```text
EXISTING_STEGVERSE_GOVERNED_PATH_REUSED
NO_DUPLICATE_INTR_PROTOCOL_CREATED
ELYRIA_REQUEST_TRANSLATION_BOUND
ELYRIA_RESPONSE_TRANSLATION_BOUND
TRANSITION_AND_RUN_IDENTITY_PRESERVED
ELYRIA_VERDICT_REMAINS_NON_AUTHORIZING
ELYRIA_RECEIPT_REPLAY_NOBIND_EVIDENCE_PRESERVED
ROUTE_CLOSURE_ASSERTION_DISTINGUISHED_FROM_STEGVERSE_OBSERVATION
FAIL_CLOSED_IDENTITY_AND_SCHEMA_TESTS_PASS
README_AND_HANDOFF_CURRENT
```

Remaining Goal Task-specific predicate:

```text
AUTHENTIC_TWO_WAY_PUBLIC_ELYRIA_TRANSPORT_EVIDENCE_OBSERVED
```

## Next admissible work

1. Continue discovery for an authentic owner-operated public Elyria assessment endpoint.
2. Reuse an already-existing StegVerse sovereign public execution surface only if it can carry the authentic external request/response without changing Elyria semantics or duplicating transport authority.
3. Execute one authentic governed assessment round trip only when one of those surfaces is genuinely reachable.
4. Preserve exact task/run identity and foreign response semantics.
5. Record authentic evidence through Master Records custody/readback.
6. Do not claim private production Veritas interoperability, publication, or a far-side final transition without separate evidence.

## Manual work

None.
