# Canonical Policy Context Preflight Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Canonical owner goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Parent: `docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md`
Status: `SOURCE_IMPLEMENTED / DEVICE-REPLACEABILITY REQUIRED / VALIDATION PENDING`
Authority effect: `NONE_PREWORK_INTERPRETATION_ONLY`

## Purpose

Every StegVerse session/build/task interpretation must resolve canonical policy before deriving task state, blockers, remediation, runtime substrate, KV provider behavior, or new work.

This exists to prevent local task wording from silently redefining canonical architecture.

## Required global policy context

Canonical registry:

```text
control/canonical-policy-context-registry.json
```

Required global sources include at minimum:

```text
data/task-coordination-policy.json
docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md
data/reusable-task-component-model.json
control/device-replaceability-invariant.json
docs/DEVICE_REPLACEABILITY_INVARIANT_MIRROR_HANDOFF.md
docs/CANONICAL_INVARIANT_INGRESS_LOCK_MIRROR_HANDOFF.md
```

Task-declared `canonical_policy_refs` are additionally mandatory.

## Device-replaceability preflight rule

Before any device/runtime/KV reasoning, preflight must resolve the global invariant that user-operated devices are interchangeable access/transport endpoints.

The following local interpretations are invalid even when an active task or historical handoff contains those words:

- one particular iPhone is required to continue the task;
- `CURRENT_IPHONE_*` is a current architectural identity;
- `same-device` is a required completion predicate;
- Safari, IndexedDB, service-worker state, or browser-local node state is canonical continuity;
- Google Drive/iCloud/provider-backed KV identity is coupled to whichever device is currently accessing it;
- changing devices requires replay of already-authentic transitions solely because the device changed.

Strings such as `CURRENT_IPHONE_*`, `current-iphone-*`, `same-device-*`, and `ESTABLISHED_CURRENT_IPHONE` may remain in immutable evidence and implementation symbols only as `NON_NORMATIVE_LEGACY_LABELS_ONLY`.

If local task wording conflicts with the replaceability invariant, preflight disposition is:

```text
DEVICE_BOUND_INTERPRETATION_INVALID
```

The continuation must be rebound to provider-neutral KV/MyKV plus retained canonical evidence rather than asking the human to preserve a device.

## Fail-closed behavior

If a required canonical policy ref cannot be resolved:

```text
STOP_AT_CANONICAL_POLICY_DEPENDENCY
```

Missing policy is an exact dependency and never permission to infer replacement semantics.

## Authority boundary

Policy-context resolution does not prove runtime truth, renew claims/fences, authorize Interlock/InTr transitions, grant TV/TVC credentials, grant custody, or create a runtime.

It constrains interpretation only.

## Validation

Regression coverage now includes:

```text
tests/test_canonical_policy_context_preflight.py
tests/test_device_replaceability_invariant.py
scripts/validate_device_replaceability_invariant.py
```

The device validator requires:

1. no specific device continuity authority;
2. no specific device runtime-completion prerequisite;
3. provider-neutral KV/device independence;
4. replacement-device reconstruction from KV plus retained evidence;
5. the global runtime closure task to use `TESTFLIGHT_AUTHORIZED_USER_DEVICE_RUNTIME_OBSERVED` rather than a device-specific current predicate;
6. legacy current-iPhone/same-device labels to be explicitly non-normative.

## Adoption

All tasks receive the global policy context even when they do not declare task-specific policy refs. Therefore a task-specific handoff cannot lawfully reintroduce a device-bound prerequisite by omission.

The intended steady state is that the human supplies only task intent/observations; canonical device, authority, continuity, and provider semantics are resolved by the system and do not have to be restated in chat.

## Manual work

None.
