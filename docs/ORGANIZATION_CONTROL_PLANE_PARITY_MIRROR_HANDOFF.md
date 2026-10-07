# Organization Control Plane Parity Mirror Handoff

Updated: 2026-10-07
Goal Task ID: `ORGANIZATION-CONTROL-PLANE-PARITY-001`
Parent Task ID: `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`
COSV ID: `71000000100127`
Status: `ACTIVE / CHECKED_OUT`

## Governing invariant

`StegVerse-Labs/.github` is the sole StegVerse-Labs organization ingress/egress boundary. Cross-organization traffic traverses Universal Interlock/InTr between organization `.github` boundaries. StegCore is an internal Labs decision component and is not an organization ingress endpoint.

## Reference implementation

Reference: `StegVerse-org/.github`.

The parity repair reuses the existing Org organization-control contracts and changes only organization-local identity/bindings. It creates no second runtime, scheduler, ledger, credential authority, governance authority, or Master Records authority.

## Branch repair

Branch: `fix/org-capability-parity-001`

Installed/reconciled:
- `resident-runtime/organization_manifest_ingress.py`
- `resident-runtime/organization_egress_boundary.py`
- `resident-runtime/sdk_manifest_crossing.py`
- `org-boundary/runtime/process_boundary.py`
- `org-boundary/runtime/capability_ingress.py`
- `resident-runtime/ledger_store.py`
- atomic repository receipt append semantics in `.stegverse/transition-ledger/emit.py`
- organization-owned SDK manifest receiving operation in `org-runtime/interlock-intr.json`
- `stegverse-labs.sdk-manifest-ingress` service registration.

Machine-readable audit: `data/organization-control-plane-parity-v1.json`.

## StegCore boundary

`resident-runtime/governance_endpoint.py` is already organization-local and imports StegCore only after a packet has reached `stegverse-labs.governance` inside Labs. Direct external StegCore invocation is not an alternate organization route and must never satisfy the organization-ingress predicate.

## Evidence state

Source repair is not runtime proof. Required closure is exact-head CI for parity and bypass-negative controls, followed by an authentic cross-org attempt when the existing authorized InTr surface is available. Every attempted transition retains ALLOW, DENY, or FAIL_CLOSED. Master Records remains organization-record/reconstruction only and is not a runtime gate.
