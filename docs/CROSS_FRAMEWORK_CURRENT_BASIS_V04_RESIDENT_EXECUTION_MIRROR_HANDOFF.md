# Cross-Framework Current-Basis v0.4 Resident Execution Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`
Issue: #478
Current source-fix branch: `fix/current-basis-resident-refresh-materialization-484`

## Goal

Dispatch one bounded authentic StegVerse execution of the exact frozen cross-framework current-basis v0.4 test through the existing sovereign resident runtime. This lane does not create a second scheduler, heartbeat, evaluator, credential path, or runtime authority.

## Exact upstream bindings

```text
SDK execution harness merge: StegVerse-org/StegVerse-SDK@2b1ae25662aaade5033e6bacac98d9ba5233fdee
StegCore native current-basis merge: StegVerse-Labs/StegCore@e80e927616750a88ad7fc88f4017fc496474f1e4
resident request/consumer merge: StegVerse-Labs/.github@b881eaba3b2e5eca64630a4d684352c22f782ca9
frozen manifest SHA-256: 07a08496c21b31f70f6f45ef731aa5f6b2522a6fc8f67f2d0a4c2b6fceda7a3f
frozen manifest Git blob SHA-1: 59d818a15fc7be732c97dae7d2174d8cfe9a7bab
test_id: cross-framework-current-basis-001
```

## Runtime boundary

```text
existing WorkerCoordinator / resident dispatcher
-> bounded current-basis resident request consumer
-> already-materialized local SDK + StegCore + Core-Lite + Master Records roots
-> SDK scripts/run_cross_framework_current_basis_v04.py
-> canonical StegCore current_basis derivation
-> canonical SDK sovereign validation runtime
-> Master Records custody
-> S1 observation
-> post-observation S0->S1 receipt
-> replay
-> reconstruction
-> local RUN_COMPLETE.json
```

GitHub Actions is source validation only and MUST NOT execute this test. No network source fetch, GitHub credential, provider credential, counterpart result, or external consequence is allowed.

## Local source requirements

The resident consumer uses only locally materialized roots already exposed to the sovereign runtime:

```text
STEGVERSE_SDK_SOURCE_ROOT
STEGVERSE_STEGCORE_SOURCE_ROOT
STEGVERSE_CORE_LITE_SOURCE_ROOT
STEGVERSE_MASTER_RECORDS_SOURCE_ROOT
```

Missing roots or missing exact harness/manifest/current-basis files produce a machine-observable blocked state. They do not create a user-action requirement and do not authorize remote checkout.

## Source-refresh materialization correction

Post-merge inspection of the actual resident source-refresh path found one concrete execution blocker: `scripts/dispatch_resident_execution_requests.py` and `control/resident-execution-request.d/` were copied into the resident runtime, but the newly added `scripts/consume_cross_framework_current_basis_v04_request.py` was not listed in `STATIC_FILES` in `scripts/refresh_sovereign_worker_runtime_source.py`.

Without that entry, a refreshed resident runtime would see the request and dispatcher but report the current-basis consumer as `CONSUMER_NOT_MATERIALIZED`; authentic execution could therefore never start.

The active correction adds the exact consumer to the static refresh set and adds a regression guard proving both the consumer and request directory are materialized. This is source/runtime plumbing only; it does not itself claim that the resident host has refreshed or consumed the request.

## Completion

Terminal success requires local result:

```text
~/.stegverse/state/cross-framework-current-basis-v04/result/RUN_COMPLETE.json
status=COMPLETE
manifest_sha256=07a08496...
independent_execution_complete=true
s1_observed=true
transition_receipt_bound=true
custody_recorded=true
replay_recorded=true
reconstruction_recorded=true
counterpart_result_consumed_before_completion=false
external_side_effect=false
```

Repository publication of the resultant packet is a later evidence-transport step and remains separate from resident execution authority.

## Current state

```text
resident request source: MERGED
resident consumer source: MERGED
resident dispatcher integration: MERGED
resident request/source validation: SUCCESS
source-refresh consumer materialization: FIX IMPLEMENTED / VALIDATION PENDING
resident source refresh after correction: NOT OBSERVED
resident request consumption: NOT OBSERVED
authentic StegVerse execution: NOT OBSERVED
Master Records custody/replay/reconstruction: NOT OBSERVED
user action required: false
second machine required: false
```


## Canonical local source-root discovery — 2026-08-30

A second machine-execution seam was removed after the resident materialization fix. The current-basis consumer no longer requires four manually populated component-root environment variables when the existing canonical production source materialization is already present.

Resolution order:

```text
explicit STEGVERSE_*_SOURCE_ROOT for a component, if present and valid
-> STEGVERSE_SOURCE_MATERIALIZATION_ROOT/components/<component>
-> /var/lib/stegverse/source/components/<component>
-> fail closed as BLOCKED_LOCAL_SOURCE_ROOTS_NOT_OBSERVED
```

