# Ecosystem Chat Master Records Bridge Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/HEARTBEAT_CONTINUITY_WORKER_MIRROR_HANDOFF.md` and authoritative only for the heartbeat-side integration of `master-records/orchestration` task `MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024` into `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`.

## Active claim

```text
task_id: SHWP-ECOSYSTEM-CHAT-MASTER-RECORDS-RECONSTRUCTION-002
originating_goal: continue the no-GitHub-token sovereign local-model chain through exact same-carrier Master Records provider-usage + transition reconstruction
repository: StegVerse-Labs/.github
branch: feat/master-records-same-carrier-reconstruction-20260810
canonical_worker: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
canonical_issue: StegVerse-Labs/.github#60
role: CLAIMED_FOR_INTEGRATION
claim_created_at: 2026-08-10T20:53:00Z
claim_expires_at: 2026-08-11T20:53:00Z
claim_release_condition: bridge, worker integration and tests merge; direct runtime observation then remains machine-owned under #60/#59
```

## Canonical upstream

```text
master_records_merge: master-records/orchestration@71223e5ce89536b23178063bd1f407cd37ba636b
master_records_task: tasks/MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024.json
master_records_verifier: scripts/reconstruct_ecosystem_chat_sovereign_execution.py
master_records_handoff: ECOSYSTEM_CHAT_SOVEREIGN_RECONSTRUCTION_MIRROR_HANDOFF.md
model/runtime: StegVerse-002/micro-node-runtime / SOVEREIGN-LOCAL-MODEL-001
credential policy: StegVerse-Labs/TV
route authority: StegVerse-Labs/TVC
provider transport: StegVerse-org/LLM-adapter / LLMA-SOVEREIGN-CARRIER-EXECUTION-020
```

## Credential and authority boundary

```text
credential_requirement: NONE
credential_authority: StegVerse-Labs/TV+TVC
github_token_required: false
github_auth_forwarded_to_master_records_child: false
third_party_execution_platform_required: false
master_records_reconstruction_grants_execution_authority: false
master_records_reconstruction_grants_admissibility: false
authority_effect: NONE
```

The bridge may discover only an already-materialized local Master Records capsule. It must not use GitHub source checkout, a GitHub token, bearer token, hosted custody endpoint, Render, Vercel, Cloudflare, or hosted-provider credential to obtain or execute the reconstruction verifier.

## Required implementation

```text
workers/master_records_sovereign_reconstruction_bridge.py
workers/ecosystem_chat_sovereign_route_worker.py integration
tests/test_master_records_sovereign_reconstruction_bridge.py
control/process-worker-adapters.json generation update
.github/workflows/heartbeat-worker-project.yml validation inclusion
docs/HEARTBEAT_CONTINUITY_WORKER_MIRROR_HANDOFF.md integration state
```

## Execution contract

After `LLM_ADAPTER_SAME_ENDPOINT_EXECUTED`, the heartbeat worker must:

1. reuse an existing verified Master Records reconstruction receipt only when it binds the exact runtime proof, TVC route receipt, LLM execution session/transition/measurement and provider-usage event;
2. otherwise discover a locally materialized `master-records/orchestration` capsule containing the merged task, verifier and scoped handoff;
3. build a packet containing the exact runtime proof, TVC route receipt and LLM-adapter execution receipt;
4. strip GitHub authentication variables from the reconstruction child environment;
5. invoke `scripts/reconstruct_ecosystem_chat_sovereign_execution.py` locally;
6. require PASS with `provider_usage_reconstruction_pass=true`, `transition_reconstruction_pass=true`, `same_execution=true`, `credential_requirement=NONE`, `github_token_required=false`, `execution_authority=false`, and `authority_effect=NONE`;
7. persist the reconstruction receipt in `receipts/ecosystem-chat-sovereign-inference/`;
8. advance only to immutable zero-blocker activation verification, never directly to product activation.

## Collision boundaries

- no second heartbeat or scheduler;
- no duplicated model/runtime, TV/TVC, LLM-adapter, or Master Records authority;
- no GitHub token or source checkout in the production child path;
- no hosted custody endpoint as a prerequisite;
- no false success when local capsule, exact packet, or reconstruction evidence is absent;
- no execution/admissibility/publication/release authority from reconstruction.

## Validation

Use the existing `Heartbeat Worker Project` workflow. Add only compile/test coverage for the bridge and do not create a second workflow.

## Machine continuation and archive condition

After merge, direct same-carrier observation is machine-owned by `StegVerse-Labs/.github#60/#59`. This session is archive-safe only when this integration claim is merged/released or durably transferred and no unique chat-only requirement remains. Product activation remains a separate direct-evidence predicate.

## Completion accounting

```text
developed: 1/6
validation: 0/3
integration: 0/2
goal activation: 15%
session consolidation: 10/11
archive readiness: false
```
