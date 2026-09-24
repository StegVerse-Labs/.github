# ERL Household Economic Conditions Site Mirror Handoff

## Canonical identity

- Goal Task ID: `ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001`
- coordination issue: `StegVerse-Labs/.github#2027`
- ERL implementation/research issue: `StegVerse-Labs/Executive_Rhetoric_Ledger#163`
- Site implementation issue: `StegVerse-Labs/Site#1368`
- canonical ERL household/economic-distribution source: `StegVerse-Labs/Executive_Rhetoric_Ledger/docs/ECONOMIC_DISTRIBUTION_MIRROR_HANDOFF.md`
- COSV task vector: not yet materialized
- coordination state: `ACTIVE`

## Goal

Create a real-time public U.S. household economic-conditions page that reports what current evidence supports about household economic condition rather than treating headline spending, GDP, gross real weekly earnings, or aggregate debt-service ratios as household welfare.

ERL remains evidence/analysis authority. Site remains presentation-only. Source acquisition and CI do not create findings or public activation authority.

## Household-state contract

The governed output preserves:

1. gross labor income;
2. net disposable / take-home resources;
3. household required-cost burden;
4. debt-service burden by debt class;
5. necessary consumption;
6. discretionary residual;
7. saving or dissaving;
8. new borrowing;
9. delinquency / arrears;
10. unmet or foregone consumption;
11. distribution by income/debt/wealth cohort where evidence permits.

Observed spending, gross real earnings, national output/productivity, and aggregate DSR remain contextual observations rather than household-welfare findings.

## Longitudinal graph contract

The Site graph supports `1Y`, `5Y`, `10Y`, `2000→Now`, and `Max`, subject to series-specific comparability.

- 2000 is a requested horizon, not a forced start.
- each series begins at its earliest defensible comparable observation;
- source vintage and revision semantics remain visible;
- methodology/coverage breaks remain visible;
- incompatible definitions are not silently spliced;
- same-axis absolute overlays require compatible units and definitions;
- cross-metric trajectories use selected-start normalized index mode;
- gaps remain gaps unless a governed historical reconstruction exists;
- proxies remain explicitly labeled.

## Completed implementation merges

### ERL PR #164

Merged with expected-head protection at `03aab5fe5eb75a1d8955d82d820bdd46be015316` from exact head `d47311c2cb7f33a7fa1c460d7756efab8f504ab3` after all returned exact-head workflows passed.

Implemented and merged:

- official series inventory;
- household economic-conditions output schema;
- fail-closed fixture;
- deterministic contract/fixture validator;
- CI binding;
- ERL README reconciliation;
- scoped ERL handoff.

Exact-head workflow evidence included `Validate Ledger Schemas` and `Validate Active Research Acquisition Consumer`, both `SUCCESS`.

### Site PR #1369

Merged with expected-head protection at `33c83de3ebc0ab36f35f4563e6b01263a9f9d2ff` from exact head `c68e88665875b7d34ccce9fbcaf3a954b6e69fed`.

Every workflow returned for that exact head completed `SUCCESS`, including Site Bootstrap Validate, Site Handoff Orchestrator, Ecosystem Heartbeat Orchestration, Node IndexedDB Schema Migration, persistent-card validation, no-third-party-runtime validation, StegSocials preparation, visual-transport validation, NVIDIA/Hugging Face publication validation, CFP ingestion, and ERL KV provider-proof projection.

Implemented and merged:

- `Household-Economic-Conditions.html`;
- fixture-only Site data contract;
- deterministic Site validator;
- exact Site work claim;
- Site README reconciliation;
- scoped Site handoff.

The page remains fail-closed on fixture data and is not publicly activated by source/CI/merge or branch-preview deployment.

### ERL PR #165

Merged with expected-head protection at `b0d51340238b798ba46b36ab13988f1255d43642` from exact head `555d9717e2046653af8ca61ece23617a919217f9`.

Exact-head validation:

- `Validate Household Economic Source Bindings` run `35167747226`: `SUCCESS`;
- `Validate Ledger Schemas` run `35167747146`: `SUCCESS`.

Implemented and merged:

- `research-data/household-economic-conditions/official-series-bindings.v1.json`;
- `scripts/acquire_household_economic_conditions.py`;
- `scripts/validate_household_economic_source_bindings.py`;
- `.github/workflows/validate-household-economic-source-bindings.yml`.

### ERL PR #166

Merged with expected-head protection at `3522e9d34399d6f45425af7ab11ea196b00b8012` from exact head `db1aaca276fd361904c73355783a04b3ff039d6b`.

Exact-head validation:

- `Validate Household Economic Source Bindings` run `35176879011`: `SUCCESS`;
- `Validate Ledger Schemas` run `35176878973`: `SUCCESS`;
- `Observe Household Economic Current Candidates` run `35176878974`: `SUCCESS`.

The final observation artifact is `household-economic-current-candidates`, artifact id `10479530174`, artifact digest `sha256:322b146d9cdcb9630b5691ee34cf87cd5fcca14b54bbe288fbfb3d4cdcda9a0b`.

Implemented and observed:

- bounded credential-free BLS, Federal Reserve Board DSR, Census ACS, and New York Fed candidate acquisition;
- raw source retention, SHA-256 capture, source-vintage capture, and fail-closed source handling;
- exact New York Fed Q2 2026 workbook map artifact `research-data/household-economic-conditions/nyfed-2026q2-workbook-map.v1.json`;
- exact-map New York Fed normalizer with deterministic header/layout tests and changed-layout fail-closed behavior;
- first partial multi-source household-state candidate with no finding authority and no public activation authority;
- hosted BEA credential check confirming only that `BEA_API_KEY` was absent in hosted validation and that no TV/TVC BEA registration evidence was observed there.

Authentic final artifact counts/hashes:

- BLS real hourly earnings: 19 observations; raw `sha256:c49b5e864658062a277df223db76f5bbe0e12c3a96d1f1dd3f17797570e36fd3`; acquired/source vintage `2026-09-17T03:06:33Z`.
- BLS real weekly earnings: 19 observations; raw `sha256:5dc821a95c4f80bb2cb81e09289e564d551430c84f04f6d012d819d9ac718b3b`; acquired/source vintage `2026-09-17T03:06:33Z`.
- BLS CPI-U: 19 observations; raw `sha256:6aed22b776270f00da879adcd34c65c590f35666db1ab1bf8947fa0e5000078d`; acquired/source vintage `2026-09-17T03:06:33Z`.
- Board DSR total/mortgage/consumer: 85 observations each from one retained Board release body; raw `sha256:4547f71acbea2fdde11e4a5e7061191afc19a79e2f984c61ddd0d3ad8c7ae6f5`; source vintage `Federal Reserve Board DSR release 2026-06-22`.
- Census ACS B25140: 10 observations; raw `sha256:b5f37f22d3c0ddf28350d8baf7e349a4e15c5c4981929b7717a756c77a63c880`; source vintage `2024 ACS 1-year Table-Based Summary File`.
- New York Fed debt-balance candidate: 658 normalized observations; raw workbook `sha256:ddfba16b87e187848ed591a1283f310188e7bdeebe5cf409b70a35b058d99237`; acquisition/source vintage `2026-09-17T03:06:34Z`.
- New York Fed serious-delinquency candidate: 654 normalized observations from the same retained workbook/hash; acquisition/source vintage `2026-09-17T03:06:34Z`.

Exact New York Fed Q2 2026 workbook map:

- debt balance: worksheet `Page 3 Data`; title `Total Debt Balance and Its Composition`; header row `4`; period column `A`; `B=Mortgage`, `C=HE Revolving` normalized as `HELOC`, `D=Auto Loan`, `E=Credit Card`, `F=Student Loan`, `G=Other`, `H=Total`; latest observed period `2026-Q2` at row `98`; unit `trillions of nominal dollars`.
- serious delinquency flow: worksheet `Page 14 Data`; title `New Seriously Delinquent* Balances by Loan Type `; definition `90 or more days delinquent`; header row `5`; period column `A`; `B=AUTO`, `C=CC`, `D=MORTGAGE`, `E=HELOC`, `F=STUDENT LOAN`, `G=OTHER`, `H=ALL`; latest observed period `2026-Q2` at row `99`; unit `percent`.