This matches the existing production source-preparation architecture. The generic resident dispatcher now forwards the non-secret `STEGVERSE_SOURCE_MATERIALIZATION_ROOT` locator when present. No remote checkout, network fetch, GitHub/provider credential, or new runtime authority is introduced.

This correction removes manual environment wiring as a prerequisite when the canonical local component tree already exists. Authentic resident execution remains separately evidence-bound.


## Resident materialization and source-discovery closures — 2026-08-30

Two source/runtime plumbing defects are now closed and merged:

```text
resident refresh rematerialization:
  PR #500
  merge: 0c45dfc7e413c5da8fcc89f33637e1783a6eb558
  current-basis resident request validation: 33293861330 SUCCESS
  organization control plane: 33293861332 SUCCESS
  Heartbeat Worker Project: 33293861363 SUCCESS

canonical local source-root discovery:
  PR #511
  merge: 6d03c0d3d41f45ac91b740c091f16b7ddf9097bf
  current-basis resident request validation: 33294733821 SUCCESS
  Heartbeat Worker Project: 33294733819 SUCCESS
  organization control plane: 33294733918 SUCCESS
```

The consumer is now materialized by the resident source-refresh path and resolves already-local component roots without requiring four manual environment variables.

The public Site projection is also separately complete and anonymously observed at frozen v0.4:

```text
Site PR #700 merge: 8a13182c7630eab1efa613cde45229b4de27a975
public verification: run 33294523117 attempt 2 / job 99211964506 PASS
projection state: FROZEN / execution window OPEN
authentic execution: NOT_RUN
results: absent
```

These closures do not substitute for resident execution.

## Exact canonical source-blob binding — 2026-08-30

Before invoking the SDK harness, the resident consumer now verifies the exact experiment-critical Git blob identities already merged in the canonical component repositories:

```text
SDK:
  scripts/run_cross_framework_current_basis_v04.py
    93a423a76d1662329f0511dd531646c5b21ff55b
  inspection/examples/cross-framework-current-basis-request.draft.json
    59d818a15fc7be732c97dae7d2174d8cfe9a7bab
  stegverse/sovereign_validation_runtime.py
    6bc0944633b6299c19f065f44dd5999434445dd7
  stegverse/current_basis.py
    5971a050d94fc237cad65d23ba5ac873ee6900b4

StegCore:
  src/stegcore/current_basis.py
    c56179d1ba92a3f487dd62eddd41b812028c48c3
  src/stegcore/transaction_lifecycle.py
    81935669846fedd2867272810b090226b05780ab

Core-Lite:
  core_lite/transaction_route.py
    734923a86bfcd4d41d07e0fb8797de50f0fb9408

Master Records:
  services/manifest_receipt_custody.py
    26a4c1e082ee91128648b2b9bd13cc32ce915f82
```

A local source tree that is present but stale now emits `BLOCKED_CANONICAL_SOURCE_IDENTITY_MISMATCH` and records every expected/observed blob identity without attempting the experiment. This prevents a superficially complete but stale local materialization from being mistaken for the frozen v0.4 execution basis.

Current evidence boundary remains:

```text
resident request source: MERGED
resident consumer source: MERGED
resident dispatcher integration: MERGED
resident source-refresh materialization defect: CLOSED / MERGED / VALIDATED
canonical local source discovery defect: CLOSED / MERGED / VALIDATED
exact critical source identity guard: IMPLEMENTED / VALIDATION PENDING
resident request consumption: NOT OBSERVED
authentic StegVerse execution: NOT OBSERVED
S1 observation: NOT OBSERVED
post-observation transition receipt: NOT OBSERVED
Master Records custody/replay/reconstruction: NOT OBSERVED
RUN_COMPLETE.json: NOT OBSERVED
user action required: false
second machine required: false
```


## Local source-package self-remediation — 2026-08-30

After exact source-blob binding was merged, one remaining local-only resolution path was made active: a resident with a missing or stale experiment component may now consume an already-local `stegverse.source-package/v1` object before deciding that execution is blocked.

Resolution behavior:

```text
discover exact component root
-> verify experiment-critical blobs
-> if missing/stale, inspect local source-package store only
-> validate package schema/version/component
-> reject credential-bearing or authority-bearing package
-> verify every file size/SHA-256
-> recompute ordered content-manifest digest/source_identity
-> stage package atomically
-> verify exact frozen-v0.4 critical Git blobs in staged tree
-> replace local component root atomically
-> rerun exact source checks
-> only then permit the SDK harness
```

Local package store:

```text
STEGVERSE_SOURCE_PACKAGE_ROOT
fallback: ~/.stegverse/packages/source/v1
```

The generic resident dispatcher forwards this non-secret locator. No HTTP/Git/GitHub/provider fetch occurs in this path.

If a required local package is absent, the consumer records `BLOCKED_LOCAL_SOURCE_PACKAGE_NOT_OBSERVED` plus the exact component/package path needed, with:

