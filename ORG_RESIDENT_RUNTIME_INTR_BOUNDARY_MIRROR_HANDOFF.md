# Organization Resident Runtime + Interlock/InTr Boundary Mirror Handoff

Status: ACTIVE
Updated: 2026-08-31
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`

This `.github` is the organization-level owner of resident-runtime activation source and all ingress/egress generation.

Application repositories expose endpoint/runtime profiles only. Cross-organization traffic is generated here as Interlock/InTr envelopes.

Authentic runtime execution remains a sovereign resident process. GitHub and GitHub Actions are source/evidence/validation surfaces only.

HB/HB-derived carriers may synchronize and carry packets but grant no admission, execution, credential, routing, transition, receiving, publication, or release authority.

Action admission, authority transfer, capability realization, and authority effect are distinct; standing/effects are `DERIVED_FROM_APPLICABLE_TRANSITION_ELEMENTS`.

Machine surfaces:
- `org-runtime/activation.json`
- `org-runtime/interlock-intr.json`
- `org-runtime/runtime_boundary.py`

The tool validates the contract and emits resident activation requests plus ingress/egress envelopes. It cannot self-grant authority.


## Workflow surface registration

The existing `.github/workflows/org-runtime-boundary.yml` is registered in `control/workflow-surface-registry.json` as `KEEP_STANDALONE_EXCEPTION` for source-only validation. This classification grants no resident execution, ingress/egress, credential, routing, transition, publication, or release authority. Authentic organization runtime execution remains resident-only.
