# SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001 — Mirror Handoff

Updated: 2026-10-09
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
| Heartbeat installers (`install_sovereign_heartbeat_service`, `_base`, `install_sovereign_heartbeat_carrier`, `install_sovereign_worker_source_refresh_service`) take supplied locations: registration root, runtime root, source-package root and node marker are supplied or `FAIL_CLOSED` `LOCATION_REQUIRED_FROM_MATERIALIZER` by name; no `Path.home()`/XDG/APPDATA/`/etc` derivation; the test that wrote under HOME supplies a scratch location | `MERGED` | PR #3017, merge `3518c4c` |

| Kernel and callers at semantic parity with StegVerse-org `6674994` (#93–#97). `emit.append(idempotent_on=)` returns a transition the chain already records, read at the HEAD the CAS compares, or refuses `ledger_receipt_collision`. `receive` and its refusals append idempotently, report `transition_replayed`, refuse an id collision as `ONE_TRANSITION_ID_BINDS_ONE_MANIFEST`, and take later epochs from the retained repository receipt. Egress records idempotently at a supplied epoch. `consume_and_respond` stamps answers with the consumed frame's epoch. `endpoint_adapter_effect` (`PURE`, `NODE_STATE_WRITE_ONCE`) is declared and tested, and the kernel hands node state only to `NODE_STATE_WRITE_ONCE` adapters. `org-boundary/runtime/manifest_selection.py` is ported: an `INTERNAL_ENDPOINT` packet with no processing declaration is refused before any receipt (`PROCESSING_SELECTED_ONLY_BY_ADMITTED_PROCESSING_CAPABILITY_AND_ROUTE_ID`). `consume_and_respond` and `consume_addressed_frames` take `repo_ledger_root` and `org_ledger_root` and refuse before consuming without them. Every consumed crossing appends `ORGANIZATION_FEDERATION_CROSSING_CONSUMED` (repository receipt, then the organization receipt) before its answer or seen marker. Refused crossings append `ORGANIZATION_FEDERATION_CROSSING_REFUSED`: deterministic refusals are `DENY` and marked; others are `FAIL_CLOSED`, recorded once, left unmarked and retried. The emitters are loaded from the kernel's own repository (`dispatch_root_is_not_this_kernels_organization`). `federation_cycle` passes the supplied ledgers, or returns `FAIL_CLOSED` `LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER`. Peers in tests are materialized as their own organization (`tests/peer_organization.py`) | `MERGED` | PR #3020, merge `fc4df22` |

The parity row above follows Labs' own surfaces wherever they differ from StegVerse-org's:

- **Organization emitter.** `resident-runtime/aggregate_repo_transition.py` here has no `append`. It has `aggregate_transition`, which already returns the receipt that consumes an exact source receipt. That function gained one keyword, `ledger=`, so the kernel can pass the supplied organization ledger root. The environment-supplied root still applies when the keyword is omitted. No `append(idempotent=)` was invented. The kernel builds each organization receipt from the repository receipt the idempotent append returned. A retried `FAIL_CLOSED` whose reason text changed therefore consumes the same source, with the same context, instead of colliding.
- **Endpoint adapters run in the kernel** (`run_endpoint_adapter`), not through `process_boundary.py`, so manifest selection is called in `dispatch`. Its `SystemExit` is surfaced as the boundary's `ValueError`. `process_boundary.py` received StegVerse-org's #94 change too, and it can now load because `manifest_selection.py` exists here.
- **Node state.** The `node_state_root` plumbing from #3016 is unchanged. Labs has no `sdk_self_characterization_response.py` and no `NODE_STATE_WRITE_ONCE` adapter. The governance adapter is `PURE`: it writes only its result file, and its ledger appends go to the supplied ledger roots. No adapter wrote into the checkout, so nothing was moved to `node_store.put_once`.

Not ported, and why:

- **Capability-address dispatch.** This kernel does not dispatch `BOUNDARY_LOCAL_CAPABILITY_INGRESS`. A crossing to `stegverse-labs.sdk-manifest-ingress` is refused with `endpoint_adapter_not_installed`, as before. It is now recorded as `DENY` rather than raised, because no receiving operation exists here to record it. StegVerse-org re-raises these, because its receiving operation records them.
- **Endpoint-response answering** (`build_endpoint_response`). The Labs kernel answers only `RESPONDED_REQUEST_CLASSES`. `manifest_selection` carries `RETURN_BOUND_TO_REQUEST` unchanged. No Labs service accepts `stegverse.org-endpoint-response/v1`, so the return path is admitted nowhere here.
- **`organization_ledger.append` in ingress and egress.** It is still undefined in this repository. Before this work, `tests/test_organization_manifest_ingress_rule_ref.py` already patched it onto `aggregate_transition`. Organization-level idempotence comes from `aggregate_transition`'s exact-source reuse, not from an `idempotent=True` argument.
- **Egress.** `organization_egress_boundary.py` received #93's change verbatim. It still cannot be loaded, because `org-boundary/runtime/origin_attestation.py` is absent (recorded below), so the change is not exercised here.
- **Master Records submitter epoch.** The submitter now stamps a frame with the carried receipt's `hb_reference.epoch`. Labs organization receipts carry `observed_at` and no `hb_reference`, so the submitter's frames here are still stamped from the clock.

Cross-organization consequence: `StegVerse-org/.github:resident-runtime/organization_manifest_ingress.py::governance_request_payload` at `6674994` declares no `processing`. This kernel now refuses that request at `stegverse-labs.governance` and records it as `DENY` `PROCESSING_SELECTED_ONLY_BY_ADMITTED_PROCESSING_CAPABILITY_AND_ROUTE_ID`. The same function in this repository now carries the admitted manifest's `processing` (`capability`, `route_id`). StegVerse-org's sender needs the same change before its governance route can reach `ALLOW` here. That change is that repository's. It is StegVerse-org/.github PR #99 (head `053d961`, "Governance requests declare the processing the decider selects by"). StegVerse-org/.github#99 merged at `893e921`. History (recorded at PR #3020, before that merge, retained verbatim): "As of this edit, #99 is open and not merged into StegVerse-org `main` (`6674994`). Its CI state was not observable from this session: the repository is readable only by git here. Until #99 merges, StegVerse-org governance requests are recorded `DENY` at `stegverse-labs.governance`."

Validation, source only: each new test module fails on main `c66c5f3` and passes on this branch. The full suite was run on main and on this branch in separate worktrees, with scratch `HOME` and `PYTHONDONTWRITEBYTECODE=1`: main had 114 failed and 3408 passed, the branch 114 failed and 3470 passed. The failing set is identical (113 unique ids) and lies within `data/test-suite-baseline.json`. Every workflow `run:` step was compared the same way: 33 fail on both, an identical set, and the 5 new steps pass. No dependency was added.

StegVerse-org #88's regression does not arise here. This repository's `federation_cycle.py` does not propagate repository receipts, and there is no `propagate_repository_receipts.py`.

### Exemption register

No entry was added to `data/organization-role-exemption-register.json`. Every surface changed above was made conformant in source, so none of them needs an exemption. The kernel parity work found both a repository emitter (`.stegverse/transition-ledger/emit.py`) and an organization emitter (`resident-runtime/aggregate_repo_transition.py::aggregate_transition`), so consumed and refused crossings are recorded rather than exempted.

The following nonconformance was observed on surfaces this work did not change. It is recorded here only and is not classified:

- **Always-on surface: the sovereign heartbeat `Restart=always` units.** `scripts/install_sovereign_heartbeat_service.py` and `scripts/install_sovereign_heartbeat_service_base.py` render persistent `Restart=always` systemd user units (KeepAlive LaunchAgents and ONLOGON scheduled tasks elsewhere) for the heartbeat carrier and the worker runtime. This is the Labs counterpart of the persistent executor StegVerse-org #91 removed. Their locations are now supplied rather than derived from the host (row above). The always-on supervision itself is recorded here, not redesigned.
  - Owning goal: none is named in `data/canonical-task-records`. `SV-KV-AI-PERSISTENCE-001` cites the installer only as a resolved dependency, which is not ownership.
- **Shared `default_runtime_root` helper** in those two installers. It still derives a runtime root from `STEGVERSE_HEARTBEAT_ROOT`, falling back to `Path.home()`/XDG/LOCALAPPDATA. About a dozen scripts of other goals evaluate it as an argparse default, so failing it closed would break them even when `--runtime-root` is passed. The installers' own command lines no longer use it. Owning goal: none named.
- **`scripts/install_stegfin_continuity_machine_service.py`** (StegFin) still derives its unit and receipt locations from `Path.home()`/XDG. It was not changed here. Owning goal: none named in this work.
- **`resident-runtime/organization_egress_boundary.py`.** It cannot be loaded, because `org-boundary/runtime/origin_attestation.py` is absent from this repository.
- **`scripts/dispatch_resident_execution_requests.py`.** It still forwards `STEGVERSE_ORG_FEDERATION_GATEWAY_URL` to the StegVerse-002 child.

None of these is claimed conforming. Under `ALL_ACTIONABLE_SURFACES_CLASSIFIED_CONFORMING_OR_REGISTERED_EXEMPTION`, each still needs either a repair or a registered exemption. No `owning_existing_goal` was chosen for any of them, because none was mapped from `data/canonical-task-records` in this work.

## 2026-10-09 N2 canonical exemption registration (W5)

Bounded extension `SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001/N2` (registry generation 298). Design authority: StegVerse-Labs/TVC#488 comments 6071531441 (I-7/I-8) and 6071544608 (W5 rule). Input: the TVC review records merged in StegVerse-Labs/TVC#489, `coordination/credential-model-socket-module-review.v1.json` at TVC `dcf1a90` (blob `660b7ff`). The TVC checker `scripts/check_credential_model_socket_module_review.py` reports `PASS` there (26 non-ALLOW records). Evidence class: `SOURCE_IMPLEMENTED` (source review). No runtime attempt was made, and none is claimed.

`data/organization-role-exemption-register.json` gains 26 entries, all in the live 12-key shape: `current_disposition` `FAIL_CLOSED`, `consequence_committed` false, `authority_effect` `NONE_REGISTER_ONLY`. Each surface is repo-qualified (`StegVerse-Labs/TVC:<path>`). Each `retry_entrypoint` names its TVC record id. The I-8 entry (`workers/sdk_manifest_diagnostic_admitted_consumer.py::_prove_ancestry`) is unchanged and was not duplicated.

| TVC record | Register entries | Owner |
| --- | --- | --- |
| O2B1-NA-01..05, O2B1-NA-07 | one each, broker request construction | `TVC-CREDENTIAL-MODEL-CONSISTENCY-20260826` |
| O2B1-NA-08 | `tvc_primary_runtime_binder.py (discover_primary_runtime)`; O2B1-NA-09 (`task_preflight`, inherited only) consolidated here | `TVC-CREDENTIAL-MODEL-CONSISTENCY-20260826` |
| W4-N1-01 | two: the core forwarder, with its 16 `inherited_by` callers consolidated, and the gmail forwarder, which has its own synchronous connect (`tvc_gmail_provider_operation_broker.py:43-47`) | `TVC-PROVIDER-OPERATION-BROKER-003` |
| W4-N2-01..06 | one each; W4-N2-04's 3 `inherited_by` callers consolidated | `TVC-CREDENTIAL-MODEL-CONSISTENCY-20260826` |
| W4-N2-07 | `tvc_primary_runtime_activation_task.py::task_activate` | `TVC-PROVIDER-OPERATION-BROKER-003` |
| W4-N3-01, W4-N3-02 | one each (socket-presence unit gate) | `TVC-PROVIDER-OPERATION-BROKER-003` |
| W4-N3-03..10 | one each | `TVC-CREDENTIAL-MODEL-CONSISTENCY-20260826` |

`scripts/validate_task_registry_global_invariants.py` now enforces the following for every exemption:

- the exact 12-key shape;
- `FAIL_CLOSED`, with `consequence_committed` false and `authority_effect` `NONE_REGISTER_ONLY`;
- unique surfaces;
- no prohibited justification code in any field, and no equivalent wording in the justification;
- for TVC surfaces, an owner admitted by the N2 extension's `input_owners` and a named TVC record;
- for other surfaces, an owner with a canonical task record.

`tests/test_organization_role_runtime_reality_deployment.py` pins the TVC record-to-surface mapping. The TVC records still read `TVC_LOCAL_PENDING_CANONICAL_REGISTRATION`. Updating that status is TVC's own change.

An exemption grants no authority and satisfies no terminal predicate. This registration addresses the N2 predicates `N2_EACH_CONFIRMED_NONCONFORMING_SURFACE_REGISTERED_WITH_ADMITTED_OWNER_AND_ACTIONABLE_RETRY` and `N2_NO_EXEMPTION_USES_A_PROHIBITED_JUSTIFICATION` in source only. `N2_EXACT_HEAD_REQUIRED_CI_GREEN` is open until CI is green at the exact head. The task record's predicates are not changed here. The 2026-10-08 unclassified surfaces above (heartbeat units, `default_runtime_root`, StegFin installer, egress boundary, gateway URL forwarding) are outside N2's TVC input and remain unregistered and unclassified.

### Remaining predicates (all six open)

- `MANIFEST_BOUND_INTR_ADMISSION_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `GOVERNANCE_MANIFEST_ROUTE_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `NON_GOVERNANCE_MANIFEST_ROUTE_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `APPLICABLE_ORGANIZATION_STATE_TRANSITION_RECEIPT_RETAINED`
- `APPLICABLE_POST_ORGANIZATION_RECORD_RECONSTRUCTION_EVIDENCE_RETAINED`
- `ALL_ACTIONABLE_SURFACES_CLASSIFIED_CONFORMING_OR_REGISTERED_EXEMPTION`

The source repairs above remove host-derived state locations, checkout-resident node state and the hosted gateway path. They are prerequisites for these predicates; none of them satisfies one.
