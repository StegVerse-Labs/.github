# Live Site Registered-Node Conversation Mirror Handoff

Updated: 2026-10-05
Goal Task ID: `LIVE-SITE-REGISTERED-NODE-CONVERSATION-001`
Parent Goal Task ID: `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`
COSV ID: `50000000100000`
Repository: `StegVerse-Labs/.github`
Status: `ACTIVE`

## Goal

Trace the public stegverse.org Send action through the exact registered-Node conversation path and reconcile the bytes actually served for the homepage, `assets/ecosystem-chat-va-runtime.js`, and `assets/ecosystem-chat-simple.js` with current canonical `StegVerse-Labs/Site` source.

Acceptance prompt: `What is the SDK?`

Current canonical Site source resolves that prompt through `canonicalProductDefinitionCapability()` before `executeDeviceRaw()`. The deterministic SDK definition must not depend on local-model readiness.

## Demonstrated observation gap

The existing public asset observer covers `assets/stegverse-node-continuity-impl.js` and `assets/ecosystem-chat-simple.js`, but not the homepage asset references or `assets/ecosystem-chat-va-runtime.js`, which contains the exact `canonical_product_definition_sdk` decision path. Existing propagation evidence therefore cannot establish that the live page loaded the runtime bytes required by this acceptance prompt.

The homepage references both conversation scripts without an explicit version identity while other critical browser assets already use version query strings. The current HTML contract therefore does not bind one identifiable conversation-runtime release.

## Bounded repair

Repair only the Site asset-identity boundary: bind the two conversation scripts in the homepage to one explicit release identity; extend the existing public asset observer to verify the homepage references and exact deployed runtime/simple bytes; require the runtime marker `canonical_product_definition_sdk` and ordering before `executeDeviceRaw`; preserve node registration, LLM-adapter, SDK ingress, transport, device topology, hosting architecture, and authority boundaries unchanged.

## Evidence rule

Source/CI proves deterministic routing and observer correctness only. Public observation separately proves deployed homepage/script bytes. Registered-Node execution is complete only when the existing Node observation path retains the deterministic invocation/result evidence for the acceptance prompt.

## Next transition

Create the bounded Site repair, validate exact-head tests, then run the existing public observer after merge. If deployed bytes match canonical main, invoke the acceptance prompt on the registered Node and retain its existing exportable observation. If they do not match, the first mismatched asset identity is the actionable non-ALLOW boundary.
