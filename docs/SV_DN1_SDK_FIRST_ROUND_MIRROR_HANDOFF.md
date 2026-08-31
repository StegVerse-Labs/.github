# SV-DN-1 SDK Governed First-Round Mirror Handoff

## Canonical scope

```text
goal_id: SV-DN1-SDK-GOVERNED-FIRST-ROUND-001
task_id: SV-DN1-SDK-FIRST-ROUND-001
repository: StegVerse-Labs/.github
branch: main
canonical product owner: StegVerse-org/stegverse-demo-suite
canonical product handoff: docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md
parent_task: SV-DN1-INTR-RUNTIME-001
production SDK owner: StegVerse-org/StegVerse-SDK
production StegCore owner: StegVerse-Labs/StegCore
production Core-Lite owner: Data-Continuation/core-lite
production custody owner: master-records/orchestration
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: NONE
```

## Goal

After the first authentic resident observation and route-specific InTr receipt exist, execute the exact SV-DN-1 manifest through the canonical SDK 0B production-validation route on the sovereign carrier, bind the returned result, replay/reconstruct the exact run through Master Records without consequence re-execution, and invoke the merged first-round finalizer.

This is the production-side execution path. It MUST NOT use a parallel evaluator, mock SDK route, fixture result, GitHub Actions runtime, or third-party host.

## Source of truth order

1. `docs/SV_DN1_SDK_FIRST_ROUND_MIRROR_HANDOFF.md`
2. `handoffs/SV-DN1-SDK-FIRST-ROUND-001.json`
3. `workers/sv_dn1_sdk_first_round_worker.py`
4. `StegVerse-org/stegverse-demo-suite/docs/SV_DN1_SDK_LIVE_ADMISSION_MIRROR_HANDOFF.md`
5. `StegVerse-org/stegverse-demo-suite/scripts/build_sv_dn1_sdk_ingress_manifest.py`
6. `StegVerse-org/stegverse-demo-suite/scripts/bind_sv_dn1_sdk_live_result.py`
7. `StegVerse-org/stegverse-demo-suite/scripts/finalize_sv_dn1_first_round.py`
8. `StegVerse-org/StegVerse-SDK/stegverse/governance_ingress_runtime.py`
9. `StegVerse-org/StegVerse-SDK/stegverse/sovereign_validation_runtime.py`
10. applicable exact local StegCore/Core-Lite/Master Records sources

Newer authentic runtime evidence overrides older session claims.

## Required upstream evidence

The worker requires the existing sovereign bound-state chain:

```text
SV-DN1-RESIDENT-OBSERVER-001
  -> COMPLETE / SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE

SV-DN1-INTR-RUNTIME-001
  -> COMPLETE / SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE

SV-DN1-PRODUCTION-SOURCE-PREP-001
  -> COMPLETE / SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE
```

Required local evidence roots:

```text
~/.stegverse/state/sv-dn1-resident-observer/
~/.stegverse/state/sv-dn1-intr-runtime/
~/.stegverse/source/stegverse-demo-suite/
```

The route-specific InTr receipt MUST validate under the canonical demo-suite SDK bridge and produce:

`execution_readiness: READY_FOR_SDK_0B`

Anything else returns HANDOFF_READY or fails closed.

## Canonical runtime sources

The worker consumes one completed production-source-preparation receipt:

```text
~/.stegverse/state/sv-dn1-production-source-prep/receipts/latest.json
schema: stegverse.sv-dn1.production-source-prep-receipt/v2
source_identity_scheme: sha256-content-manifest
network_source_fetch_performed: false
github_platform_required: false
```

That receipt supplies the four sovereign component roots and their content-addressed identities. The SDK worker no longer accepts four independent source-root environment variables as source admission. Repository/Git coordinates are not runtime locators.

Current production anchor blobs checked before execution:

```text
StegVerse-org/StegVerse-SDK
  stegverse/governance_ingress_runtime.py
  git_blob_sha1: 62c5ae4799ae018f6b100766215c3c68078c5b2e

  stegverse/sovereign_validation_runtime.py
  git_blob_sha1: 6bc0944633b6299c19f065f44dd5999434445dd7

StegVerse-Labs/StegCore
  src/stegcore/transaction_lifecycle.py
  git_blob_sha1: 81935669846fedd2867272810b090226b05780ab

Data-Continuation/core-lite
  core_lite/transaction_route.py
  git_blob_sha1: 734923a86bfcd4d41d07e0fb8797de50f0fb9408

master-records/orchestration
  services/manifest_receipt_custody.py
  git_blob_sha1: 26a4c1e082ee91128648b2b9bd13cc32ce915f82
```

The complete source identity from the predecessor receipt is canonical. The retained anchor hashes are migration compatibility checks only; they are not source locators or canonical source identities. Any receipt/root/identity mismatch fails closed as SOURCE_DRIFT.

## Production execution

The worker must:

1. load the authentic resident receipt, capture, exchange, and route-specific InTr receipt;
2. use the merged demo-suite builder to create the SDK candidate;
3. require `READY_FOR_SDK_0B`;
4. execute `StegVerse-SDK.governance_ingress_runtime.run_external_manifest` against a local custody database;
5. require returned schema `stegverse.sovereign-production-validation-result.v1`;
6. bind that result using `bind_sv_dn1_sdk_live_result.py`;
7. require exact `SDK_ADMITTED`;
8. generate the deterministic SV-DN-1 result receipt;
9. call canonical SDK `replay_sovereign` and `reconstruct_sovereign` on the exact manifest receipt;
10. require consequence_reexecuted=false and original_record_mutated=false;
11. call the canonical first-round finalizer;
12. preserve all outputs in this worker's bounded state.

