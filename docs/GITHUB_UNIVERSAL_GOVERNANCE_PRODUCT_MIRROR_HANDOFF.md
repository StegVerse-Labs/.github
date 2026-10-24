# GitHub Universal Governance Product Mirror Handoff (DRAFT, proposed for admission)

Status: **DRAFT, PROPOSED.** Not Registry-admitted. Prepared read-only by Grok Bot Lane C (GitHub Product) on 2026-10-18 for the Registry owner (decision D7). This doc does not register anything. A PR that adds it must not touch `data/canonical-task-registry.json`.
Proposed path: `StegVerse-Labs/.github:docs/GITHUB_UNIVERSAL_GOVERNANCE_PRODUCT_MIRROR_HANDOFF.md`
Proposed canonical record: `data/canonical-task-records/GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001.json` (draft: `hd7_canonical_task_record_GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001.json`)
Coordination: `StegVerse-org/.github#164` (lane `P2-commercial-governance`). Parents: `StegVerse-org/.github#160` (coordination) and `StegVerse-Labs/.github#3183` (product/revenue), both under INDEX H14. Proposal: `StegVerse-Labs/.github#3012`.

## Owning canonical task (proposed)

| Field | Value |
|---|---|
| Goal Task ID | `GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001` (absent from the Registry at generation 319) |
| COSV | `10610000116000` (proposed; derivation and alternatives are in the record) |
| Coordination state | `PROPOSED` / `UNCLAIMED` |
| Parent task | `null` by default (59 of 118 rows have none). Alternative: `ECOSYSTEM-ECONOMIC-WHITEPAPER-GATED-ROADMAP-001`. The owner decides. |
| Registry observed | `StegVerse-Labs/.github` main `bfcf0318`, generation **319**, blob `8d3ff190` |
| Admission rule | One registry-only PR at **live main generation + 1** (320 if main is still at 319). The Labs#3220 fence (`f16b9153`) fails anything else closed with `REGISTRY_GENERATION_NOT_TIP_PLUS_ONE`. Owner-only merge. |

COSV is a state vector, not an identifier: 14 vectors are shared by several rows at generation 319. Vector uniqueness is therefore not an admission predicate; `task_id` uniqueness is. `10610000116000` does not occur in the registry or in `control/task-vector-index.json`.

## Product claim (narrow)

The only product claim: **a verifiable receipt chain built on customer-supplied manifest constraints.** Nothing else is claimed: no safety, compliance, certification, legal, authority or runtime claim. A release, CI run or source merge does not mint runtime ALLOW, an entitlement or a price.

## Surfaces and owners

