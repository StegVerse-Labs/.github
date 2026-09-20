# SDK Four-Stage Manifest Experiment Rerun Mirror Handoff

Updated: 2026-09-20
Goal Task ID: `SDK-FOUR-STAGE-MANIFEST-EXPERIMENT-RERUN-001`
Parent Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-TEST1-AUTHENTIC-RUNTIME-001`
COSV ID: `71000000111111`
Status: ACTIVE / CHECKED OUT

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
