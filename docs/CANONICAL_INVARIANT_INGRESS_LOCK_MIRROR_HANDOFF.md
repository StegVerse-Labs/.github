# Canonical Invariant Ingress Lock Mirror Handoff

Updated: 2026-09-14
Canonical owner: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Registry: `control/canonical-policy-context-registry.json`
Entrypoint: `scripts/session_build_preflight.py`
Authority effect: `NONE_PREWORK_INTERPRETATION_ONLY`

## Purpose

Every StegVerse session, task/COSV continuation, build/implementation pre-work, handoff reconciliation, remediation proposal, source-mutation proposal, and reusable-component decomposition must consume canonical policy context before local interpretation or mutation.

This lock exists because canonical architecture must not be re-derived from task-specific prose after it has already been established.

## Assistant work-entry rule

Before every substantive StegVerse assistant work turn, the assistant must read the current canonical Task Registry documentation from canonical source at that moment before interpreting task state or performing work.

The required read is:

1. the current canonical Task Registry record for the task being worked;
2. the current applicable `*_MIRROR_HANDOFF.md` projection(s) identified by that registry record;
3. all required global sources in `control/canonical-policy-context-registry.json`, including the device-replaceability invariant before any device/KV/runtime interpretation.

The read must come from the current canonical branch/source. A Task Registry or handoff read from an earlier turn, earlier session, cached context, conversation memory, prior validation, prior receipt, prior CI result, or previously observed commit does not satisfy this rule.

If canonical Task Registry documentation changes after it was read and before substantive work continues, the assistant must read the current Task Registry documentation again and reconcile against the new state before proceeding.

This is an assistant work-entry requirement, not a merge-time validation requirement. Passing CI, a validator, a preflight receipt, branch protection, or any other validation artifact cannot substitute for the fresh canonical read.

## Mandatory ingress invariants

1. Canonical source precedes local interpretation.
2. A fresh current Task Registry record plus its applicable handoff projection(s) and required global policy sources precedes every substantive assistant work turn.
3. Prior reads, memory, chat context, validation results, receipts, CI results, or cached task state never substitute for the fresh current Task Registry read.
4. Task-specific wording may parameterize an existing canonical invariant but may not redefine it.
5. A concrete runtime subject, device, repository, worker, provider, or observation target does not create a new architectural role or authority class merely by being named in a task.
6. A local interpretation that conflicts with canonical source is invalid.
7. An existing canonical invariant must be reused, not recreated as new work.
8. Restating an existing canonical invariant is not a new capability and must not by itself create a PR, Goal Task, reusable component, handoff, or policy mutation.
9. A proposed new role, authority owner, identity class, execution owner, verification owner, transport class, or governance role requires evidence that the canonical model lacks an equivalent before source mutation is admissible.
10. When a human correction matches already-canonical truth and no conflicting canonical artifact remains, the required disposition is `NO_SOURCE_MUTATION_REQUIRED`; the correction does not authorize a second artifact that merely restates the same invariant.
11. If active canonical artifacts conflict with the existing invariant, reconcile or supersede those conflicting artifacts rather than teaching the human to work around them.
12. Missing canonical context is an exact dependency. It is never permission to invent replacement semantics.
13. Canonical policy resolution is interpretation-only and grants no execution, claim/fence, credential, transition, custody, publication, release, or user-verification authority.

## Standing device/continuity invariant

The Reusable Task Component Model and `control/device-replaceability-invariant.json` establish the global rule:

- user-operated devices are interchangeable access/transport endpoints;
- no specific phone, computer, browser, OS, Safari session, service worker, IndexedDB instance, browser-local node state, or transport identity may become the sole continuity root or runtime-completion prerequisite;
- KV/SKAP Vault remains the user-continuity/user-verification boundary;
- KV/MyKV provider identity is independent of client-device identity;
- Google Drive, iCloud, and other providers are accessed through provider-neutral KV semantics;
- replacement devices continue from provider-neutral KV plus retained canonical evidence without replaying already-authentic transitions solely because the device changed.

A task may name a particular device because that device carried an observation. That is evidence provenance only. It does not make that device the required continuation surface.

Strings such as `CURRENT_IPHONE_*`, `current-iphone-*`, `same-device-*`, and `ESTABLISHED_CURRENT_IPHONE` are `NON_NORMATIVE_LEGACY_LABELS_ONLY` unless a separate canonical security policy explicitly binds a particular hardware property. They must not be promoted into continuity/runtime architecture by local task prose.

Any instruction such as `do not switch devices`, `preserve this Safari session`, or `use the established current iPhone` is invalid when used as an architectural prerequisite. A bounded observation may ask the user not to mutate evidence during that one observation, but that temporary evidence-preservation request must not become continuity ownership.

## Ingress enforcement path

`control/canonical-policy-context-registry.json` is consumed by `scripts/session_build_preflight.py`. The registry is required before state interpretation, blocker derivation, remediation proposal, new task creation, source mutation, runtime/substrate selection, KV-provider reasoning, or architecture reinterpretation.

Required global device policy sources are:

```text
control/device-replaceability-invariant.json
docs/DEVICE_REPLACEABILITY_INVARIANT_MIRROR_HANDOFF.md
```

The assistant work-entry rule above is stricter than a successful preflight artifact: the assistant must still fetch and read the current canonical Task Registry record and applicable handoff projection(s) for the work turn. Preflight, CI, and retained receipts may support other checks but do not satisfy the fresh-read requirement.

If the registry or a required source cannot be resolved, the existing fail-closed disposition remains:

`STOP_AT_CANONICAL_POLICY_DEPENDENCY`

If local task wording attempts to bind continuity to one device, the required disposition is:

`DEVICE_BOUND_INTERPRETATION_INVALID`

and the task must be rebound to provider-neutral KV plus retained canonical evidence.

This lock changes interpretation discipline only. It does not modify Interlock/InTr packet admission or any runtime authority owner.
