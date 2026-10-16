# Reverse InTr governance and remediation route — mirror handoff

Organization: `StegVerse-Labs`
Evidence class: `SOURCE_IMPLEMENTED` for the validation tests below. Declaration only for the route. No production runtime observation is claimed, and no authentic receipt is claimed.

## The rule this checks

InTr is one-way. StegVerse-org → StegVerse-Labs (governance decided here, remediation classified here) does not establish Labs → StegVerse-org. PR #3197 declared the reverse bindings on `org-runtime/interlock-intr.json`. This handoff records how those bindings are validated. It does not record a production crossing.

## The declared legs

```text
governance-to-org
  capability governance
  destination_organization StegVerse-org
  destination_service      stegverse-org.governance
  request_schema           stegverse.org-governance-decision-request/v1
  authority_effect         NONE_BINDING_ONLY

remediation-to-org
  capability remediation
  destination_organization StegVerse-org
  destination_service      stegverse-org.remediation
  request_schema           stegverse.org-remediation-classification-request/v1
  authority_effect         NONE_BINDING_ONLY
  classification_grants_authority false
```

`governance` bound to StegVerse-Labs at `stegverse-labs.governance` is unchanged. A capability is sent only to an organization a binding names (`CAPABILITY_IS_SENT_TO_THE_ORGANIZATION_THAT_OWNS_IT`).

`organization_egress_boundary.resolve_destination` selects the binding by capability and destination organization, and addresses `destination_service` from that binding. The organization receipt for an emission is appended by `aggregate_repo_transition.aggregate_transition`, which is this ledger's append owner. Neither change grants authority.

## What the validation drives

`tests/test_reverse_intr_inter_org_route.py` (`.github/workflows/reverse-intr-inter-org-route-validation.yml`) mirrors StegVerse-org `.github` `tests/test_governance_inter_org_route.py`:

```text
organization_egress_boundary.emit
  ORGANIZATION_EGRESS_EMITTED or ORGANIZATION_EGRESS_REFUSED
  org-kernel/kernel.py::publish_packet onto a temporary federation mesh
→ far side, simulated
  kernel.receipt (INGRESS_ACCEPTED … EGRESS_EMITTED)
  kernel.build_control_response
  kernel.publish_packet
→ organization_egress_boundary.close
  PENDING when no answer is in the mesh (records nothing)
  ORGANIZATION_EGRESS_CLOSED when the far-side terminal recomputes
  ORGANIZATION_EGRESS_CLOSURE_REFUSED when it does not
```

The peer adapters `stegverse-org.governance` and `stegverse-org.remediation` live in StegVerse-org/.github. They are not imported here. The simulated answer is not that adapter's execution.

`STEGVERSE_REPO_LEDGER_ROOT` and `STEGVERSE_ORG_LEDGER_ROOT` are temporary. Under `python -m unittest`, `tests/__init__.py` declares the POSIX organization-ledger locus for the run, which is the same redirection the rest of this repository's unittest workflows use. Production selection stays the git locus in `.stegverse/transition-ledger/org-contract.json`.

## What each leg asserts

- **ALLOW emit.** A governance request is published to `stegverse-org.governance`. A remediation classification request is published to `stegverse-org.remediation`. Origin is StegVerse-Labs, message class is `ecosystem.work.request`, packet authority effect is `NONE`, binding authority effect is `NONE_BINDING_ONLY`.
- **DENY emit.** An organization the binding does not name (`StegGhost`) is `ORGANIZATION_EGRESS_REFUSED` and publishes no frame. A node with no mesh is refused with `mesh_location_required_from_materializer` and publishes no frame.
- **PENDING close.** No answer yet records nothing. Absence is not a transition.
- **ALLOW close.** A recomputing far-side chain closes. A carried governance `DENY` or `FAIL_CLOSED`, and a carried remediation `ALLOW` or `FAIL_CLOSED`, stay that disposition. Closure authority effect stays `NONE_CLOSURE_RECORD_ONLY`. Remediation `classification_grants_authority` stays false.
- **DENY close.** A terminal receipt that does not recompute is `ORGANIZATION_EGRESS_CLOSURE_REFUSED`.

## What this does not claim

No authentic mesh, no peer-adapter execution, no StegCore decision, no StegHealer classification, and no production demonstration. The forward route's deciding and classifying adapters remain `stegverse-labs.governance` and `stegverse-labs.remediation` in this repository. The reverse legs address the peer services; they do not install those services here.
