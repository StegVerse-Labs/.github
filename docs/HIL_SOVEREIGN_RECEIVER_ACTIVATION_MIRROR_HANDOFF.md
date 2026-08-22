# HIL Sovereign Receiver Activation Mirror Handoff

## Source of truth

```text
goal_id: SHWP-HIL-SOVEREIGN-RECEIVER-001
issue: StegVerse-Labs/.github#246
source_dependency: StegVerse-org/LLM-adapter@40eaa9af5cb7e3845ddaf4e79e02d299c76b9655
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_allowed: false
participant_machine_required: false
developer_machine_required: false
current_user_iphone_required: false
hb30_browser_capsule_required: false
third_party_runtime_required: false
execution_authority_from_transport: false
```

This lane exists to make the merged HIL v1.1 receiver executable on an existing StegVerse-controlled carrier without inheriting the historical CURRENT_USER_IPHONE/HB30 prerequisite from the broader sovereign-runtime recovery lane.

## Collision boundary

This task does not mutate or steal claims/fences from `SHWP-DURABLE-RUNTIME-ACTIVATION`, `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`, WorkerCoordinator, TV/TVC, or Master Records. It is a bounded capability launcher/probe for the already-merged LLM-adapter HIL receiver.

## Required source work

1. Discover an already-materialized local LLM-adapter tree containing the merged HIL receiver contract.
2. Build a credential-free child environment that marks the process as a `sovereign-carrier`, binds HIL state beneath a non-temporary durable StegVerse root, and permits only declared StegVerse browser origins.
3. Launch the existing `llm_adapter.combined_gateway:app` locally without granting route, publication, review, Master Records, or execution authority.
4. Probe `/api/hil/sovereign-receiver-profile` and `/api/hil/readiness` and fail closed unless the profile is `ACTIVE_SOVEREIGN_RECEIVER`, readiness is `READY`, exact HIL v1.1 Primary/prompt identities match, and all participant/developer/host dependency flags are false.
5. Emit non-authorizing machine-readable launcher/probe evidence for the carrier worker.

## Activation proof still required after source merge

Source implementation and CI do not activate HIL. Completion of #246 still requires a real StegVerse-controlled carrier observation, public HTTPS rendezvous reachable from `stegverse.org`, one real Site browser submission returning `HIL-RECEIVER-RECEIPT-v2`, post-restart/replacement exact-byte SHA-256 verification, and handoff into the existing TVC HIL lifecycle.

## Execution ownership

```text
manual_execution_allowed: false
source_implementation_lane: this branch / PR
runtime_execution_owner: admitted StegVerse carrier worker derived from #246
credential_route_authority: TV/TVC
review_publication_authority: existing TVC HIL lifecycle only
master_records_authority: master-records/orchestration
```

No third-party host or participant hardware may be substituted as production authority merely because live carrier evidence is not yet present.
