# SV-DN-1 Resident Observer Mirror Handoff

## Canonical scope

```text
goal_id: SV-DN1-RESIDENT-PUBLIC-SOURCE-OBSERVATION-001
task_id: SV-DN1-RESIDENT-OBSERVER-001
repository: StegVerse-Labs/.github
branch: feature/sv-dn1-resident-observer
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

The next successor lane after this worker completes is route-specific InTr traversal plus SDK live admission.

## Collision boundary

Do not create another worker that independently fetches the same source for this goal while `SV-DN1-RESIDENT-OBSERVER-001` is HANDOFF_READY, CLAIMED, or running.

The canonical demo-suite task remains the product-level owner. This `.github` lane only owns sovereign execution of the first live source-capture step.

## Current state

```text
canonical demo-suite source: MERGED
demo-suite public observer source: MERGED
demo-suite resident task: MERGED
real public web parsed preflight: OBSERVED / NONADMISSIBLE_AS_LIVE_SOURCE_CAPTURE
.github executable handoff: IMPLEMENTED_ON_FEATURE_BRANCH
.github worker registry: PENDING
.github process adapter: PENDING
.github worker implementation: PENDING
.github cost basis: PENDING
.github tests: PENDING
resident source capture: NOT OBSERVED
raw-byte digest: NOT OBSERVED
HF semantic exchange runtime: NOT OBSERVED
InTr live traversal: NOT OBSERVED
SDK live admission: NOT OBSERVED
dashboard live publication: NOT OBSERVED
```

## Archive readiness

This handoff captures the current execution ownership, authority ceiling, remaining files, collision boundary, and successor boundary. Once merged, no originating chat is required to recover this task.