## Exact official source identifiers now bound

- BLS CES real hourly production/nonsupervisory earnings: `CES0500000032`.
- BLS CES real weekly production/nonsupervisory earnings: `CES0500000031`.
- BLS CPI-U U.S. city average all items, unadjusted: `CUUR0000SA0`.
- BEA NIPA monthly Table 2.6: dataset `NIPA`, table `T20600`:
  - line `27` disposable personal income;
  - line `29` personal consumption expenditures;
  - line `35` personal saving as percent of disposable personal income;
  - line `37` real disposable personal income.
- Board of Governors Household Debt Service Ratio current-method series: `TDSP` total, `MDSP` mortgage, and `CDSP` consumer; current-method comparable history begins in 2005 and remains distinct from the archived prior method.
- New York Fed Household Debt and Credit Q2 2026 release and official underlying workbook are exact-bound for debt balances and serious-delinquency transitions through the retained Q2 2026 workbook map above.
- Census ACS 1-year detailed table `B25140` is bound with explicit variables for total occupied units, owner-with-mortgage, owner-without-mortgage, renters, and over-30/over-50-percent housing-cost burden. Standard-comparison year 2020 remains excluded.

## Acquisition and normalization state

- BLS, BEA, Board/FRED-shaped, Census, and New York Fed exact-workbook normalizers have deterministic tests where source structure is admitted.
- raw bytes are hashed before candidate normalization; source vintage is retained; source failures remain fail-closed instead of becoming zeros.
- BEA remains credential-gated. Hosted validation observed no `BEA_API_KEY`; TV/TVC BEA credential registration/availability remains `UNKNOWN` because no authentic TV/TVC registration evidence was observed in this lane.
- candidate outputs carry `finding_authority=false` and `public_activation_authorized=false`.
- the first multi-source state candidate is explicitly `PARTIAL` and non-authorizing. It keeps `net_disposable_resources`, `required_cost_burden`, `necessary_consumption`, `discretionary_residual`, `saving_dissaving`, `new_borrowing`, `delinquency_arrears`, and `unmet_foregone_consumption` as `UNKNOWN` where the current candidate does not yet admit a governed household-state interpretation.

## Current canonical state

- task registry: ACTIVE / CLAIMED_INTEGRATION
- ERL inventory/schema/fixture/validators: MERGED
- Site page/fixture/validator/README: MERGED
- exact official source identifiers: MERGED / BOUND
- BLS/Board/Census credential-free candidate acquisition: AUTHENTIC OBSERVATION RETAINED IN ACTIONS ARTIFACT
- New York Fed Q2 2026 workbook hash/map/normalization: MERGED / EXACT-BOUND / AUTHENTIC OBSERVATION RETAINED
- BEA TV/TVC credential availability: UNKNOWN / NOT OBSERVED
- first multi-source household-state candidate: PARTIAL / NON-AUTHORIZING / RETAINED IN ACTIONS ARTIFACT
- cohort joins / complete required-cost composite: PENDING
- authentic governed ERL-to-Site live-output binding: NOT YET IMPLEMENTED
- current-iPhone Safari validation: PENDING
- served-body/public activation verification: NOT OBSERVED
- Site public activation: FALSE / NOT AUTHORIZED

## Next work

Inspect TV/TVC custody for authentic BEA credential registration without exposing credential values; if admissible, execute bounded BEA acquisition and retain hashes/vintages. Then determine which currently normalized New York Fed debt/delinquency observations can be admitted into the household-state contract without conflating debt stock with new borrowing or aggregate delinquency flow with distributional household stress; add distribution/cohort and required-cost evidence only where exact source support exists; keep unsupported fields `UNKNOWN`; and bind Site only to an authentic governed ERL output with stale/invalid fail-closed behavior. Public activation remains separately gated on authentic governed output and served-body verification.
## BEA resident-readiness re-observation — 2026-09-21

