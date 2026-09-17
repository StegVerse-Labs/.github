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

## Exact official source identifiers now bound

- BLS CES real hourly production/nonsupervisory earnings: `CES0500000032`.
- BLS CES real weekly production/nonsupervisory earnings: `CES0500000031`.
- BLS CPI-U U.S. city average all items, unadjusted: `CUUR0000SA0`.
- BEA NIPA monthly Table 2.6: dataset `NIPA`, table `T20600`:
  - line `27` disposable personal income;
  - line `29` personal consumption expenditures;
  - line `35` personal saving as percent of disposable personal income;
  - line `37` real disposable personal income.
- Board of Governors Household Debt Service Ratio series via FRED:
  - `TDSP` total;
  - `MDSP` mortgage;
  - `CDSP` consumer;
  - current-method comparable history begins in 2005 and remains distinct from the archived prior method.
- New York Fed Household Debt and Credit Q2 2026 release and exact official underlying-workbook URL are bound for debt balances and serious-delinquency transitions. Worksheet/column normalization remains explicitly pending rather than guessed.
- Census ACS 1-year detailed table `B25140` is bound with explicit variables for total occupied units, owner-with-mortgage, owner-without-mortgage, renters, and over-30/over-50-percent housing-cost burden. Standard-comparison year 2020 remains excluded.

## Acquisition and normalization state

The merged acquisition entrypoint now supports bounded source acquisition for BLS, BEA, Board/FRED, Census, and New York Fed source material.

- BLS, BEA, FRED, and Census normalizers have deterministic provider-shaped tests.
- raw bytes are hashed before candidate normalization.
- source vintage is retained.
- source failures remain fail-closed instead of becoming zeros.
- BEA requires `BEA_API_KEY`; absent credential fails only that source family and must be resolved through governed credential custody rather than embedded in source.
- New York Fed workbook bytes can be captured and hashed, but worksheet/column-level normalization remains `WORKBOOK_COLUMN_BINDING_PENDING` until exact source evidence is available.
- candidate outputs carry `finding_authority=false` and `public_activation_authorized=false`.

## Current canonical state

- task registry: ACTIVE / CLAIMED_INTEGRATION
- ERL inventory/schema/fixture/validators: MERGED
- Site page/fixture/validator/README: MERGED
- exact official source identifiers: MERGED / BOUND
- deterministic BLS/BEA/FRED/Census normalizers: MERGED / PASS
- New York Fed raw workbook binding: MERGED
- New York Fed workbook worksheet/column normalization: PENDING EXACT BINDING
- live source candidate acquisition: NOT YET RETAINED AS CANONICAL EVIDENCE
- cohort joins / required-cost composite: PENDING
- governed multi-source household-state generation: NOT YET IMPLEMENTED
- authentic ERL-to-Site live-output binding: NOT YET IMPLEMENTED
- current-iPhone Safari validation: PENDING
- served-body/public activation verification: NOT OBSERVED
- public activation: NOT CLAIMED

## Next work

Resolve the exact New York Fed workbook worksheet/column map from official retained evidence; execute bounded credential-free candidate acquisition for BLS, FRED, and Census with raw hashes/vintages; resolve BEA access through governed credential custody; construct the first multi-source household-state candidate while preserving household/distribution limits; then bind Site only to a governed ERL output with stale/invalid fail-closed behavior. Public activation remains separately gated on authentic fresh output and served-body verification.
