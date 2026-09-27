# Manifest / Task Registry / Transition Receipt Join Mirror Handoff

Updated: 2026-09-27
Repository: `StegVerse-Labs/.github`
Companion repository: `StegVerse-org/StegVerse-SDK`
Goal Task ID: **unregistered — see §8**
Status: `SPEC ONLY / NO SOURCE MUTATION / NO REGISTRATION`

## 1. Purpose

`ECOSYSTEM_STATE_TRANSITION_DISPOSITION_INVARIANT.md` requires every requested
operation to be an attempted state transition resolved from an admitted
manifest, and `.stegverse/transition-ledger/org-contract.json` requires that
`EVERY_STATE_TRANSITION_OCCURRING_WITHIN_THE_ORGANIZATION_EMITS_AN_ORGANIZATION_RECEIPT`.

Three components exist to satisfy this. None of them are connected:

| Component | Where | State |
| --- | --- | --- |
| Ingress manifest — determines capability and route | SDK `schemas/stegverse.ingress-manifest.v1.schema.json` | built |
| Canonical task registry — owns transitions and their COSV vectors | `.github data/canonical-task-records/` | built |
| Repo/Org transition ledger — records transitions as receipts | `.github .stegverse/transition-ledger/` | built |

The manifest does not name a task. The task does not name a manifest. Neither
emits a receipt. This document specifies the three joins and nothing else.

## 2. Evidence that the joins are absent

- No SDK source under `stegverse/` references `canonical-task-record`,
  `canonical_task_record` or `canonical-task-registry`.
- Across all canonical task records, exactly one record carries
  `capability_evaluation`, one `proven_route_reuse`, one
  `canonical_route_duplication_binding`. No record carries `manifest_hash`,
  `processing.capability` or `route_id`. That is noise, not a convention.
- Neither `SDK_GENERIC_MANIFEST_TASK_REGISTRY_REGISTRATION_MIRROR_HANDOFF.md`
  nor `SDK_GENERIC_MANIFEST_ECOSYSTEM_INVARIANT_MIRROR_HANDOFF.md` states a
  manifest-binding convention for records.
- `scripts/validate_task_registration_substrate_resolution.py` hardcodes
  `REVIEW_ORDER` (six substrates) and `DISPOSITIONS` (five values) as module
  constants, and enforces `len(reviews) == 6` in fixed order. A transition space
  that the invariant says the manifest determines is fixed in a validator file.
- `scripts/evaluate_task_registry_collision_checkin.py` emits
  `STOP_SUBSTRATE_REVIEW_REQUIRED` carrying `substrate_review_error: str(exc)` —
  a stringified Python exception — and emits no receipt of any kind.

## 3. Join A — canonical task record names its manifest

**Blocked by a prerequisite.** `schemas/canonical-task-record.schema.json`
declares `additionalProperties: false` over 25 properties. The merged record
`STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001` has 31 keys, of which **ten are
not permitted by that schema**: `authority_effect`, `checkout_state`,
`cosv_task_vector`, `device_interchangeability_enforced`,
`governing_invariant_ref`, `nonclaims`, `physical_device_identity_gate`,
`registration`, `repository`, `work_units`.

`checkout_state`, `cosv_task_vector` and `repository` are core registry
concepts read by the collision evaluator and the COSV index. The schema is
stale, not the records.

The constraint is currently dormant: `validate_canonical_work_coordination.py`
loads `TASK_SCHEMA` at line 35 and never applies it — the file contains no
`jsonschema` import and no `validate(` call. So a new key works at runtime
while violating the declared contract.

**Therefore A is two steps, in order:**

**A1. Reconcile the schema to the record model.** Add the ten keys above.
Adding an eleventh violation instead would bury the join in a contract nobody
can enforce.

**A2. Add the binding**, as a new optional record property:

```json
"manifest_binding": {
  "manifest_profile": "stegverse.ingress-manifest",
  "manifest_profile_version": "v1",
  "manifest_sha256": "sha256:...",
  "processing": { "capability": "<capability>", "route_id": "<route_id>" },
  "authority_effect": "NONE"
}
```

`processing.capability` and `processing.route_id` mirror the manifest's own
required `processing` object exactly, so the record states the transition space
it was admitted under. Optional at introduction; required only after §7 step 4.

## 4. Join B — ingress manifest names its canonical task

The ingress manifest root declares `additionalProperties: false`, so **no
top-level field may be added**. `processing` and `completion` are likewise
closed.

`extensions` declares `additionalProperties: true`, requires `stegverse_route`,
and already carries a second member, `stegverse_governance_request`. That is
the sanctioned extension point and the precedent for using it.

**Add `extensions.stegverse_canonical_task`:**

```json
"stegverse_canonical_task": {
  "task_id": "<canonical task id>",
  "correlation_id": "<correlation id>",
  "registry_repository": "StegVerse-Labs/.github",
  "observed_registry_generation": 262,
  "cosv_task_vector": "<vector>",
  "authority_effect": "NONE"
}
```

This requires **no schema change** — it is additive under an already-open
object. `context_refs` (array of strings) is the weaker alternative and is not
recommended: it is untyped and cannot carry the generation fence.

`observed_registry_generation` is load-bearing. The collision evaluator already
fences on it, returning `STOP_COORDINATION_GENERATION_REQUIRED` when absent and
`STOP_STALE_COORDINATION` when behind. Carrying it in the manifest lets an
ingressing machine be fenced at ingress rather than discovering staleness later.

## 5. Join C — the transition disposition emits a receipt

