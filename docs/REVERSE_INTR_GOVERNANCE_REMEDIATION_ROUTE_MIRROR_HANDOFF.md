# Reverse InTr governance route — mirror handoff

Organization: `StegVerse-Labs`
Evidence class: `SOURCE_IMPLEMENTED` for the validation tests below. Declaration only for the route. No production runtime observation is claimed, and no authentic receipt is claimed.

## The rule this checks

InTr is one-way. StegVerse-org → StegVerse-Labs (governance decided here) does not establish Labs → StegVerse-org. PR #3197 declared reverse bindings on `org-runtime/interlock-intr.json`. This handoff records how the governance binding is validated. It does not record a production crossing.

StegVerse-org does not request or receive remediation. StegHealer pulls the org's NON-ALLOW receipts from the org ledgers and decides on remediation itself. This repository does not declare `remediation-to-org` and does not address `stegverse-org.remediation`. The binding PR #3197 added for that leg is removed. Reference: StegVerse-Labs/.github#3183. This text claims no runtime result, safety, compliance, or authority.

## The declared leg

```text
governance-to-org
  capability governance
  destination_organization StegVerse-org
  destination_service      stegverse-org.governance
  request_schema           stegverse.org-governance-decision-request/v1
  authority_effect         NONE_BINDING_ONLY
```

`governance` bound to StegVerse-Labs at `stegverse-labs.governance` is unchanged. A capability is sent only to an organization a binding names (`CAPABILITY_IS_SENT_TO_THE_ORGANIZATION_THAT_OWNS_IT`).

`organization_egress_boundary.resolve_destination` selects the binding by capability and destination organization, and addresses `destination_service` from that binding. The organization receipt for an emission is appended by `aggregate_repo_transition.aggregate_transition`, which is this ledger's append owner. The declared authority effect on the binding is `NONE_BINDING_ONLY`.

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

The peer adapter `stegverse-org.governance` lives in StegVerse-org/.github. It is not imported here. The simulated answer is not that adapter's execution.

`STEGVERSE_REPO_LEDGER_ROOT` and `STEGVERSE_ORG_LEDGER_ROOT` are temporary. Under `python -m unittest`, `tests/__init__.py` declares the POSIX organization-ledger locus for the run, which is the same redirection the rest of this repository's unittest workflows use. Production selection stays the git locus in `.stegverse/transition-ledger/org-contract.json`.

## What the governance leg asserts

- **ALLOW emit.** A governance request is published to `stegverse-org.governance`. Origin is StegVerse-Labs, message class is `ecosystem.work.request`, packet authority effect is `NONE`, binding authority effect is `NONE_BINDING_ONLY`.
- **DENY emit.** An organization the binding does not name (`StegGhost`) is `ORGANIZATION_EGRESS_REFUSED` and publishes no frame. A node with no mesh is refused with `mesh_location_required_from_materializer` and publishes no frame.
- **PENDING close.** No answer yet records nothing. Absence is not a transition.
- **ALLOW close.** A recomputing far-side chain closes. A carried governance `DENY` or `FAIL_CLOSED` stays that disposition. Closure authority effect stays `NONE_CLOSURE_RECORD_ONLY`.
- **DENY close.** A terminal receipt that does not recompute is `ORGANIZATION_EGRESS_CLOSURE_REFUSED`.
- **No remediation leg.** No egress binding uses profile `remediation-to-org` or destination service `stegverse-org.remediation`. Resolving capability `remediation` toward StegVerse-org is refused.

## What this does not claim

No authentic mesh, no peer-adapter execution, no StegCore decision, no StegHealer classification, and no production demonstration. The forward route's deciding adapter remains `stegverse-labs.governance` in this repository. The reverse leg addresses the peer governance service; it does not install that service here. The local classifier `stegverse-labs.remediation` is unchanged and is not a route to StegVerse-org.