| Surface | Repository / path | Owning task | State (2026-10-18) |
|---|---|---|---|
| Governance gate and reusable workflow | `StegVerse-org/StegVerse-SDK`: `stegverse/governance_gate.py`, `.github/workflows/governance-gate.yml` | `SDK-STRUCTURAL-VALIDATOR-CONSOLIDATION-001` | main `291ad15b` still runs the pre-#534 gate (`PASS`; empty glob passes). #534 (head `3dd6c80b`, draft) brings `ALLOW`/`FAIL_CLOSED`, the six fields, empty glob `FAIL_CLOSED` and SHA-pinned actions. |
| Structural validator contract | `stegverse/structural_validator_candidate.py` | same | contract 1.7 merged (#542, 02:59:17Z). Schema classification is informational and never changes the disposition. |
| Release notes | `RELEASE_NOTES_1.3.0.md` | same | #535 (head `14b0ecc6`) records contract 1.7 |
| Tier pricing and cost registry | `stegverse/tier_pricing.py`, `stegverse/cost_registry.py`, `pricing/` | `SDK-COST-DERIVED-TIER-PRICING-001` | ACTIVE/UNCLAIMED; `PROVISIONAL_SCENARIO_ONLY`; `final_price_approved: false`. Source ownership of `tier_pricing.py` is FAIL_CLOSED pending Claude/owner. |
| Commercial catalog, payment and entitlement records | `Infrastructure-Continuity-Ventures/.github`: `commercial/` | none admitted (ICV owner) | Payment provider `PAYMENT_PROVIDER_NOT_DECIDED` (owner). Lane C H-E draft (negative cases plus a validator repair) prepared, not opened. |
| Release identity and credentials | `StegVerse-Labs/TVC` | `TVC-SDK-1.3.0-CREDENTIAL-AUTHORIZATION-001` (TVC-local; absent from the Labs registry) | `v1.3.0` absent; warrant binds `b1376d3e`, which lacks the gate |

## Dependencies

1. **SDK #534 and the pin follow-up.** #534 merges at its exact head (owner). A follow-up PR then retargets `uses:` and the `sdk_ref` default to #534's merge commit. `ba5bbf42` is the pre-#534 workflow and checker.
2. **Q1, v1.3.0 tag / release ref (owner + TV/TVC).** Fail-closed default: callers stay on a commit-SHA pin, no tag claims the gate, `v1.3.0` is left untouched, and the product is not announced as a tagged release.
3. **Q3, license (Rigel).** Default: the existing MIT `LICENSE` stays unchanged, with no new or commercial terms and no licence claims beyond that file.
4. **Q4, pricing (Rigel).** Default: no paid tier, price or entitlement is offered; only the FREE limits (25 bundles / 200 schemas) apply. Any paid request is `FAIL_CLOSED` pending the owner. Pricing stays `PROVISIONAL_SCENARIO_ONLY`.
5. **Payment provider (owner).** `FAIL_CLOSED PAYMENT_PROVIDER_NOT_DECIDED`. `PAYMENT-PROVIDER-AUTHENTIC-INGRESS-001` is present (ACTIVE) but does not decide the provider.
6. **D7 Registry admission and D8 parent (Registry owner).**

## Acceptance predicates (proposed)

- `PRODUCT_CLAIM_LIMITED_TO_VERIFIABLE_RECEIPT_CHAIN_ON_CUSTOMER_SUPPLIED_MANIFEST_CONSTRAINTS`
- `PACKAGE_VERSION_IDENTITY_CONSISTENT_ACROSS_PYPROJECT_INIT_VERSION_JSON`
- `REUSABLE_GOVERNANCE_GATE_PINNED_TO_IMMUTABLE_TV_TVC_PUBLISHED_REF` (or a full commit SHA whose tree contains the #534 checker)
- `PINNED_REF_TREE_CONTAINS_GOVERNANCE_GATE_WORKFLOW_AND_MODULE`
- `NON_ALLOW_PRODUCES_NO_EFFECT_IN_CUSTOMER_CONFORMANCE_RUN`: valid bundle gives ALLOW; tampered, over-limit or empty glob gives FAIL_CLOSED with the six fields; the job is green only on ALLOW
- `NO_NEW_RUNTIME_DEPENDENCY_INTRODUCED` (dependency count at or below `ba5bbf42`; #539 removed black, mypy and pytest-cov)
- `ROUTE_SHA256_PRESERVED_ACROSS_CLASSIFIER_ALIAS_MIGRATION` (#536)
- `LICENSE_AND_TERMS_OWNER_APPROVED`, `TIER_PRICING_OWNER_APPROVED_AND_ENTITLEMENT_SEPARATE_FROM_DISPOSITION`, `PAYMENT_PROVIDER_OWNER_DECIDED`
- `ROLLBACK_PROCEDURE_DOCUMENTED_WITHOUT_TAG_RETARGET`
- `IMMUTABLE_TAG_AND_GITHUB_RELEASE_PUBLISHED_UNDER_TV_TVC_AUTHORITY`
- `ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK:GOVERNANCE_PRODUCT_RELEASE` (completion is claimed only from TV/TVC provenance plus an Organization receipt read back)

## Current disposition

`FAIL_CLOSED`
- `failure_code`: `PARENT_GOAL_NOT_REGISTRY_ADMITTED`
- `failed_predicate`: `GITHUB_UNIVERSAL_GOVERNANCE_PRODUCT_001_IN_REGISTRY_WITH_HANDOFF`
- `required_evidence_or_repair`: the Registry owner admits the goal (proposed COSV `10610000116000`) in one registry-only PR at live main generation + 1, with the canonical record and this handoff
- `retry_entrypoint`: `StegVerse-Labs/.github#3012`; owner decision D7
- `owning_existing_goal`: `GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001` (PROPOSED)
- `next_attempt`: after D7. This handoff may land first as a docs-only draft.

Other open records, each owned elsewhere: `PAYMENT_PROVIDER_NOT_DECIDED` (owner), `SOURCE_FILE_OWNERSHIP_UNRESOLVED` for `tier_pricing.py` (Claude/owner), Q1/Q3/Q4 (owner, TV/TVC).

## Authority separation

Task Registry: coordination only. WorkerCoordinator: claims and fences (none asserted). Interlock/InTr: governed transitions. TV/TVC: credentials, release, entitlements. Organization ledger: observed reality. Master Records: reconstruction. ICV: commercial packaging and distribution. StegOps: CRM projection only. GitHub runtime authority: NONE. The owner merges. A paid tier can never manufacture ALLOW.

## Not claimed

No Registry admission, WorkerCoordinator claim, release, tag, entitlement, price, payment, revenue or runtime ALLOW. Nothing here was observed at runtime. Anything Lane C did not observe is marked `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` in the record.