```text
runtime_execution_attempted=false
source_resolution_attempted=true
network_source_fetch_performed=false
credential_read_or_acquired=false
user_action_required=false
second_machine_required=false
authority_effect=NONE_SOURCE_RESOLUTION_ONLY
```

Package integrity is transport evidence only and never confers execution authority. The frozen experiment remains executable only after the independently merged request, non-hosted resident eligibility, exact source identity checks, and canonical SDK/StegCore/Master Records path all hold.


## Local package remediation merged; arrival retry implementation — 2026-08-30

Local source-package self-remediation is now merged and validated:

```text
PR: #531
merge: 4da6427767b0c63a3110efd96b0ccedae8935d98
Cross-Framework Current-Basis Resident Request Validation: 33296221146 SUCCESS
Heartbeat Worker Project: 33296221148 SUCCESS
Organization control plane: 33296221166 SUCCESS
```

The next local-only execution seam is package arrival after a prior blocked attempt. The existing rootless source-refresh watcher is being extended rather than creating a second scheduler or heartbeat.

Intended event path:

```text
BLOCKED_LOCAL_SOURCE_PACKAGE_NOT_OBSERVED
-> exact package arrives in local source-package store
-> existing systemd-user path watcher fires
-> existing source refresh service runs
-> existing resident dispatcher runs
-> current-basis consumer re-enters
-> package is verified/staged atomically
-> exact frozen-v0.4 critical blobs reverified
-> harness may execute only if all gates pass
```

The watcher uses:

```text
STEGVERSE_SOURCE_PACKAGE_ROOT
fallback: ~/.stegverse/packages/source/v1
```

The package-store path is non-secret and is passed into the existing refresh service environment. Installation creates the directory and records it in the local source-refresh installation receipt. No network acquisition, provider credential, package authority, new scheduler, or new HeartBeat instance is introduced.

Sovereign bootstrap/native materialization source completeness is also tightened so the current-basis resident consumer itself must exist in:
- `bootstrap_sovereign_runtime.py::REQUIRED_SOURCE_FILES`;
- `install_sovereign_heartbeat_service.py::COPY_FILES`;
- the post-materialization required-file check.

This prevents a stale canonical checkout from being accepted as a complete resident runtime while silently lacking the exact consumer needed by the queued frozen-v0.4 request.

Current execution boundary:

```text
frozen v0.4 request: MERGED / QUEUED IN SOURCE
resident consumer: MERGED
exact source guard: MERGED / VALIDATED
local package repair: MERGED / VALIDATED
package-arrival event retry: IMPLEMENTED / VALIDATION PENDING
authentic resident consumption: NOT OBSERVED
S1: NOT OBSERVED
post-observation transition receipt: NOT OBSERVED
Master Records custody/replay/reconstruction: NOT OBSERVED
RUN_COMPLETE.json: NOT OBSERVED
user action required: false
second machine required: false
```


## Automatic local external-result packet preparation — 2026-08-30

After authentic `RUN_COMPLETE.json` exists, the resident consumer now invokes the exact hardened SDK result packager locally instead of leaving packet construction as a later manual step.

Additional exact SDK source binding:

```text
scripts/package_cross_framework_current_basis_results.py
Git blob SHA-1: 5cd6d104d5d08042aa60330ade92370d53fad28a
```

Post-run flow:

```text
authentic RUN_COMPLETE observed
-> invoke canonical SDK hardened result packager
-> verify frozen v0.4 SHA-256 + Git blob binding
-> verify GitHub Actions runtime authority=false
-> retain publication-packet/RESULT_PACKET_INDEX.json
-> create local cross-framework-current-basis-v0.4-results.tar.gz
-> hash archive
-> write PUBLICATION_READY.json
```

The same packet-preparation function runs when a later resident pass finds an already-complete authentic run, so packaging may be recovered without rerunning the experiment.

Local receipt semantics:

```text
schema: stegverse.current-basis-v04.local-publication-ready/v1
state: LOCAL_PACKET_READY_FOR_EVIDENCE_TRANSPORT
network_transport_performed: false
repository_writeback_performed: false
github_actions_runtime_authority: false
publication_authority: false
credential_read_or_acquired: false
authority_effect: NONE_LOCAL_EVIDENCE_PACKAGING_ONLY
```

This closes local machine-side packet preparation only. It does not publish to GitHub, create a successful Actions run, or send material to the external evaluator. Those remain evidence-transport/distribution steps after authentic execution.

Current boundary:

```text
local source repair: MERGED / VALIDATED
package-arrival retry: MERGED / VALIDATED
local result packet preparation: IMPLEMENTED / VALIDATION PENDING
authentic resident consumption: NOT OBSERVED
S1: NOT OBSERVED
post-observation transition receipt: NOT OBSERVED
Master Records custody/replay/reconstruction: NOT OBSERVED
RUN_COMPLETE.json: NOT OBSERVED
PUBLICATION_READY.json from authentic run: NOT OBSERVED
successful external-result GitHub Action: NOT OBSERVED
```
