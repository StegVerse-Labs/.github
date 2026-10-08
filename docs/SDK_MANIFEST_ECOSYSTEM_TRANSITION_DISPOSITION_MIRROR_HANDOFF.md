# SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001 — Mirror Handoff

Updated: 2026-10-07
Goal Task ID: `SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001`
Parent Task ID: `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`
COSV ID: `71000000100126`
Status: `ACTIVE / CHECKED_OUT`

## Goal

After source-conformance repairs, exercise representative governance and non-governance ACTIONS as manifest-bound state transitions and retain terminal ALLOW/DENY/FAIL_CLOSED dispositions, and applicable Organization ledger receipts; also retain Master Records reconstruction evidence taken after the Organization record. That reconstruction is non-gating.

## Inherited invariants

- Every ACTION is a manifest-bound state transition.
- Processing semantics are selected only by admitted `processing.capability` + `processing.route_id` and installed route resolution.
- Terminal attempted-boundary disposition is `ALLOW | DENY | FAIL_CLOSED`.
- Organization ledger append is runtime reality when Organization state changes.
- Master Records is limited to organization records and reconstruction evidence; Organization runtime reality does not depend on it.
- No external machine, listener, session, receiver liveness, hosted service, scheduler, or later observer may be awaited as a transition/completion predicate.
- Receiver unavailability follows `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION`.

## Remaining predicates

