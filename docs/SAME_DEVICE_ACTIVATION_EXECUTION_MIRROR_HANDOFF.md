# Same-Device Activation / Execution Mirror Handoff

State: ACTIVE_ECOSYSTEM_AUDIT_AND_REMEDIATION  
Architecture owner: `StegVerse-Labs/.github#201`  
Observed: 2026-09-03

## Governing invariant

No StegVerse service may require any other machine for routine activation or routine execution, including another StegVerse node.

```text
for service S on established device/node N:

activation(S,N)
and
routine_execution(S,N)

MUST NOT require execution on M where M != N.
```

A required Mac, PC, server, cloud host, GitHub runner, remote model host, separately administered sovereign node, or another StegVerse node is an external/third-party dependency relative to the active device.

Remote peers may participate only as optional interoperability/federation/recovery peers.

## Lifecycle

```text
requires_other_machine=true
or
activation_execution_scope != SAME_DEVICE
or
required prerequisite provider != LOCAL_NODE

=> blocker_code: OTHER_MACHINE_REQUIRED
=> lifecycle_state: INCOMPLETE_REQUIRES_CONTINUED_BUILD
=> continuation_required: true
```

This is never an acceptable permanent blocked deployment state.

## Authority

```text
activation authority plane: STEGVERSE
credential authority: TV/TVC
GitHub token runtime authority: NONE
hosted CI activation authority: NONE
HB/HB-derived execution authority: NONE
Interlock/InTr authority: unchanged
WorkerCoordinator claim/fence authority: unchanged
```

TV/TVC semantics must be consumable through the same-device StegVerse path without making a second machine a required runtime or control-plane dependency.

## Completed enforcement

### StegOS

```text
issue: StegVerse-Labs/StegOS#165 CLOSED_COMPLETED
PR: StegVerse-Labs/StegOS#174
merge: 8ecf8836b5cab8546a2b10ecd1b6089be76705b4
CI: 33713239881 SUCCESS
same-device validator: INSTALLED
required remote StegVerse prerequisite: REJECTED
runtime execution proof implied by source: NO
```

### Shared resident runtime lanes

```text
issue: StegVerse-Labs/.github#871
PR: StegVerse-Labs/.github#872
merge: 6e81537b35f19c67fc2a5bce060c9650190521c3
Heartbeat validation: 33706409165 SUCCESS
organization-control validation: 33706408995 SUCCESS

SV001 #739: SAME_DEVICE semantics installed
SV002 #462: SAME_DEVICE semantics installed
Ecosystem Chat #60: SAME_DEVICE semantics installed
runtime evidence implied by source: NO
```

## Current audit truth

Earlier audit statements that cleared a path merely because it did not require a *non-StegVerse* machine are not sufficient under this stricter rule.

Owner-by-owner audit must now answer:

1. Does routine activation execute on the current established device?
2. Does routine execution execute on that same device?
3. Is every required prerequisite local to that device?
4. Can any remote StegVerse node/model/runtime/receipt producer be removed without breaking routine operation?
5. Does TV/TVC remain authority without becoming a second-machine execution dependency?
6. Are hosted CI and repository systems evidence-only?

A "no" to 1-3 or 5-6, or a "no" to removal in 4, means `OTHER_MACHINE_REQUIRED` and continued implementation.

## Existing iPhone evidence

Authentic StegOS iOS device-local inference evidence demonstrates that same-device inference is technically achievable on the current device class. It does not by itself satisfy SV001, SV002, Ecosystem Chat parent-chain, or other service-specific execution predicates.

## Remaining work

```text
ecosystem-wide audit: ACTIVE
StegOS same-device enforcement: COMPLETE_MERGED_VALIDATED
shared resident-lane semantic correction: COMPLETE_MERGED_VALIDATED
all canonical service owners audited under strict same-device rule: NOT YET COMPLETE
runtime activation implied: false
user second-machine action required: false
```

Do not assign another machine to the user. If a required same-device capability is absent, that absence is implementation work.
