# StegOS Device-Local Parent Evidence Candidate Handoff

Issue: #837
Parent: #60
State: SOURCE_IMPLEMENTATION
Authority effect: NONE

This lane verifies an exported StegOS device-local evidence bundle using the canonical
StegOS verifier from an already-local StegOS source root.

Output states:
- PARENT_EVIDENCE_CANDIDATE_VERIFIED
- FAIL_CLOSED

A verified candidate proves authentic device-local execution, reconstruction, and replay.
It never proves the Ecosystem Chat parent executed and never promotes the StegOS
device-local fencing token into a global WorkerCoordinator parent fence.

Credential authority remains TV/TVC. GitHub token required: false. Network fetch:
false. Second user-operated machine required: false.

Downstream admission or re-execution remains owned by #60.
