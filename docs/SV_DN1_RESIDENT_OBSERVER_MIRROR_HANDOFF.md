# SV-DN-1 Resident Observer Mirror Handoff

## Canonical scope

```text
goal_id: SV-DN1-RESIDENT-PUBLIC-SOURCE-OBSERVATION-001
task_id: SV-DN1-RESIDENT-OBSERVER-001
repository: StegVerse-Labs/.github
branch: main
canonical product owner: StegVerse-org/stegverse-demo-suite
canonical product handoff: docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: NONE
```

This lane binds the already-merged SV-DN-1 public-source observer to the sovereign WorkerCoordinator execution surface. It does not move model-evaluation ownership into `StegVerse-Labs/.github`.

## Source of truth order

1. `docs/SV_DN1_RESIDENT_OBSERVER_MIRROR_HANDOFF.md`
2. `handoffs/SV-DN1-RESIDENT-OBSERVER-001.json`
3. `control/worker-registry.d/sv-dn1-resident-observer-001.json`
4. `control/process-worker-adapters.d/sv-dn1-resident-observer-001.json`
5. `workers/sv_dn1_resident_observer_worker.py`
6. `cost-basis/worker-runtime/sv-dn1-resident-observer.json`
7. `StegVerse-org/stegverse-demo-suite/docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md`
8. `StegVerse-org/stegverse-demo-suite/tasks/SV-DN1-RESIDENT-OBSERVER-001.json`

Newer live runtime evidence overrides older chat/session claims.

## Goal

On an admitted sovereign StegVerse node, perform one exact public-source observation against:

`https://huggingface.co/api/models/Qwen/Qwen3-8B`

using the canonical locally materialized `stegverse-demo-suite` implementation.

The worker must preserve:

```text
exact public source bytes
-> raw SHA-256 before semantic normalization
-> source-capture receipt
-> HF-facing semantic Interlock exchange
-> destination-side structural validation
-> fenced local receipt
```

This worker stops before InTr runtime traversal and SDK live admission.

## Why this worker exists

The demo-suite source is already merged and source-validated. The missing claim is authentic resident observation.

GitHub Actions is validation-only and may not be repurposed as:

- production observer;
- external-source runtime;
- control plane;
- credential authority;
- publication authority;
- SDK admission authority;
- certification authority.

The resident worker therefore provides the exact non-hosted execution boundary needed to obtain authentic source-capture evidence.

## Public network boundary

Allowed:

```text
method: GET
scheme: HTTPS
hosts:
  - huggingface.co
  - *.huggingface.co
authentication: NONE
credential_forwarding: false
```

The worker may not:

- send Authorization headers;
- consume Hugging Face credentials;
- use GitHub tokens;
- perform remote repository checkout;
- follow redirects outside the admitted Hugging Face boundary;
- write back to either source repository.

## Materialized source boundary

The worker consumes exact local source only.

The local demo-suite executable/config source must additionally match the merged runtime-source manifest:

```text
config/sv_dn1_runtime_source_manifest.json
schema: stegverse.sv-dn1.runtime-source-manifest/v1
hash_profile: git-blob-sha1
source_basis_commit: ccd8a1886e8b87865cfcc541be5f32bf59f34e17
drift_policy: FAIL_CLOSED
```

File presence alone is no longer sufficient. Any pinned byte drift returns HANDOFF_READY / blocked source materialization rather than executing an ambiguous production observation.

Optional locator:

`STEGVERSE_SV_DN1_SOURCE_ROOT`

Canonical fallback locations may be inspected locally, but remote checkout is prohibited.

Required local files:

```text
docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md
tasks/SV-DN1-RESIDENT-OBSERVER-001.json
scripts/observe_sv_dn1_hf_public.py
scripts/sv_dn1_hf_interlock.py
scripts/sv_dn1_stegverse_interlock.py
config/sv_dn1_hf_mapping.v1.json
config/sv_dn1_runtime_source_manifest.json
```

Missing source means `HANDOFF_READY`, not a fabricated success and not a duplicate source-retrieval lane.

## Bound-state outputs

Only the ProcessWorkerAdapter bound-state mirror may be written:

```text
observed/source-capture.json
observed/native.json
observed/exchange.json
receipts/latest.json
```

No repository mutation is authorized.

## Completion boundary

Completion for this worker means:

```text
resident source capture: OBSERVED
raw response hash: VERIFIED
HF-facing semantic exchange: VERIFIED
destination structural validation: PASS
credential use: false
repository writeback: false
SDK admission: false
InTr live traversal: NOT CLAIMED
public dashboard live: NOT CLAIMED
```

