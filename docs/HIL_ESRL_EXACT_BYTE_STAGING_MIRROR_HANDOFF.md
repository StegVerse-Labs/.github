# HIL ESRL Exact-Byte Staging Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Issue: `#1432`
Parent goal: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Canonical parent handoff: `docs/HIL_RESIDENT_SESSION_MANIFOLD_ACTIVATION_MIRROR_HANDOFF.md`
Current COSV: `50000000103000`

## Purpose

Prepare the exact-byte bridge between the now-physically-observed current-iPhone ESRL `LEASE_OPEN` result and the already-merged canonical intake/reconciliation contracts without weakening the evidence boundary.

## Implemented helper

`scripts/stage_hil_esrl_exact_byte_acceptance.py` reads the supplied physical artifact bytes exactly once, validates the decoded object through `intake_hil_browser_esrl_evidence.validate_artifact`, computes the source SHA-256 from those same bytes, then builds the existing `reconcile_hil_esrl_acceptance.build_proposal` result against the current task vector and worker registry.

When an output directory is supplied it writes only staging artifacts:

- the exact source bytes verbatim under a SHA-addressed filename;
- the accepted intake receipt;
- the non-mutating reconciliation proposal;
- a staging manifest.

It does not edit the task vector, worker registry, COSV, runtime state, receiver state, TVC lifecycle state, or downstream evidence.

## Current runtime/evidence boundary

Physical `LEASE_OPEN` has been observed in the retained current-iPhone G25 context, but exact downloaded bytes have not yet been supplied to canonical intake. Therefore the canonical ESRL blocker and COSV remain unchanged until an exact file passes this helper and the existing reviewed reconciliation step is then applied.

No screenshot reconstruction or reserialized substitute may be used as authentic evidence.

## Expected accepted transition

After exact-byte intake succeeds, the staged proposal must remain:

```text
50000000103000 -> 50000000102000
remove only AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED
retain POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED
retain TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN
next runtime stage = HIL_RECEIVER_READY_AND_CUSTODY
```

## Tests

Focused tests use a synthetic fixture matching the already-observed subject lineage solely to validate code behavior; synthetic fixture bytes are never runtime evidence. Tests assert exact staged-byte preservation, accepted intake composition, the two-blocker proposal, no canonical/runtime mutation, and fail-closed rejection when the lease state is not `LEASE_OPEN`.

## README review

README was re-reviewed. This is an internal staging/control helper and does not change a public interface or runtime architecture, so no README prose change is required.
