# StegOS Device-Local Parent Evidence Candidate Handoff

Issue: #837
Parent: #60
State: PARENT_EVIDENCE_CANDIDATE_VERIFIED
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


## Exact DE-006 binding requirement

After StegOS merge `04974cab2963c6d28c1cbb7bc9d54e2226d1feb9`, a parent
evidence candidate is accepted only when the exported bundle contains a
`stegos.web_admitted_inference_receipt.v1` whose `request_sha256` exactly matches
the verified device-task claim and whose `execution_binding` exactly equals:

```json
{
  "schema": "stegos.web_execution_binding.v1",
  "goal_id": "DE-006",
  "task_id": "DE-006",
  "source_repository": "Admissible-Existence/GCAT-BCAT",
  "review_tag": "decision-envelope-review-v0.1.0",
  "review_commit": "7e053d007e416ff51e76cb4e9c0ffd73943b3acc",
  "authority_effect": "NONE_BINDING_ONLY"
}
```

A generic valid StegOS device task is therefore no longer sufficient for the DE-006
candidate state. Wrong tag/commit/task/repository/binding fails closed.

This still does not prove #60 parent execution. The candidate remains observation-only
until independently admitted/re-executed under the parent authority.


## Authentic DE-006 candidate verification — 2026-09-03

Exact exported CURRENT_USER_IPHONE evidence bundle was verified against the canonical #837 acceptance conditions.

Result:
- state: `PARENT_EVIDENCE_CANDIDATE_VERIFIED`;
- device-local execution proven: `true`;
- exact DE-006 execution binding verified: `true`;
- task: `STEGOS-LOCAL-INFERENCE-bde14fe691cc86924cee9a44`;
- claim: `STEGOS-STEGOS-LOCAL-INFERENCE-bde14fe691cc86924cee9a44-G11`;
- fencing token: `11`;
- reconstruction: `PASS`;
- `same_execution=true`;
- replay relation: `VALID_APPEND_ONLY_DESCENDANT`;
- final journal tail: `897b9c70e704243939659009ef8d2e9d5ba984d1c4d0edd835afdaf26c5f4b69`;
- bound admitted-inference receipt SHA-256: `26728181de31c9b3d402c2cb30414a83aedfbfa175cc8fe7a1e2af68f5874fe4`.

Authority remains unchanged:
- `parent_execution_proven=false`;
- `global_workercoordinator_authority=false`;
- device-local fence is not promoted to the parent fence;
- resident request `RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002` remains the existing request;
- #60 must independently consume the request and acquire a fresh parent fence >22 before parent execution can be claimed.
