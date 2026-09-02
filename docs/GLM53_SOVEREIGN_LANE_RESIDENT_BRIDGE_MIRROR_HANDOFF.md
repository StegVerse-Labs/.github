# GLM-5.3-Flash Sovereign Eleven-Lane Resident Bridge Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Issue: `#819`  
State: SOURCE_IMPLEMENTATION_ACTIVE / AUTHENTIC_RESIDENT_EXECUTION_PENDING  
Authority effect: NONE_REQUEST_BRIDGE_ONLY  
Activation effect: false

## Goal

Connect the already-merged consumer-ready GLM-5.3-Flash sovereign evidence producer in `StegVerse-002/micro-node-runtime` to the existing sovereign WorkerCoordinator without creating a second scheduler, model downloader, hosted fallback, credential lane, or claim/fence path.

## Canonical upstream source

Required source merge:

`StegVerse-002/micro-node-runtime@07e4388eda92d99a8feb220f28265b147551242d`

Pinned evidence-producer blobs:
- `tools/run_glm53_sovereign_lane_evidence.py`
- `tools/evaluate_glm53_sovereign_eligibility.py`
- `tasks/SV-COST-ELEVEN-LANE-GLM-SOVEREIGN-001.prompt.md`

The resident worker verifies those exact source blobs and, for a Git checkout, requires the source merge as an ancestor.

## Installed resident surfaces

- `handoffs/SHWP-GLM53-SOVEREIGN-LANE-001.json`
- `control/worker-registry.d/glm53-sovereign-lane-001.json`
- `control/process-worker-adapters.d/glm53-sovereign-lane-001.json`
- `control/resident-execution-request.d/glm53-sovereign-lane-001.json`
- `control/task-vectors/SHWP-GLM53-SOVEREIGN-LANE-001.json`
- `workers/glm53_sovereign_lane_worker.py`
- `scripts/consume_glm53_sovereign_lane_request.py`

Dispatcher selector:

`glm53_sovereign_lane`

## Runtime contract

The task may execute only through the existing independently admitted WorkerCoordinator path.

Allowed runtime inputs are non-secret locators only:
- `STEGVERSE_MICRO_NODE_RUNTIME_ROOT`
- `STEGVERSE_GLM53_ENDPOINT`
- `STEGVERSE_GLM53_MODEL_PATH`
- `STEGVERSE_GLM53_RUNTIME_IDENTITY`

The endpoint must already be private/loopback/StegVerse-local as enforced by the upstream producer. No network model download or hosted inference substitution is permitted.

If the endpoint/model is absent, the producer emits the exact fail-closed eligibility blocker. The resident task must remain BLOCKED rather than fabricating lane-11 evidence.

## Success evidence

Completion requires one authentic resident execution that produces:
- `model=GLM-5.3-Flash`;
- `task_id=SV-RECON-001`;
- deterministic final state balance 75 / risk 3 / active;
- event decisions ALLOW, ALLOW, ALLOW, DENY, DENY, ALLOW;
- applied_count=4;
- denied_count=2;
- `vendor_api_credential_used=false`;
- no hosted substitution;
- no model download;
- consumer-compatible evidence persisted at the resident evidence path.

## Non-claims

Source merge or GitHub Actions validation is not sovereign execution.
A resident request grants no claim, fence, credential, model, provider, heartbeat, publication, or runtime authority.
Lane-11 evidence is not complete until a resident WorkerCoordinator execution emits the actual evidence.