- `MANIFEST_BOUND_INTR_ADMISSION_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `GOVERNANCE_MANIFEST_ROUTE_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `NON_GOVERNANCE_MANIFEST_ROUTE_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `APPLICABLE_ORGANIZATION_STATE_TRANSITION_RECEIPT_RETAINED`
- `APPLICABLE_POST_ORGANIZATION_RECORD_RECONSTRUCTION_EVIDENCE_RETAINED`
- `ALL_ACTIONABLE_SURFACES_CLASSIFIED_CONFORMING_OR_REGISTERED_EXEMPTION`

## Completion discipline

Close only from exact source/runtime evidence appropriate to each predicate. Source/CI/merge evidence must not be promoted to runtime execution. Preserve historical evidence and use registered exemptions only for genuine nonconformance that cannot be repaired; reachability is not an exemption justification.

## 2026-10-07 cross-organization roundtrip source assessment

Source inspection (not execution) identified `StegVerse-org/.github:resident-runtime/run_sv002_self_characterization_roundtrip.py` as a legacy host-coupled specimen: it resolves local checkouts, calls subprocess federation cycles, and rejects hosted environments. It must not become a normative dependency for SV-LLM. `StegVerse-org/.github:org-boundary/registry/federation.json` has 15 entries and no SV-LLM peer at inspected default head. `SV-LLM/.github:org-runtime/crossing.py` already models manifested ingress/egress, no receiver liveness prerequisite, durable queue, and organization ledger append. SDK `stegverse/review_publisher_transfer.py` only prepares Publisher evidence envelopes; Publisher `publisher/intr_artifact_transfer.py` is the existing InTr destination adapter. These are source observations, not live dispositions.

Required repair at existing owners: reconcile federation membership under its registry rules; implement manifest-directed egress/ingress/return with `processing.capability` and `processing.route_id`, independently disposition each attempted boundary, preserve TV/TVC custody and organization-ledger append, use `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION` rather than host/spool liveness as a prerequisite, and invoke the existing Publisher route only if the admitted manifest requests presentation. No new machine, framework, scheduler, authority, or runtime gate. CI may validate source but cannot attest actual crossing. Non-ALLOW must name the failed predicate and retry edge at the actually invoked boundary; do not fabricate downstream results.

Remaining: owner-specific source repairs, exact-head tests, CI evidence, Organization readback and applicable Master Records reconstruction; that reconstruction is non-gating. No ALLOW, live crossing, Publisher PDF, or runtime validation is claimed by this assessment.

## 2026-10-08 source-conformance reconciliation

This section records repository events and their evidence classes. Each item is classed separately. `SOURCE_IMPLEMENTED`, `CI_VALIDATED` and `MERGED` are source evidence, not runtime evidence. None of them is promoted to `SANDBOX_RUNTIME_OBSERVED`, `EXTERNAL_PROVIDER_OBSERVED`, `MASTER_RECORDS_RECONSTRUCTED` or `END_TO_END`. No ALLOW, live crossing, Organization ledger readback or Master Records reconstruction is claimed. The canonical task record's state and predicates are unchanged.

### StegVerse-org/.github

| Change | Evidence class | Ref |
| --- | --- | --- |
| Write-once `put_once` is atomic (`os.link`); a `PENDING` CLI result exits 3, not success | `MERGED` | PR #86, merge `2f1c907` |
| Organization and repository ledger roots are supplied or `FAIL_CLOSED` `LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER`; never `XDG_STATE_HOME`/`Path.home()` | `MERGED` | PR #87, merge `60ddd13` |
| Regression fix for #87: repository propagation without a ledger home records `FAIL_CLOSED` with a retry entrypoint instead of aborting the federation cycle | `MERGED` | PR #88, merge `9e112b4` |
| Host-selected federation gateway removed; the declared carrier is the only path | `MERGED` | PR #89, merge `8c802ab` |
| Governance return materialized on decision-frame consumption; canonical manifest retained at ingress | `MERGED` | PR #90, merge `37673ca` |
| Resident executor runs one federation cycle per materialization (polling loop and `Restart=always` systemd unit removed); SV002 query is a manifest-bound submission on the supplied mesh; gateway transport, activator and activation request removed | `MERGED` | PR #91, merge `72f3a4c` |

### SV-LLM

| Change | Evidence class | Ref |
| --- | --- | --- |
| Anthropic terms notation (documentation only; no runtime surface) | `MERGED` | SV-LLM/Anthropic PR #10 |
| Supplied mesh and ledger roots; carrier declaration | `MERGED` | SV-LLM/.github PR #17, merge `ed27bc4` |

### StegVerse-org/StegVerse-SDK

| Change | Evidence class | Ref |
| --- | --- | --- |
| Round trip supplies `STEGVERSE_REPO_LEDGER_HOME`; workflow pins moved to StegVerse-org `72f3a4c` and SV-LLM `ed27bc4` | `SOURCE_IMPLEMENTED` (open). The parent session reports a local round trip with all 7 legs `ALLOW` against both mains, 3/3 runs. That is a local source test, not a runtime observation, and is not promoted | PR #440 |

### StegVerse-Labs/.github (this repository)

| Change | Evidence class | Ref |
| --- | --- | --- |
| Shared kernel at semantic parity with StegVerse-org: `org-kernel/node_store.py` seam; mesh supplied or `FAIL_CLOSED` `mesh_location_required_from_materializer`; heartbeat reference validated on recovery; `hb_reference(epoch=)` with `derived_from_clock`; frame layout `frames.d/<sha256(packet_id\|frame_sha256)>.json` unchanged. Callers take a supplied mesh. Ledger roots supplied or `FAIL_CLOSED` `LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER` | `MERGED`, `CI_VALIDATED` | PR #3013, merge `f68a472` |
| Hosted federation gateway branches removed; kernel `publish_packet` over the supplied mesh is the only carrier; `federation_gateway_transport.py` retired; activation manifest declares no gateway | `MERGED`, `CI_VALIDATED` | PR #3014, merge `1a7fb82` |
| Resident cycle writes consumption markers and work intake under the supplied node-state root, never into the checkout; frame-name dedup identity unchanged | `MERGED` | PR #3016, merge `7eb7545` |
| Heartbeat installers (`install_sovereign_heartbeat_service`, `_base`, `install_sovereign_heartbeat_carrier`, `install_sovereign_worker_source_refresh_service`) take supplied locations: registration root, runtime root, source-package root and node marker are supplied or `FAIL_CLOSED` `LOCATION_REQUIRED_FROM_MATERIALIZER` by name; no `Path.home()`/XDG/APPDATA/`/etc` derivation; the test that wrote under HOME supplies a scratch location | `SOURCE_IMPLEMENTED` (open) | PR #3017 |

StegVerse-org #88's regression does not arise here. This repository's `federation_cycle.py` does not propagate repository receipts, and there is no `propagate_repository_receipts.py`.

### Exemption register

No entry was added to `data/organization-role-exemption-register.json`. Every surface changed above was made conformant in source, so none of them needs an exemption.

The following nonconformance was observed on surfaces this work did not change. It is recorded here only and is not classified:

- **Always-on surface: the sovereign heartbeat `Restart=always` units.** `scripts/install_sovereign_heartbeat_service.py` and `scripts/install_sovereign_heartbeat_service_base.py` render persistent `Restart=always` systemd user units (KeepAlive LaunchAgents and ONLOGON scheduled tasks elsewhere) for the heartbeat carrier and the worker runtime. This is the Labs counterpart of the persistent executor StegVerse-org #91 removed. Their locations are now supplied rather than derived from the host (row above). The always-on supervision itself is recorded here, not redesigned.
  - Owning goal: none is named in `data/canonical-task-records`. `SV-KV-AI-PERSISTENCE-001` cites the installer only as a resolved dependency, which is not ownership.
- **Shared `default_runtime_root` helper** in those two installers. It still derives a runtime root from `STEGVERSE_HEARTBEAT_ROOT`, falling back to `Path.home()`/XDG/LOCALAPPDATA. About a dozen scripts of other goals evaluate it as an argparse default, so failing it closed would break them even when `--runtime-root` is passed. The installers' own command lines no longer use it. Owning goal: none named.
- **`scripts/install_stegfin_continuity_machine_service.py`** (StegFin) still derives its unit and receipt locations from `Path.home()`/XDG. It was not changed here. Owning goal: none named in this work.
- **`resident-runtime/organization_egress_boundary.py`.** It cannot be loaded, because `org-boundary/runtime/origin_attestation.py` is absent from this repository.
- **`scripts/dispatch_resident_execution_requests.py`.** It still forwards `STEGVERSE_ORG_FEDERATION_GATEWAY_URL` to the StegVerse-002 child.

None of these is claimed conforming. Under `ALL_ACTIONABLE_SURFACES_CLASSIFIED_CONFORMING_OR_REGISTERED_EXEMPTION`, each still needs either a repair or a registered exemption. No `owning_existing_goal` was chosen for any of them, because none was mapped from `data/canonical-task-records` in this work.

### Remaining predicates (all six open)

- `MANIFEST_BOUND_INTR_ADMISSION_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `GOVERNANCE_MANIFEST_ROUTE_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `NON_GOVERNANCE_MANIFEST_ROUTE_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `APPLICABLE_ORGANIZATION_STATE_TRANSITION_RECEIPT_RETAINED`
- `APPLICABLE_POST_ORGANIZATION_RECORD_RECONSTRUCTION_EVIDENCE_RETAINED`
- `ALL_ACTIONABLE_SURFACES_CLASSIFIED_CONFORMING_OR_REGISTERED_EXEMPTION`

The source repairs above remove host-derived state locations, checkout-resident node state and the hosted gateway path. They are prerequisites for these predicates; none of them satisfies one.
