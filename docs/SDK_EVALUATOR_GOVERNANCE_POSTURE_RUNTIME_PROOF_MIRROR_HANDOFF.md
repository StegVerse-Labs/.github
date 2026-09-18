# SDK Evaluator Governance Posture Runtime Proof Mirror Handoff

Goal Task ID: `SDK-EVALUATOR-GOVERNANCE-POSTURE-RUNTIME-PROOF-001`
Parent: `SDK-EVALUATOR-GOVERNANCE-POSTURE-MANIFEST-001`
COSV: `71000000100110`
Status: `ACTIVE / AUTHENTIC RUNTIME PROOF PENDING`

## Purpose
Own only the authentic resident execution proof transferred from the completed parent source/console goal. Reuse the existing resident dispatcher and exact SDK entry point `run_evaluator_governance_manifest`. Do not create another runtime, scheduler, governance/credential/transition authority, request path, or second user-operated device.

## Canonical execution path
```text
existing resident dispatcher
-> bounded sdk_evaluator_governance_posture consumer
-> exact manifested evaluator input
-> run_evaluator_governance_manifest
-> external_manifest_to_public_request
-> StegOS intr_security_posture_resolution.resolve_task_security_posture
-> Interlock/InTr posture resolution over exact task/payload/transition request
-> governed result
-> retained resident receipt
```

Registration/tests are source evidence only. Authentic completion requires a retained resident machine result binding exact manifest/graph hash when present, projected-input hash when applicable, transition_request_sha256, posture instance id/hash, `resolution_authority=INTERLOCK_INTR`, `posture_bound_execution=true`, `sdk_resolved_posture=false`, and custody/result locator. GitHub Actions cannot substitute.

TV/TVC remains credential authority; Interlock/InTr remains transition/posture authority; SDK is representation/transport/evidence only; HB is observability only; GitHub has no runtime authority. `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` remains a separate downstream consumer.

## First implementation seam
Add only the bounded request-specific consumer and dispatcher registration needed to invoke `run_evaluator_governance_manifest` from the existing resident carrier. Reuse WorkerCoordinator/ProcessWorkerAdapter/Interlock paths where admission is required; do not repurpose READ_REVIEW or create a parallel runtime.
