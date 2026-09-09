# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
Canonical PR: `StegVerse-Labs/.github#1261`
COSV: `50000000100000`
Status: `ACTIVE / PARTIAL_SOLUTIONS_MACHINE_PROJECTED_ACROSS_18_MEMBERS / RESIDENT_CONVERGENCE_EXECUTION_WIRED_AND_VALIDATED / AUTHENTIC_RESIDENT_CONVERGENCE_RECEIPT_PENDING`

## Purpose

Converge all StegVerse ecosystem capabilities that are implemented or integration-ready but still require authentic runtime execution/evidence, receipt custody, reconstruction, runtime-bound validation, or downstream propagation proof. The umbrella preserves child Goal Task IDs and resumes each child from its first genuinely unresolved evidence predicate instead of restarting completed stages.

## Canonical registration on PR #1261

- `data/canonical-task-records/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json`
- `control/task-vectors/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json`
- `control/task-vector-index.d/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json`
- `docs/GLOBAL_RUNTIME_EVIDENCE_CONVERGENCE_MATRIX.md`
- `control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json`
- `tools/validate_runtime_partial_solution_projection.py`
- `scripts/run_global_runtime_evidence_convergence.py`
- `tests/test_global_runtime_evidence_convergence_execution.py`
- this handoff

The repository's sharded task/vector resolution path is used intentionally. The task record is `ACTIVE / CLAIMED_INTEGRATION`, the task.v1 COSV record is `50000000100000`, and the index shard resolves directly to the canonical task-record shard.

## Partial-solution implementation

The earlier issue-level fanout is now materialized as a machine-readable projection contract rather than remaining advisory prose.

`control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json` contains all 18 current umbrella members. For each member it records canonical task identity, reusable mechanisms adopted from more advanced sibling lanes, and the exact stage at which that member must resume. The projection forbids generic runtime restart for later-stage lanes and permits cross-task evidence reuse only when exact subject binding is compatible.

The seven reusable solution classes are:

1. `HIL_G25_BROWSER`
2. `HF_UNIVERSAL_INTR`
3. `VACC_LOCAL_RUNTIME`
4. `DE006_SAME_EXEC_RECONSTRUCTION`
5. `SV001_POST_TERMINAL_CONTINUATION`
6. `EXACT_RESIDENT_REQUEST`
7. `RUNTIME_PROFILE_MAP`

`tools/validate_runtime_partial_solution_projection.py` rejects missing members, duplicate task IDs, unknown solution identifiers, empty adoption sets, empty resume stages, generic-runtime restart of later-stage lanes, or cross-task receipt reuse without exact subject binding.

This establishes `REUSABLE_PARTIAL_SOLUTIONS_PROJECTED` at source/control level for the current 18 members. It does not claim the physical resident has executed those projected mechanisms yet.

## Resident convergence execution now wired

The projection is now connected to the existing sovereign resident execution path rather than remaining a passive map.

A bounded convergence visitor now exists at:

`script/run_global_runtime_evidence_convergence.py` is intentionally not a second scheduler or dispatcher. The actual path is `scripts/run_global_runtime_evidence_convergence.py` and it invokes only selectors already registered in `scripts/dispatch_resident_execution_requests.py`.

The Canonical Runtime Profile Map remains the shared diagnostic trigger. `scripts/install_and_run_canonical_work_event_bootstrap.py` now performs the ordinary task-specific Canonical Work bootstrap first. When the admitted task is exactly `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`, it then materializes the already-local convergence helper/projection and runs that helper against the same resident root.

The convergence helper:

- selects all currently compatible registered child consumers in one resident visit;
- excludes `canonical_work_coordination` to prevent recursion;
- preserves each member's projected resume stage and adopted solution set;
- records registered-selector outcomes separately per member;
- recognizes Canonical Work-only ingress evidence for CryptoBot and StegBrowser;
- reports `NO_REGISTERED_SELECTOR` for current members whose task-specific execution still lacks a compatible registered resident selector rather than flattening them into `runtime pending`;
- writes `receipts/sovereign-host/global-runtime-evidence-convergence.latest.json` with per-lane runtime outcomes, runtime-state counts, unresolved-resume-stage counts, and whether all members actually converged on one state.