`.stegverse/transition-ledger/emit.py` already produces
`stegverse.repo-transition-receipt/v1` with a hash chain: it reads `HEAD.json`
for `previous_receipt_sha256`, computes `receipt_sha256` over the body, writes
`receipts/<digest>.json`, refuses a digest collision with differing content, and
advances HEAD. Its CLI takes `--transition-id`, `--transition-class`,
`--predecessor-state-sha256`, `--successor-state-sha256`, `--evidence-json`,
`--authority-effect`, `--hb-ref`.

The receipt body has no `disposition` field, and `evidence` is free-form JSON.
**`evidence` is where the transition-disposition receipt goes**, carrying the
fields the invariant requires on every non-ALLOW:

```json
{
  "disposition": "STOP_SUBSTRATE_REVIEW_REQUIRED",
  "failure_code": "...",
  "failed_predicate": "...",
  "required_evidence_or_repair": "...",
  "retry_entrypoint": "...",
  "owning_existing_goal": "<task id>",
  "next_attempt": "...",
  "manifest_sha256": "sha256:...",
  "consequence_committed": false
}
```

This replaces `substrate_review_error: str(exc)`. A stringified exception cannot
be aggregated; these fields can.

**Non-commit is machine-checkable.** The invariant says non-ALLOW "must not
mutate the denied consequential state." In receipt terms that is exactly
`predecessor_state_sha256 == successor_state_sha256`. A non-ALLOW receipt whose
two state hashes differ is a contract violation detectable without reading the
evidence, and `consequence_committed: true` may appear only on an evidenced
ALLOW. This is a validator that can be written the day receipts start flowing.

**Note on custody.** The ledger root is `STEGVERSE_REPO_LEDGER_ROOT`, defaulting
to `~/.local/state/stegverse/repo-ledgers/<repository>`. Receipts live outside
the repository and are not committed. Any workflow-emitted receipt on an
ephemeral runner is lost unless propagated. Deciding that propagation path is a
prerequisite to wiring emission into CI, and is **not specified here**.

## 6. What the joins unlock

- **Substrate review becomes manifest-determined.** With A2 and B in place, the
  review covers the transition space the manifest admits instead of a hardcoded
  six. An unadmitted route is not dispositioned `NOT_APPLICABLE`; it is absent.
- **The 37-record backfill becomes derivable rather than authored.** Today it
  would be 37 hand-written judgments in a vocabulary that does not conform.
- **`PENDING_EVIDENCE` loses its purpose.** It is what one writes when the
  manifest does not determine the answer. When the manifest determines it, the
  disposition is `ALLOW`, a named non-ALLOW with its predicate and retry edge,
  or the substrate is out of scope.
- **Nonclaims become derivable.** `NO_RUNTIME_OBSERVATION_OF_WORKSPACE_IS_CLAIMED`
  is presently a sentence. With receipts, the absence of an evidenced ALLOW for
  that task is the proof.
- **The backlog self-reports.** The 42 records currently failing
  `validate_resolution` are invisible until `scripts/audit_execution_substrate_resolution.py`
  is run by hand. Under C each blocked check-in emits a receipt naming its
  predicate.

## 7. Migration sequence — non-breaking at every step

1. **A1** reconcile `canonical-task-record.schema.json` to the record model.
   No record changes. Nothing enforces it yet, so nothing breaks.
2. **B** add `extensions.stegverse_canonical_task` to manifests. Additive under
   an open object; no schema change; old manifests stay valid.
3. **A2** add optional `manifest_binding` to records. Optional, so no record is
   invalidated.
4. **C** emit receipts on transition dispositions, starting with
   `STOP_SUBSTRATE_REVIEW_REQUIRED`, after the §5 custody decision.
5. Only then: make `manifest_binding` required for runtime-capable records,
   derive substrate scope from the manifest, and retire the hardcoded
   `REVIEW_ORDER` / `DISPOSITIONS` constants.
6. Only then: enforce the reconciled record schema, and wire
   `audit_execution_substrate_resolution.py --strict` to CI.

Steps 1–4 change no existing record and invalidate no existing manifest.

## 8. What this document does not do

- **It registers nothing.** This specification is itself a mutation proposal
  with no canonical Goal Task ID. Under
  `scripts/evaluate_task_registry_collision_checkin.py`, absence returns
  `STOP_NOT_REGISTERED / END_OR_REGISTER_BEFORE_MUTATION`. Registration must
  precede any implementation, exactly as
  `SDK_GENERIC_MANIFEST_TASK_REGISTRY_REGISTRATION_MIRROR_HANDOFF.md` records
  for the SDK propagation goal.
- **It claims no runtime observation.** Nothing here was executed against a
  live manifest, ingress path, ledger or device. Every statement above is a
  source read of the named file at the named commit.
- **It does not repair the 42 non-conforming records**, the dormant record
  schema, the hardcoded validator constants, or the stringified
  `substrate_review_error`.
- **It decides no substrate disposition vocabulary.** §6 states what the joins
  make possible; the vocabulary itself is determined by the manifest, which is
  the point.
- **It grants no authority.** `authority_effect: NONE` throughout.

## 9. Validation plan

Each join is testable before anything depends on it:

| Join | Test |
| --- | --- |
| A1 | Every record under `data/canonical-task-records/` validates against the reconciled schema — currently ten keys fail on at least one record. |
| A2 | A record with `manifest_binding` validates; `processing.capability`/`route_id` match the referenced manifest's own `processing` object. |
| B | A manifest with `extensions.stegverse_canonical_task` validates against the unmodified `stegverse.ingress-manifest.v1` schema. |
| C | A non-ALLOW receipt has `predecessor_state_sha256 == successor_state_sha256` and `consequence_committed: false`; an ALLOW receipt with equal state hashes fails. |
| chain | `previous_receipt_sha256` links to HEAD before append; a gap or fork is detected. |
