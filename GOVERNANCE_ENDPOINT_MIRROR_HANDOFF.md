# Governance endpoint — mirror handoff

Organization: `StegVerse-Labs`
Service: `stegverse-labs.governance`
Evidence class: `SOURCE_IMPLEMENTED`. No production runtime observation is claimed.

## What this is

StegCore is a StegVerse-Labs repository, so a governance decision is made here, in the organization that owns the evaluator. Another organization does not import StegCore and decide for itself. It emits the request out through its own `.github` egress; the request crosses Interlock/InTr on the federation mesh; this organization's `.github` receives it, decides it, and answers the same way.

```text
StegVerse-org/.github  egress  --InTr / federation mesh-->  StegVerse-Labs/.github  ingress
                                                            stegverse-labs.governance
                                                            StegCore StegGate decides
StegVerse-org/.github  <--InTr / federation mesh--  ecosystem.work.ack with the decision
```

## What changed here

- `org-boundary/registry/services.json` declares `stegverse-labs.governance`: an `INTERNAL_ENDPOINT` whose adapter is admitted (`ALLOW_DECLARED_ADAPTER`), admitting `governance` on `stegverse.route.canonical-governed.v1`.
- `org-kernel/kernel.py` dispatches an `INTERNAL_ENDPOINT` that declares an admitted adapter. The adapter is resolved before any receipt is minted, so an adapter the registry does not admit leaves no chain. Receipts are minted by the same `receipt` rule as every other role, so the origin recomputes the chain from what it already holds. The adapter runs under the kernel's own interpreter, not a bare `python3` from the host path. Boundary-local roles are unchanged.
- `resident-runtime/governance_endpoint.py` decides the request with `stegcore.steggate.evaluate_admissibility`. A request whose digest does not recompute, or that cannot be evaluated, or that arrives where StegCore is not materialized, is decided `FAIL_CLOSED` naming why — never guessed.

## Records

The decision is a transition that occurs in this organization, so it is recorded here at both levels: a `stegverse.repo-transition-receipt/v1` of class `ORGANIZATION_GOVERNANCE_DECISION`, then the organization receipt consuming it. Organization records are the custody of the decision. Nothing here submits it elsewhere or waits on anything.

## Validation

`tests/test_governance_endpoint.py`, run by the whole-suite ratchet in `.github/workflows/test-suite-ratchet.yml` (`org-kernel/tests/test_kernel.py` runs in its `consolidated-source-validators` job; the former `governance-endpoint-validation.yml` was consolidated there under #3039 H6b).
