# StegDB Organization Role Version Propagation 002 Mirror Handoff

Goal Task ID: `STEGDB-ORGANIZATION-ROLE-VERSION-PROPAGATION-002`
Predecessor: `STEGDB-ORGANIZATION-ROLE-VERSION-PROPAGATION-001` (`RETIRED / COMPLETED`, not reopened)
COSV: `10000000100000`
Coordination: `ACTIVE / UNCLAIMED`
Owner: `StegVerse-Labs/StegDB`
Admission: StegVerse-Labs/TVC#488, item `O1-REG`, approved in comment 6070675863 and planned in comment 6070722044 (work item W6).

## Goal
Bounded Organization Role version propagation. Compare the exact canonical reference coordinates with the StegDB and SV-LLM source identity and manifest contract. Then carry each stale adopter to the current Organization Role version through manifest-bound Interlock/InTr conformance transitions. Each attempted transition ends `ALLOW`, `DENY` or actionable `FAIL_CLOSED`.

## Reported drift
The issue reports that StegDB binds Organization Role commit `702f896` and SV-LLM has adopted `60ddd13`. This admission records that report. It has not re-verified it. The first remaining predicate is the exact comparison.

## Boundary
- The predecessor's registry, comparison and conformance-work semantics are reused unchanged. No new registry, store or authority plane.
- StegDB holds version, adoption, migration and conformance state only. It does not install into or mutate adopter repositories.
- Interlock/InTr owns the transitions. Each Organization owns its runtime reality in its own ledger. TV/TVC owns credentials. Master Records holds organization records and reconstruction only and gates nothing.
- No external machine, listener or session is awaited. If a receiver is unavailable, the work goes to `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION`.
- This work does not block unrelated O1 work.

## Remaining predicates
- `O1_REG_EXACT_CANONICAL_REFERENCE_STEGDB_AND_SV_LLM_SOURCE_IDENTITY_COMPARED`
- `O1_REG_STALE_ADOPTER_SET_DERIVED_FROM_CANONICAL_STATE`
- `O1_REG_STEGDB_ROLE_VERSION_BINDING_ADVANCED_BY_MANIFEST_BOUND_TRANSITION`
- `O1_REG_EACH_ATTEMPTED_CONFORMANCE_TRANSITION_TERMINAL_ALLOW_DENY_OR_ACTIONABLE_FAIL_CLOSED`
- `O1_REG_EXACT_HEAD_REQUIRED_CI_GREEN`

## Completion
Nothing is claimed complete. Close each predicate only with evidence of its own class. Source, CI or merge evidence is never promoted to runtime migration.
