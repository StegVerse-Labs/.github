# Current-iPhone TestFlight Successor Allocation Mirror Handoff

Updated: 2026-09-09

```text
parent_goal: STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
adjacent_task: TASK-2026-0010
repository: StegVerse-Labs/Site
workspace: claim/current-iphone-testflight-static-bootstrap-r1
execution_surface: CURRENT_USER_IPHONE
credential_authority: TV/TVC
github_runtime_authority: NONE
```

## Purpose

Close the bootstrap/source-device seam that prevents newly merged resident control-plane source from becoming current-iPhone-local code.

The canonical StegOS successor package already exists at:

`release/current-iphone-site-projection/successors/current-iphone-testflight-static-bootstrap.json`

It binds the validated current-iPhone signer WASM, wasm-bindgen glue, unsigned IPA, signing executor, TVC provider client, and TestFlight action. Site does not yet project those assets.

## Allocation rule

TASK-2026-0008 remains unchanged and must not be widened. TASK-2026-0010 is a distinct non-overlapping Site successor scope:

`site:current-iphone-testflight-static-bootstrap`

The existing portable organization allocator remains the sole same-device claim allocator. The package retains its existing authority epoch and predecessor state. Persisted G3/G4/G5 state remains valid; a missing persisted TASK-0010 status falls back to the packaged queued status. Existing claims remain in the collision set and are not reset.

Expected continuation after TASK-0007/0008/0009 are already active:

```text
retained claim generation: 5
-> existing portable allocator CAS
-> TASK-2026-0010 selected if exact scope remains non-colliding
-> claim generation/fence: 6
-> current-iPhone claim observation retained
-> only then Site successor branch may mutate scoped product files
```

The source package does not claim that G6 has occurred.

## Site successor scope

The task owns only the TestFlight static bootstrap destinations declared by the StegOS successor package plus its Site handoff/task record/README reconciliation. It does not own TASK-0008 paths or the HB31 TASK-0009 autostart path.

## Authority

- HeartBeat grants no claim or execution authority.
- Site/static hosting grants no claim authority.
- GitHub source/CI/merge grants no runtime or claim authority.
- TV/TVC remains credential authority.
- The canonical organization allocator remains claim authority.
- WorkerCoordinator authority is unchanged.
- No second user-operated device or external machine is required.

## Current state

```text
StegOS static successor package: READY
Site static assets: NOT PROJECTED
TASK-2026-0010: QUEUED_SOURCE
portable allocator package includes TASK-0010: SOURCE CHANGE PREPARED
G6 current-iPhone allocation: NOT OBSERVED
Site scoped mutation authorization: NOT YET OBSERVED
```

After an authentic G6 claim is observed, project exact successor bytes into Site, validate hashes against the StegOS package, merge under the fresh claim, then continue current-iPhone bootstrap/TestFlight materialization and the resident relay-return runtime rerun.
