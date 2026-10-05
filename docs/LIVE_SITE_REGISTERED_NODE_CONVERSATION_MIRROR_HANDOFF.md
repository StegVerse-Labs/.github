# Live Site Registered-Node Conversation Mirror Handoff

Updated: 2026-10-05
Goal Task ID: `LIVE-SITE-REGISTERED-NODE-CONVERSATION-001`
Parent Goal Task ID: `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`
COSV ID: `50000000100000`
Repository: `StegVerse-Labs/.github`
Status: `ACTIVE`

## Goal

Restore the intended Site runtime ownership boundary and then reconcile the exact public `stegverse.org` bytes used by registered-Node Ecosystem Chat.

Acceptance prompt: `What is the SDK?`

## Demonstrated architectural defect

`assets/ecosystem-chat-va-runtime.js` was created as the VA/VACC specialization in commit `9ed2dbfe8560618be41225b47b37e19c31bc7d0d`. Commit `f43190e4108f5c881f1c64d3e17505090e33d9ca` then promoted general/shared runtime behavior into that VA-owned file and aliased the same object as both `window.EcosystemRuntime` and `window.EcosystemVARuntime`. Later Math, weather/Node status, deterministic product definitions and SDK lifecycle behavior accumulated on the same mixed owner.

That responsibility inversion is a demonstrated source defect. It is distinct from the still-separate public deployment/runtime observation question.

## Corrected ownership contract

- shared runtime owner: `StegVerse-Labs/Site/assets/ecosystem-chat-runtime.js`
- VA/VACC specialization owner: `StegVerse-Labs/Site/assets/ecosystem-chat-va-runtime.js`
- browser composition/router: `StegVerse-Labs/Site/assets/ecosystem-chat-simple.js`

The shared runtime owns the device-local bridge, general conversation, deterministic homepage/product definitions, Math, weather/Node-status capabilities and SDK lifecycle access. It is the sole owner of `window.EcosystemRuntime`.

The VA specialization owns VA intent detection, VA history/grounding, VA projection state and VA-specific server/device invocation. It is the sole owner of `window.EcosystemVARuntime` and consumes the shared runtime's bounded device-execution primitive when VA needs device-local inference.

VA projection initialization is lazy. Canonical product-definition discovery is evaluated by the shared runtime before VA intent evaluation. Therefore `What is the SDK?` does not initialize or enter VA routing.

## Bounded repair

Update Site load order to shared runtime -> VA specialization -> composition/router; preserve all external StegVerse Node, Receipt #1, StegOS, local-model bridge protocol, LLM-adapter, SDK ingress, Interlock/InTr, device topology, hosting and authority contracts. Add regression tests that reject a shared/VA alias, reject shared capabilities inside the VA file, prove the SDK acceptance prompt short-circuits VA routing, and prove an explicit VA prompt enters the VA specialization.

After source validation/merge, compare the deployed homepage, shared runtime, VA specialization and simple-router bytes with canonical Site main. Public byte equality proves propagation only. Authentic registered-Node execution is complete only when the existing Node observation path retains the deterministic `What is the SDK?` invocation/result evidence.

## Current transition

Site PR #1500 merged as `565cd816f7d8799a1cde9d968562c23fb3f23a53` from exact validated head `6dfffc8355930b56332991e9606be305ab06fb5f`.

Exact-head validation on the PR passed all task-relevant repository requirements, including Site Homepage Chat, Site Node Continuity, Site Handoff Orchestrator, Site Bootstrap Validate, Ecosystem Heartbeat Orchestration, No Required Third-Party Runtime, and the split-runtime public-asset observer validation.

Post-merge main validation also passed for the same runtime surfaces. Public observation run `37385542714` completed successfully after the merge and emitted `SITE_HOMEPAGE_CHAT_PUBLIC_ASSET_OBSERVATION_PASS`. Its retained artifact is `site-homepage-chat-public-assets-37385542714` / artifact ID `11378940616`. That observer compared the deployed homepage, shared runtime, VA specialization, simple router, and Node continuity bytes against canonical Site main and enforced the shared/VA ownership markers.

Therefore these predicates are now satisfied by retained source/CI/public-deployment evidence:
- `SHARED_AND_VA_RUNTIME_OWNERSHIP_SEPARATED`
- `WHAT_IS_THE_SDK_DOES_NOT_INITIALIZE_OR_ENTER_VA_ROUTING`
- `VA_PROMPT_ENTERS_VA_SPECIALIZATION_ONLY`
- `PUBLIC_HOMEPAGE_LOADS_EXACT_CANONICAL_CHAT_ASSET_IDENTITIES`

The remaining predicate is `REGISTERED_NODE_DETERMINISTIC_OBSERVATION_RETAINED`. Public-byte observation is not substituted for that browser-local Receipt #1-bound execution evidence. No alternate runtime, endpoint, device, credential, authority plane or transport path was introduced.