## Governance posture

The actual StegGate disposition is not preselected.

Allowed observed governance states:

```text
ALLOW
DENY
REVIEW
FAIL_CLOSED
```

Any of these may be the authentic result. The worker must preserve it exactly.

A DENY/REVIEW/FAIL_CLOSED result is not a failed demo merely because it is not ALLOW.

## External consequence posture

SV-DN-1 is evaluation-only:

```text
external_consequence_enabled: false
external_side_effect: false
third_party_host_required: false
```

The canonical production route still executes its governance/custody lifecycle. No external system mutation is permitted.

## First-round analysis output

On success, bounded state contains:

```text
candidate/sdk-ingress-candidate.json
sdk/sdk-result.json
sdk/sdk-admission.json
sdk/replay.json
sdk/reconstruction.json
round/result-receipt.json
round/first-round-analysis.json
round/production-pipeline-observation.json
round/report.md
round/index.html
receipts/latest.json
```

The resulting dashboard is generated from authentic production receipts but is not considered publicly hosted until the separate publication/Pages gate succeeds.

## Failure / unknown policy

This worker must preserve bounded-confidence semantics.

- missing upstream authentic evidence -> HANDOFF_READY;
- missing exact local canonical artifacts -> HANDOFF_READY;
- local anchor drift -> HANDOFF_READY / SOURCE_DRIFT;
- SDK runtime/binding/reconstruction mismatch -> BLOCKED;
- governance FAIL_CLOSED -> authentic governed result, not hidden;
- first-round lane finding may remain FAIL/DEGRADED/UNKNOWN if evidence-backed;
- no missing evidence may be silently promoted.

## Authority boundary

This worker has authority only to execute the already-admitted production validation path and write its local bounded-state evidence.

It has no authority to:

- modify repositories;
- publish the dashboard;
- grant certification;
- adopt Universal Interlock;
- activate global production Interlock;
- use provider/GitHub credentials;
- mutate the evaluated Hugging Face source.

## Completion boundary

Completion transition:

`SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED`

Completion requires:

```text
candidate execution_readiness: READY_FOR_SDK_0B
SDK result schema: canonical sovereign production validation
SDK admission: SDK_ADMITTED
Master Records custody: RECORDED
replay consequence_reexecuted: false
reconstruction consequence_reexecuted: false
reconstruction original_record_mutated: false
first-round analysis state: ANALYZED
dashboard generated: true
dashboard publicly hosted: false
production perfection claimed: false
```

## Successor

After completion, the remaining machine lane is publication of the generated authentic static artifacts to the already-defined public dashboard surface, subject to the repository Pages enablement gate.

## Current state

```text
source materialization worker: MERGED / runtime completion NOT OBSERVED
resident observer worker: MERGED / runtime completion NOT OBSERVED
route-specific InTr worker: MERGED / runtime completion NOT OBSERVED
production source prep worker: IMPLEMENTING / runtime completion NOT OBSERVED
SDK bridge/result binder/finalizer source: MERGED
SDK governed first-round worker: MERGED
first authentic round: NOT ANALYZED
public live dashboard data: NOT PUBLISHED
```

## Merge and execution-chain evidence

```text
SDK first-round PR #340: MERGED
merge_commit: 778020f45571d84d9c7ed545bbe85294a91f60a0
independent admission/dependency PR #343: MERGED
merge_commit: 75fbb638a8003d42517620cc95b383070ea3b15e
sovereign one-shot chain PR #348: MERGED
merge_commit: a45095d2c2099b9318915410e78a4615b4dc68e6
chain validation runs: 33138330575 PASS / 33138330592 PASS
```

The first-round worker now has a complete machine-executable predecessor chain and resident request bridge. Its execution dependencies are now both `SV-DN1-INTR-RUNTIME-001=COMPLETED` and `SV-DN1-PRODUCTION-SOURCE-PREP-001=COMPLETED`. The latter guarantees exact SDK/StegCore/Core-Lite/Master Records roots before canonical production execution. Independent fresh fence >22 and HeartBeat reference-only semantics remain unchanged.

Authentic SDK execution, Master Records custody, and first-round analysis remain NOT OBSERVED.

## Archive readiness

This handoff is the canonical continuation source for the first canonical SDK-governed SV-DN-1 production round. Once merged, no originating conversation is required to recover the machine path.


## 2026-08-31 SDK sovereign-runtime anchor reconciliation

Live source inspection before the next SV-DN-1 sovereign execution opportunity found one
stale migration compatibility anchor:

```text
StegVerse-org/StegVerse-SDK
stegverse/sovereign_validation_runtime.py
previous expected blob: 814d4cb607cc2cb4c7a605474fe845e13540898d
current main blob:      6bc0944633b6299c19f065f44dd5999434445dd7
```

The other four retained migration anchors still match current owner-repository source.

The SDK change is attributable to the validated current-basis v0.4 reconciliation on SDK
main. It adds the optional `derived_governance_request` execution input and records its
source as `DERIVED_NATIVE_REQUEST`; the pre-existing manifest-input branch remains the
default when that optional input is absent. SV-DN-1 continues to call
`governance_ingress_runtime.run_external_manifest` without supplying a derived governance
request, so this source change does not alter the SV-DN-1 request path or grant additional
authority.

The migration anchor is therefore repinned to the current validated blob rather than
relaxed or removed. Complete source identity remains supplied by the v2
`sha256-content-manifest` source-preparation receipt; this blob pin remains a compatibility
guard only.

This reconciliation does not claim resident execution, SDK admission, custody,
reconstruction, first-round analysis, public promotion, repository persistence, deployment,
release, or certification.
