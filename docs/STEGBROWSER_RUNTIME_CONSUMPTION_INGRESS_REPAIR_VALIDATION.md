# StegBrowser Runtime Consumption Ingress Repair Validation

Goal Task ID: `STEG-BROWSER-RUNTIME-CONSUMPTION-001`
COSV: `40000100100000`

This branch repairs only the canonical resident-ingress pointer from the superseded parent to the active runtime-consumption successor.

Validation must establish:

- the successor request is COSV-bound and non-authorizing;
- the superseded parent remains `SUPERSEDED` and is not the active StegBrowser request in `REQUEST_SPECS`;
- the active consumer stages `STEG-BROWSER-RUNTIME-CONSUMPTION-001` through the existing Canonical Work entrypoint;
- the existing bootstrap applies the established StegBrowser/global convergence continuation to the successor;
- no credential path, scheduler, dispatcher, runtime authority, second-machine requirement, or network source fetch is introduced.

This validation does not claim authentic resident execution, Task Registry `CONTINUE`, WorkerCoordinator claim/fence, Interlock/InTr admission, TVC promotion, runtime restart, observer execution, or `OWNER_INGRESS_READY_OBSERVED`.
