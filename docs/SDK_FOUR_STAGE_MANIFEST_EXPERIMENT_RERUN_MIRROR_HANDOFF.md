# SDK Four-Stage Manifest Experiment Rerun Mirror Handoff

Updated: 2026-09-20
Goal Task ID: `SDK-FOUR-STAGE-MANIFEST-EXPERIMENT-RERUN-001`
Parent Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-TEST1-AUTHENTIC-RUNTIME-001`
COSV ID: `71000000111111`
Status: RETIRED / COMPLETED / VALIDATED

## Purpose

Repair and rerun the four-stage manifest-only SDK experiment against current SDK source. The experiment must freeze one exact SDK source identity before execution, build all four manifests before any stage runs, execute every stage only through the public Manifest Builder -> run-manifest surface, and retain raw manifests/results/hash inventory alongside human-readable post-test reports.

## Required repairs

1. Task 4 concurrency evidence must measure the actual post-barrier worker execution interval, not pre-barrier readiness/waiting time.
2. Freeze proof must bind the full execution-relevant SDK source identity, not only a subset of package files.
3. Test 3 documentation must describe exactly what differs from Test 2 and must not imply a distinct runtime behavior unless the manifest actually supplies one.
4. The final report ZIP must contain the raw replay evidence referenced by the PDFs.

## Execution order

```text
interpretation/pre-test
-> freeze exact current SDK source
-> build all four manifests
-> Test 1 run-manifest
-> Test 2 run-manifest
-> Test 3 run-manifest
-> Task 4 run-manifest
-> verify unchanged source identity
-> retain raw evidence
-> produce post-test reports
```

No test-specific runtime, scheduler, dispatcher, authority plane, credential path, or hidden non-manifest execution input may be introduced.

## Initial source observation

Current SDK main observed at task registration: `33dc1b9df68a3a5d18a977aca09fddb6037cd043` (SDK 1.3.0 closeout). The historical experiment workflow is still frozen to `4c8b72b317fdb4fb5f5e6879dd028c04ee89bb97` and therefore must be replaced for this rerun.

Task 4 currently records `started_ns` before the barrier wait, so the existing `simultaneous_overlap_observed` result is not evidence of overlapping execution. Repair that generic observation before establishing the new freeze.


## Final closure - 2026-09-20

The repaired experiment completed end to end against exact SDK head `0f74d3b1ec2226d6cf668a6bd011b3e8cf104985` in GitHub Actions run `35545606808`. All four stages passed and all 12 applicable exact-head SDK validation workflows passed.

SDK PR #298 merged as `310c9fe7988a659c22764f4e16e2086f7cb22b12`. The tested head and merged main commit share exact Git tree `56d6d64b4f887130792e7dd0e4cfe1553e0b12fc`, preserving the tested source bytes.

Retained workflow artifact:
- artifact ID: `10616772029`
- artifact SHA-256: `05a45ba5feb820a26106d6c2e112dd8571d9da9a61abad482de0e2e58297df21`

Delivered documentation/evidence bundle SHA-256:
`91e4034b20c399a78a757103c650a5faa16a18c66ea14815f003d7ddf2448ef7`

Final interpretation boundaries:
- Test 3 is a same-route invariance/person-neutrality test using the installed `atomic_task_worker` processor; it does not claim a separate Test-3 runtime.
- Task 4 proves overlapping concurrent worker invocation lifetimes. It explicitly does not claim CPU-parallel instruction execution.
- Raw manifests/results/source-index/metadata/hash inventory accompany the PDFs, so the reports no longer depend on unavailable retained files.

No remaining experiment predicate is open.
