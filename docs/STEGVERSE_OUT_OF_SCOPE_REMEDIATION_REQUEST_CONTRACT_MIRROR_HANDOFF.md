# Out-of-Scope Remediation Request Contract Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEGVERSE-OUT-OF-SCOPE-REMEDIATION-REQUEST-CONTRACT-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `RETIRED / SOURCE CONTRACT MERGED+VALIDATED / FIRST HEALER EVALUATION REQUEST MATERIALIZED / NO HEALER TRIGGER OR REMEDY CLAIMED`

## Validation evidence

- `.github` PR: `#1911`
- validated head: `faa1c77f65006514b251ff92bc152f78acb8b81a`
- merge commit: `e4775d3844a46ad4ee45a751ff559c100a183b7f`
- organization-control run `34919182490`: PASS
- deterministic repository suite run `34919182479`: PASS
- heartbeat validation run `34919182505`: PASS
- StegVerse-Healer evaluation-request PR `#86`: merged as `3be626ab1ec90e766c50221cff6b9ed690947647`

GitHub/CI proves source-contract validation only. It does not prove a Healer trigger or remediation.

## Purpose

When a Goal observes an actual broken condition whose owning domain is outside that Goal, the Goal must not silently widen scope and repair the foreign subsystem. It retains exact evidence, classifies ownership, emits a remediation evaluation request to StegVerse-Healer, and continues work that does not depend on the foreign defect.

The request is not a Healer trigger, does not transfer authority, and does not authorize a remedy. StegVerse-Healer independently evaluates whether an authorized remediation trigger applies.

Canonical contract:

`data/out-of-scope-remediation-request-contract.json`

## Coordination sequence

```text
observed broken condition
-> retain exact failure evidence
-> classify owning domain
-> OUT_OF_SCOPE_FOR_CURRENT_GOAL=true
-> classify blocking vs nonblocking for the originating transition
-> emit StegVerse-Healer remediation evaluation request
-> no authority transfer
-> StegVerse-Healer independently evaluates authorized trigger predicates
-> if matched: bounded remedy + remediation evidence
-> if unmatched: retain/route without inventing remedy
-> if blocking: return to the interrupted GC transition after admissible remediation evidence
-> if nonblocking: originating Goal continues independently
```

## First fixture — GADI compatibility mismatch

Observed during StegBrowser source validation:

`GADI_SOURCE_SCHEMA_TEST_API_MISMATCH`

The GADI deterministic test fixture referenced `retained_projector.SOURCE_SCHEMA` while the projector exposed `SOURCE_SCHEMAS` as the accepted-schema set.

Classification:

```text
OWNING_DOMAIN = GADI
OUT_OF_SCOPE_FOR_CURRENT_GOAL = true
BLOCKS_ORIGINATING_TRANSITION = false
AUTHORITY_TRANSFER = NONE
ORIGINATING_GOAL_ACTION = RETAIN_EVIDENCE_EMIT_REQUEST_CONTINUE_STEGBROWSER_SPECIFIC_VALIDATION
```

The fixture proves routing semantics only. It does not authorize or apply a GADI repair.

## GC exception overlay

This branch is orthogonal to normal GC stages A0-A7, B1, and C1-C4.

At any GC transition:

### X1 — Observe actual broken condition

A pending predicate by itself is not enough.

Completion:

`OBSERVED_BROKEN_CONDITION = true`

### X2 — Retain evidence and classify owner/scope

Required:

```text
EXACT_FAILURE_EVIDENCE_RETAINED = true
OWNING_DOMAIN_CLASSIFIED = true
OUT_OF_SCOPE_FOR_CURRENT_GOAL = true
```

### X3 — Classify impact on current transition

Nonblocking:

`blocks_originating_transition=false`

Blocking:

`blocks_originating_transition=true` plus exact `interrupted_gc_transition`.

### X4 — Emit Healer remediation evaluation request

Required:

```text
HEALER_REMEDIATION_REQUEST_EMITTED = true
AUTHORITY_TRANSFER = NONE
HEALER_TRIGGERED = false
```

The last predicate means request emission alone does not trigger remediation.

### X5 — Independent Healer trigger evaluation

StegVerse-Healer determines whether an authorized remediation trigger matches.

Outcomes:

- `AUTHORIZED_TRIGGER_MATCHED_APPLY_BOUNDED_REMEDY`
- `NO_AUTHORIZED_TRIGGER_MATCH_RETAIN_OR_ROUTE_WITHOUT_REMEDY`
- `INSUFFICIENT_EVIDENCE_REQUEST_MORE_EVIDENCE`

### X6 — Continue or return

Nonblocking defect:

`CONTINUE_CURRENT_GOAL_UNRELATED_TRANSITIONS`

Blocking defect after admissible remedy evidence:

`RETURN_TO_INTERRUPTED_GC_TRANSITION`

The originating Goal never becomes owner of the foreign remediation merely because it observed the failure.

## Authority boundaries

- Originating Goal: own-domain work only.
- StegVerse-Healer: independent trigger evaluation and bounded remedy only after an authorized trigger matches.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: transition authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification authority.
- Master Records: observed-reality/reconstruction authority.
- GitHub/CI: source validation/evidence only; runtime authority `NONE`.
- Healer is not a normal GC stage owner, scheduler, carrier, or prerequisite.

## Manual work

None.