Current explicit no-selector members are VACC adapter execution, StegClaw P4, Endpoint Fanout, GADI controlled actuator execution, and DE-006 parent rebinding/re-execution. That classification is now machine-observable and gives those lanes a concrete integration defect if they remain unwired after the convergence receipt is produced.

A canonical umbrella resident request is also staged at `control/resident-execution-request.d/canonical-work-global-runtime-evidence-closure-001.json`; no claim is made that this request has been authentically consumed yet.

## Current member routing after projection

- CryptoBot -> exact request consumption.
- HIL -> ESRL `LEASE_OPEN`.
- Hugging Face / SV-DN1 -> SDK first-round resident analysis.
- SDK / Ecosystem Chat -> exact parent/SDK execution.
- VACC -> canonical adapter execution.
- DEVICE_KV / MyKV -> subject-bound resident request execution.
- StegVerse-001 -> current-device continuation without rerunning terminal execution.
- SV002 -> authentic materialization consumption.
- StegClaw -> resident process + request consumption.
- Endpoint Fanout -> authentic DEVICE_KV parent.
- GADI -> WorkerCoordinator claim/fence.
- Governed Multilane Manifold -> per-child claim/fence + formalism execution.
- GLM 5.3 Sovereign -> subject-bound GLM execution.
- SV-011 Phase 5 -> subject-bound Phase-5 execution.
- Runtime Profile Map -> CanonicalWork `INGRESS_ADMITTED`, then convergence visitor.
- Native Email -> provider runtime consumption.
- StegBrowser -> authentic browser invocation.
- DE-006 -> exact parent rebinding/re-execution.

## Failure-point interpretation

The different stopping points do reflect reusable partial solutions. After source/control projection and execution wiring, a member that still fails at an earlier stage can no longer be explained merely by the sibling mechanism being unknown or unassigned.

The next authentic resident convergence receipt is now the decisive comparison. It will distinguish:

1. a shared resident/request failure across multiple selectors;
2. task-specific consumer/claim/InTr/component failures after request consumption;
3. post-execution custody/reconstruction/propagation failures; and
4. missing task-specific resident-selector integration (`NO_REGISTERED_SELECTOR`).

Only after that receipt exists should clusters be collapsed further.

## Exact-head validation evidence

PR #1261 head `47b74f6e80cf35ff6151e32fa84badf2ee191c96` contains the convergence runner, Runtime Profile Map bootstrap hook, and regression coverage. All three repository validation surfaces completed successfully on that exact head:

- organization control plane run `34364612570` — SUCCESS
- deterministic repository suite run `34364612579` — SUCCESS
- Heartbeat Worker Project run `34364612713` — SUCCESS

These validations prove source/control consistency only. They do not substitute for `receipts/sovereign-host/global-runtime-evidence-convergence.latest.json` from the sovereign resident.

## Next execution sequence

1. Existing resident Canonical Work consumer visits the staged Runtime Profile Map request.
2. Authentic Runtime Profile Map Canonical Work ingress succeeds.
3. The bootstrap hook executes the convergence visitor against the same resident root.
4. Already-registered compatible child consumers are visited from their projected resume points.
5. The convergence receipt records per-member states and explicit no-selector integrations.
6. Repair the first common runtime failure if one emerges; otherwise repair the smallest remaining selector/component-specific groups.
7. Reconcile resulting child evidence into Master Records and regenerate the convergence matrix.

## Manual work

None currently required. The source/control implementation is complete enough for the existing resident to perform the convergence visit automatically when the Runtime Profile Map Canonical Work request is authentically consumed. Authentic resident evidence is still required before runtime-state claims are advanced.
