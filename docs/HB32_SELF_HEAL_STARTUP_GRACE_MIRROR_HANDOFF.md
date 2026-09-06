# HB32 Self-Heal Startup Grace Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent authority: `docs/RESIDENT_WORKER_SELF_HEAL_MIRROR_HANDOFF.md`  
Preflight: `receipts/preflight/HB32-SELF-HEAL-STARTUP-GRACE-002.json`  
State: `SOURCE_REPAIR_IMPLEMENTED / VALIDATION_PENDING`  
Authority effect: `NONE_SOURCE_AND_SUPERVISION_SEMANTICS_ONLY`

## Canonical runtime solution reused

This repair does not create a runtime solution. It reuses the already-installed chain:

```text
HB32 independent oscillator
-> heartbeat_runtime.engine_v13.HeartbeatRuntime carrier
-> carrier-owned scripts/repair_resident_worker_presence.py supervision
-> existing heartbeat_runtime.worker_runtime.WorkerCoordinator
-> existing scripts/dispatch_resident_execution_requests.py
-> existing task-specific resident consumers, including HIL request 002
```

The oscillator/carrier grants no execution authority. WorkerCoordinator retains claim/fence and task-admission authority, InTr/Interlock retains transition authority, and TV/TVC retains credential authority.

## Runtime defect

The existing self-heal supervisor waits only a short bounded interval for the first task-capable WorkerCoordinator tick. The WorkerCoordinator may synchronously perform already-existing source refresh, rendezvous, and resident-request dispatch before its first `cycle()`, and resident dispatch is allowed to run much longer than that first-tick proof interval.

Before this repair, a healthy newly spawned WorkerCoordinator could therefore still be alive and draining resident work when supervision classified the missing tick as repair failure and terminated it. The next HB-scale supervision visit could restart the same process and reproduce the failure loop.

PR #1084 independently fixed a different state: a **previously proven** WorkerCoordinator whose cycle later becomes stale must be recycled. That stale-worker repair remains canonical and must not be weakened.

## Repair semantics

The states are now distinguished:

```text
previously proven worker + current cycle fresh
-> reuse worker

previously proven worker + stale/non-task-capable
-> existing PR #1084 controlled worker-only recycle

newly spawned worker + first tick observed
-> repaired presence

newly spawned worker + first tick timeout + exact PID still alive
-> retain exact PID
-> WORKER_REPAIR_PENDING_TASK_CAPABLE_TICK
-> persist startup baseline
-> do not SIGTERM
-> do not create second WorkerCoordinator

later supervision + same pending PID + runtime_tick <= baseline
-> WORKER_PRESENT_AWAITING_TASK_CAPABLE_TICK
-> retain exact PID

later supervision + same pending PID + runtime_tick > baseline
-> prove task-capable startup transition
-> normal presence/freshness semantics resume

newly spawned worker exits before first tick
-> existing fail-closed repair failure path
```

PID existence never becomes runtime-presence proof by itself.

## HIL relevance

The HIL sovereign receiver already has resident request `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002` and the existing HIL consumer/WorkerCoordinator path. This startup repair removes a carrier/self-heal failure mode that could prevent that existing resident dispatcher from surviving long enough to consume request 002. It does not itself prove HIL request consumption, HIL claim/fence, receiver READY, custody, TVC lifecycle admission, or activation.

## README completeness

README impact is material because resident failure-recovery behavior changes. `README.md` is updated in this same change set to distinguish pending-first-tick startup from previously proven stale-worker recycling.

## Validation boundary

Required before merge:

- focused startup-grace regression tests pass;
- existing stale-worker recycle tests remain passing;
- Heartbeat Worker Project validation succeeds on exact head;
- organization control-plane validation succeeds on exact head;
- no GitHub token or non-TV/TVC credential gains runtime authority.

Source/CI completion is not authentic runtime execution evidence. After merge, the next authentic evidence remains a real resident carrier supervision visit followed by a fresh WorkerCoordinator tick and task-specific consumption/claim/fence receipts.
