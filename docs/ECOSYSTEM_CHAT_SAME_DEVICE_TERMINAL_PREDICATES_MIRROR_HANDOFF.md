# Ecosystem Chat Same-Device Terminal Predicates Mirror Handoff

Updated: 2026-09-05
Repository: `StegVerse-Labs/.github`
Architecture owner: `.github#201`
Task: `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`

## Defect

The canonical parent terminalizer accepted only the native/private-process runtime pair:

```text
real_model_process_observed=true
private_endpoint_only=true
```

The already-implemented current-iPhone sovereign runtime intentionally reports those two predicates false and instead proves:

```text
browser_service_worker_runtime_observed=true
device_local_intercepted_endpoint=true
network_egress_required=false
real_inference_response_observed=true
endpoint_transport=SERVICE_WORKER_LOCAL_INTERCEPT
endpoint=https://stegverse.org/stegos-bootstrap/local-model
service_worker_scope=https://stegverse.org/stegos-bootstrap/
```

The TVC, LLM-adapter, and Master Records web-runtime validators already accept this exact device surface. Therefore the parent terminalizer's process-only predicate was a same-device activation defect.

## Repair

`scripts/run_independent_ecosystem_chat_parent.py` now classifies the sovereign execution surface as either:

1. `PRIVATE_PROCESS` — existing process/private endpoint path; or
2. `CURRENT_USER_IPHONE_SERVICE_WORKER` — exact current-iPhone service-worker path above.

Terminal activation requires the aggregate:

```text
sovereign_runtime_execution_surface_observed=true
```

rather than requiring process-only facts to be true.

The receipt preserves actual source predicates. A service-worker execution therefore remains:

```text
real_model_process_observed=false
private_endpoint_only=false
device_local_runtime_observed=true
runtime_execution_surface=CURRENT_USER_IPHONE_SERVICE_WORKER
sovereign_runtime_execution_surface_observed=true
```

No false process/private evidence is created.

## Unchanged terminal requirements

The runtime-surface repair does not relax:
- exact TVC route verification;
- exact LLM-adapter execution verification;
- measured usage;
- Master Records reconstruction verification;
- provider-usage reconstruction PASS;
- transition reconstruction PASS;
- same-execution identity;
- persistent conversational runtime readiness;
- TV/TVC credential authority / `NONE` credential requirement;
- no GitHub token / no hosted production authority;
- bounded fresh parent claim/fence;
- fail-closed release on nonterminal or scope failure.

## README impact

README update is **required**. This changes runtime prerequisite/failure semantics for a canonical parent task by recognizing an already-supported same-device service-worker runtime as a valid sovereign execution surface. `README.md` is updated in the same change set.

## Non-inference boundary

Source, merge, CI, and this repair do not prove that the current iPhone executed the task, that a fresh fence was issued, that measured usage or reconstruction occurred, or that Ecosystem Chat activated.

## Next transition

After merge, project the already-merged canonical Ecosystem Chat portable WorkerCoordinator package plus exact TVC/LLM-adapter/Master-Records web runtimes into StegOS, execute them on `CURRENT_USER_IPHONE`, and preserve the resulting authentic device evidence for parent/activation consumption.
