# Hosted Provider InTr Runtime Profile Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Issue: `#1121`
Branch: `feat/provider-intr-runtime-profile-1121`
State: `SOURCE_IMPLEMENTATION_IN_PROGRESS`
Authority effect: `NONE_RUNTIME_PROFILE_PROJECTION_ONLY`

## Source of truth

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `docs/CANONICAL_RUNTIME_PROFILE_MAP_MIRROR_HANDOFF.md`.

The goal is to make optional hosted-provider interoperability resolvable by the existing canonical runtime-profile matcher without creating a second runtime or granting provider authority.

## Existing runtime reused

```text
HB protocol: HB32
heartbeat progression: OSCILLATOR_ONLY
oscillator: independent 100 Hz reference / 10 ms reference increment
worker runtime: WorkerCoordinator
resident dispatcher: existing canonical resident request dispatcher
transition authority: Interlock/InTr
credential authority: TV/TVC
observed reality / custody: Master Records
GitHub token runtime authority: NONE
provider output authority: NONE
```

No new heartbeat, oscillator, scheduler, worker registry, route authority, transition authority, credential authority, custody authority, or hosted availability authority is introduced.

## Missing capability being repaired

The canonical runtime map currently exposes resident process execution and generic InTr ingress, but no worker capability explicitly admits a bounded external provider transport after an exact InTr ingress ALLOW and before a separately required egress decision. Existing sovereign relay capability explicitly excludes outbound EGRESS.

This issue adds a bounded worker capability profile that may be selected only for tasks requiring governed hosted-provider interoperability. Selection remains a non-authorizing projection. WorkerCoordinator claim/fence, task admission, TV/TVC credential materialization, exact InTr ingress/egress decisions, and Master Records evidence remain independently required.

## Intended capability contract

```text
profile_id: hosted-provider-intr-transport-worker-v1
environment: SOVEREIGN_RESIDENT
direction: EGRESS
capabilities:
  - bounded_process_execution
  - hosted_provider_intr_transport
  - execution_scoped_tvtvc_credential_resolution
  - exact_provider_request_hash_binding
  - provider_response_evidence_projection
  - master_records_provider_usage_handoff
mutation_required: true
deployment_required: false
```

`mutation_required` refers only to bounded runtime/evidence state within an admitted task scope. It does not authorize repository, deployment, provider-account, route, credential, or public-state mutation.

## Anthropic #288 binding

`StegVerse-org/LLM-adapter#288` / `stegverse.intr.anthropic.transport.v1` is the first intended consumer. The canonical task projection must require this profile's exact capabilities and retain:

```text
canonical_sovereign_route_replaced: false
hosted_provider_required: false
credential_authority: TV/TVC
transition_authority: Interlock/InTr
provider_output_authority: NONE
live_execution_claim_from_profile_match: false
```

The profile is provider-neutral. Z.ai and future optional hosted-provider transports may use it only when their own task/handoff explicitly binds the same authority and evidence semantics.

## README impact

README impact is REQUIRED because the change adds a new runtime capability meaning. Documentation must state that the profile makes optional provider egress discoverable/selectable but does not prove availability, credential materialization, provider execution, egress ALLOW, custody, or product activation.

## Completion predicates

1. worker capability profile installed with explicit EGRESS environment normalization;
2. canonical runtime-profile map builder projects it without special-case authority;
3. canonical task registry includes the Anthropic #288 runtime requirements;
4. deterministic matcher resolves the #288 task to this profile and does not treat profile match as authority;
5. README/runtime handoff updated;
6. source validation passes;
7. no live Anthropic/Claude execution is claimed without authentic runtime evidence.

## Downstream boundary

This runtime-profile source change does not authorize Site, Publisher, StegIndex, protocol wiki, tag, release, or activation propagation. Those remain governed by the #288 release/evidence predicates.