The next successor lane after this worker completes is the merged machine-owned route-specific InTr runtime task `SV-DN1-INTR-RUNTIME-001`. SDK live admission remains the successor after that InTr receipt exists.

## Collision boundary

Do not create another worker that independently fetches the same source for this goal while `SV-DN1-RESIDENT-OBSERVER-001` is HANDOFF_READY, CLAIMED, or running.

The canonical demo-suite task remains the product-level owner. This `.github` lane only owns sovereign execution of the first live source-capture step.

## Machine predecessor

The missing exact-local-source prerequisite now has a dedicated machine-owned predecessor:

```text
task: SV-DN1-SOURCE-MATERIALIZATION-001
worker: sv-dn1-source-materialization-worker
handoff: docs/SV_DN1_SOURCE_MATERIALIZATION_MIRROR_HANDOFF.md
state: HANDOFF_READY / source merged
PR #337: MERGED
merge_commit: f5ca06543d1dd17b3095d424dc5eed578c15299d
```

This predecessor may materialize the exact pinned demo-suite bytes without GitHub credentials, remote checkout, repository writeback, or observation authority. Completion only releases the existing resident observer's local-source prerequisite; it does not perform the Hugging Face observation.

## Machine successor

The route-specific InTr successor is now machine-owned and merged:

\`\`\`text
task: SV-DN1-INTR-RUNTIME-001
worker: sv-dn1-intr-runtime-worker
handoff: docs/SV_DN1_INTR_RUNTIME_MIRROR_HANDOFF.md
PR #339: MERGED
merge_commit: ab6172bb1938bdb00ec7af80858547c3dcbd45ed
runtime receipt: NOT OBSERVED
\`\`\`

It consumes this worker's authentic receipt/capture/exchange and emits the exact stegverse.sv-dn1.intr-runtime-receipt/v1 route receipt only after canonical destination validation. It does not claim Universal Interlock adoption/global activation or SDK admission.

## Independent task-control dependency

PR #343 merged the explicit dependency and independent admission:

```text
dependency: SV-DN1-SOURCE-MATERIALIZATION-001
parent terminal state: COMPLETED
parent terminal transition: SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE
authority_domain: INDEPENDENT_TASK_CONTROL
fresh fence: >22
heartbeat_grants_execution_authority: false
merge_commit: 75fbb638a8003d42517620cc95b383070ea3b15e
```

PR #348 merged a resident request/chain runner that can invoke this task only after the source predecessor is terminal. The request grants no authority. Authentic resident execution remains NOT OBSERVED.

## Current state

```text
canonical demo-suite source: MERGED
demo-suite public observer source: MERGED
demo-suite resident task: MERGED
real public web parsed preflight: OBSERVED / NONADMISSIBLE_AS_LIVE_SOURCE_CAPTURE
.github executable handoff: MERGED
.github worker registry: MERGED
.github process adapter: MERGED
.github worker implementation: MERGED
.github cost basis: MERGED
.github tests: MERGED
exact pinned local source: NOT OBSERVED / predecessor SV-DN1-SOURCE-MATERIALIZATION-001 registered
resident source capture: NOT OBSERVED
raw-byte digest: NOT OBSERVED
HF semantic exchange runtime: NOT OBSERVED
InTr live traversal: NOT OBSERVED
SDK live admission: NOT OBSERVED
dashboard live publication: NOT OBSERVED
```

## Merge and validation evidence

```text
PR #335: MERGED
merge_commit: d3dec277360327085ceb0266cfbf1f92e633da4e
validated_head: 00762a32bac060cc33daa5638335d26aa86a2fe3
organization control plane run 33127505443: PASS
heartbeat worker validation run 33127505433: PASS
complete deterministic repository suite: PASS
AE handoff/registry conformance: PASS
workflow token-authority checks: PASS
```

The resident observer is now registered and source-valid on main. This does not claim that WorkerCoordinator has yet bound a live claim or that a resident runtime receipt exists.

## Exact source-pin merge evidence

```text
demo-suite runtime source pin: PR #12 MERGED
demo-suite merge_commit: 6d520d36b45a2f4ff02f5e97a4190a089a6d1fb6
resident enforcement: PR #336 MERGED
resident enforcement merge_commit: 436431dfdbedf6614c291a59b0da2d3f62612df1
organization control-plane run 33129172918 / job 98714401407: PASS
heartbeat worker validation run 33129172924 / job 98714401859: PASS
```

The resident worker now refuses ambiguous local demo-suite executable/config bytes. An authentic capture can only proceed after the locally materialized source satisfies the exact runtime-source manifest.

## Archive readiness

This handoff captures the current execution ownership, authority ceiling, remaining files, collision boundary, and successor boundary. Once merged, no originating chat is required to recover this task.