The existing TV/TVC BEA provider and non-exporting secret-ingress capabilities remain materialized through TVC #442 and stegfin-governance #110. The current session re-observed the authorized execution surfaces before any BEA request:

- connected resident execution devices visible to the available authorized execution connector: **0**;
- repository-retained authentic `stegverse.tvc.bea-credential-readiness/v1` receipt: **not observed**;
- credential value requested/read/returned/logged/hashed: **false**;
- BEA provider contacted: **false**;
- bounded BEA lease issued: **false**;
- BEA NIPA acquisition executed: **false**.

This does not prove credential absence. The runtime predicate remains `UNKNOWN / NOT OBSERVED`. Only an authentic retained readiness result with `decision=READY` may permit the already-existing bounded single-use BEA read-only lease for NIPA `T20600` lines `27/29/35/37`.

Household-state consequence: no BEA-derived DPI/PCE/saving-rate/real-DPI candidate was admitted in this observation. Unsupported net take-home resources, discretionary residual, complete required-cost burden, and unmet/foregone consumption remain `UNKNOWN`. Site public activation remains `FALSE / NOT AUTHORIZED` pending authentic governed ERL output plus served-body proof.
## Task Registry runtime correction — 2026-09-21

The global Task Registry runtime invariant was re-read before further BEA work. Connected-device inventory is prohibited from ordinary task progression and zero connected devices has no task-state meaning. The prior 2026-09-21 zero-device observation is therefore superseded as a gating fact; it remains provenance only.

The Goal Task is reconciled back to the canonical progression order: Task Registry -> Canonical Work/Interlock-InTr ingress -> fresh WorkerCoordinator claim/fence -> TV/TVC readiness/capability use when required -> Master Records custody/reconstruction -> Task Registry reconciliation. No external-device discovery is a prerequisite.

The authentic BEA predicate remains `stegverse.tvc.bea-credential-readiness/v1 decision=READY`. Source review also found existing-path BEA broker composition defects; TVC #451 and stegfin-governance #111 repair those seams without creating a new runtime or credential path. Until authentic READY is retained, no BEA lease/API call or BEA-derived household conclusion is permitted. Site public activation remains false.

## 2026-09-21 runtime/source merge reconciliation

The corrected runtime/source chain is now merged with exact-head protection:

- TVC #451 exact head `90825af302731a6182f1a760c16c110088796b90` -> merge `d7bbb9024ace0c1c41be35cda3269008139cae6f`; all returned exact-head workflows succeeded.
- stegfin-governance #111 exact head `13e67ab5b1364a536b5fcda1490337e34da8b16e` -> merge `a06ff7b6811128481bdc4b94f08f1a5540cc1c67`; all returned exact-head workflows succeeded.
- ERL #199 exact head `d7b7dc18a10a68e5babe04fec498acad401046f8` -> merge `0281a717e720d111b76898232985f8f357d1af33`; source-binding, schema, and public-source observation workflows succeeded.
- .github #2443 exact head `b39d932aeeab90942daf7914c7b1bb85829e8293` -> merge `c0b93e6c4ff88a038b6af32f45aae1afee34c3ba`; Cross-Task Coordination Validation succeeded.
- ERL #200 exact head `77c2a8955ebc176059265ddd0d4df367e4fa9979` -> merge `46bfe423472bc0b56072581bece0c8618f7e99eb`; Observe Household Economic Current Candidates run `35601531123` and Validate Ledger Schemas run `35601531110` both succeeded.

The live credential-free ACS B25140 observation on ERL #200 retained raw SHA-256 `b5f37f22d3c0ddf28350d8baf7e349a4e15c5c4981929b7717a756c77a63c880` and emitted 16 observations: 10 direct published counts plus 6 deterministic housing-cost-burden shares. Its admitted scope is `HOUSING_COST_BURDEN_ONLY`; the resulting household state remains `required_cost_burden=PARTIAL`, not a complete required-cost or welfare finding.

Canonical task state after source reconciliation remains `PROPOSED` with only `INGRESS_ADMITTED` as the next allowed transition. Source merges and CI do not establish authentic Canonical Work ingress, WorkerCoordinator claim/fence, resident BEA readiness, Master Records reconstruction, governed ERL live output, or Site served-body proof.

BEA remains `UNKNOWN / UNRESOLVED`: no authentic resident `stegverse.tvc.bea-credential-readiness/v1 decision=READY` has been retained in this continuation, so no BEA lease or BEA provider operation was executed. Unsupported household-state fields remain `UNKNOWN`, and Site public activation remains `false`.

The earlier “0 connected devices” observation is historical provenance only and is not a task-state fact, blocker, prerequisite, fallback condition, or runtime-substrate decision.

## COSV task pointer — 2026-09-21

The current source state is now encoded through the existing `task.v1` COSV contract as `10100000100000`: lifecycle `UNCLAIMED`, one unit of unassigned work, canonical owner installed, no chat-owned claim, zero blockers, evidence incomplete, not activated, and not propagated. The exact source record is `control/task-vectors/ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001.json` and is indexed in `control/task-vector-index.json`.

This is a non-authorizing compact pointer only. It does not mint a WorkerCoordinator claim/fence, establish Interlock/InTr admission, prove resident execution, resolve BEA readiness, or authorize Site publication.

## COSV + standing carrier binding — 2026-09-21

The exact Goal now has a canonical non-authorizing `task.v1` pointer and is addressable by the already-existing standing resident carrier:

- .github #2541 exact head `830819aa37db34ba1b1d26800d3c747103813b83` passed both Cross-Task Coordination Validation and Deterministic Repository Suite, then merged with expected-head protection as `f7043dfbc05455677b55b2ade18b4461dd048240`.
- COSV: `10100000100000`; source: `control/task-vectors/ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001.json`; indexed in `control/task-vector-index.json`.
- StegVerse-Healer #100 exact head `ed7d691d0ac346695f29283a09bd286beb671c93` passed Test Readiness run `35675227970`, then merged with expected-head protection as `4b219f0acd207cbadaeaa7b040ab305bc5f6d68b`.
- The Healer schedule now binds the exact Goal/COSV to `RT-CANONICAL-WORK-PORTABLE-DISPATCH-001` using the existing `RT-REUSABLE-TASK-SCHEDULER-001`, exact invocation key, `only_consumer=canonical_work_coordination`, hourly slots, 15-minute retry, and maximum four attempts per slot.

No new scheduler, runtime, dispatcher, request plane, credential path, device dependency, or authority plane was introduced.

Current authentic boundary remains unchanged: no retained resident child trigger/dispatch receipt for this exact Goal, no Task Registry `CONTINUE`/Interlock-InTr ingress, no fresh WorkerCoordinator claim/fence, no ERL household worker receipt, and no Master Records reconstruction for this invocation were observed in repository-accessible evidence after the source/carrier merges. Their absence is not converted into a runtime-failure claim.

BEA therefore remains `UNKNOWN / UNRESOLVED`; the single-use BEA operation was not executed. Site public activation remains `false`.

## September 24 exact-goal dispatch source-order repair

Current-main continuation of the existing Canonical Work consumer gives an explicit `--goal-task-id ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001` priority over the unrelated MIR-first subprocess without changing unscoped or other-goal scheduling. The unchanged owner is the existing `canonical_work_coordination` selector. This fixes a source-order hazard (unrelated 1200-second preemption), not an observed live failed transition. Exact task consumption, Interlock/InTr outcome, WorkerCoordinator claim/fence, Master Records reconstruction, and subsequent Publisher/Site served-body verification are still required. No new execution or credential route; BEA remains UNKNOWN absent authentic READY; activation remains false.
