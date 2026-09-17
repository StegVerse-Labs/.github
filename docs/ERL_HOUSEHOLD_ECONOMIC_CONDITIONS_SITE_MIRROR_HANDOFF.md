# ERL Household Economic Conditions Site Mirror Handoff

## Canonical identity

- Goal Task ID: `ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001`
- coordination issue: `StegVerse-Labs/.github#2027`
- ERL implementation/research issue: `StegVerse-Labs/Executive_Rhetoric_Ledger#163`
- Site implementation issue: `StegVerse-Labs/Site#1368`
- canonical ERL household/economic-distribution source: `StegVerse-Labs/Executive_Rhetoric_Ledger/docs/ECONOMIC_DISTRIBUTION_MIRROR_HANDOFF.md`
- COSV task vector: not yet materialized
- coordination state: `ACTIVE`

## Goal and authority boundary

Create a real-time public U.S. household economic-conditions page that reports only what current evidence supports about household condition rather than treating headline spending, GDP, gross real weekly earnings, or aggregate debt-service ratios as household welfare.

ERL remains evidence/analysis authority. Site remains presentation-only. Source acquisition, normalization, CI, GitHub merge, and retained artifacts do not create findings or public activation authority.

The household-state contract preserves gross labor income, net disposable/take-home resources, required-cost burden, debt service by class, necessary consumption, discretionary residual, saving/dissaving, new borrowing, delinquency/arrears, unmet/foregone consumption, and distribution/cohort evidence where support exists.

## Longitudinal graph contract

The Site graph supports `1Y`, `5Y`, `10Y`, `2000→Now`, and `Max` subject to series-specific comparability. 2000 is a requested horizon, not a forced start. Methodology breaks remain visible; incompatible definitions are not silently spliced; same-axis absolute overlays require compatible units/definitions; cross-metric comparisons use selected-start normalized-index mode; unsupported history remains missing.

## Completed implementation

### ERL #164 / Site #1369

ERL #164 merged at `03aab5fe5eb75a1d8955d82d820bdd46be015316`; Site #1369 merged at `33c83de3ebc0ab36f35f4563e6b01263a9f9d2ff`. These established the official-series inventory, household-state schema, fail-closed fixture/validators, Site page shell, longitudinal controls, normalized-index mode, README reconciliation, and fail-closed Site behavior. Site public activation was not authorized.

### ERL #165

Merged at `b0d51340238b798ba46b36ab13988f1255d43642`. Bound exact BLS, BEA, Federal Reserve/Board, New York Fed, and Census identifiers and installed deterministic source acquisition/normalization entry points. BEA remained credential-gated.

### ERL #166

Merged with expected-head protection at `3522e9d34399d6f45425af7ab11ea196b00b8012` from exact head `db1aaca276fd361904c73355783a04b3ff039d6b`. Exact-head workflows `Validate Household Economic Source Bindings` (`35176879011`), `Validate Ledger Schemas` (`35176878973`), and `Observe Household Economic Current Candidates` (`35176878974`) all completed `SUCCESS`.

Retained artifact `10479530174`, digest `sha256:322b146d9cdcb9630b5691ee34cf87cd5fcca14b54bbe288fbfb3d4cdcda9a0b`, preserved current BLS/Board/Census/New York Fed raw hashes, vintages, normalized observations, exact New York Fed Q2 2026 class-level workbook map, and a first `PARTIAL` non-authorizing household-state candidate.

Exact Q2 2026 New York Fed class map remains:

- debt balance: `Page 3 Data`, header row 4, period column A, Mortgage/HELOC/Auto/Credit Card/Student Loan/Other/Total, latest `2026-Q2` row 98;
- serious delinquency: `Page 14 Data`, header row 5, period column A, Auto/Credit Card/Mortgage/HELOC/Student Loan/Other/ALL, latest `2026-Q2` row 99;
- retained workbook SHA-256: `ddfba16b87e187848ed591a1283f310188e7bdeebe5cf409b70a35b058d99237`.

### ERL #167

Merged with expected-head protection at `f709b4f032f0efbe5880a4f6dde36454930ce8f1` from exact head `c2a890f322c02eb3125dfead1075f69144af77e9` after all returned exact-head workflows completed `SUCCESS`: `Observe Household Economic Current Candidates` run `35180743927`, `Validate Household Economic Source Bindings` run `35180743993`, and `Validate Ledger Schemas` run `35180743933`.

Retained artifact `10480580791`, digest `sha256:4715836f90f3d9fea4af9c4876f5b738c6261ee46fb0bb909f54509e9f00705e`, adds exact-bound age distribution context while preserving the same source-authority boundary.

New exact New York Fed distribution map:

- total debt balance by age: `Page 20 Data`, header row 4, period column A, age columns `18-29`, `30-39`, `40-49`, `50-59`, `60-69`, `70+`, latest `2026-Q2` row 114, unit trillions of nominal dollars;
- transition into serious delinquency (90+) by age: `Page 24 Data`, header row 3, period column A, age columns `18-29`, `30-39`, `40-49`, `50-59`, `60-69`, `70+`, plus `all`, latest `2026-Q2` row 109, unit percent, four-quarter moving sum.

The Q2 2026 age-distributed serious-delinquency context in the retained artifact is: `18-29=4.0431%`, `30-39=2.8574%`, `40-49=2.5276%`, `50-59=2.6042%`, `60-69=1.7447%`, `70+=1.7967%`. These are admitted only as age-distribution context; they do not establish income/wealth distribution or complete household stress.

ACS 2024 housing-cost burden is now admitted as `PARTIAL` required-cost evidence by tenure. It remains only a housing component and cannot be promoted to total required household costs. Food, medical, insurance, transportation, utilities, taxes, and other mandatory costs remain unresolved until separately evidenced.

`new_borrowing` remains `UNKNOWN`: New York Fed debt balances, including age-distributed debt balances, are debt stock and are not relabeled as borrowing flow. `delinquency_arrears` is now `PARTIAL` only because exact age-distributed serious-delinquency transition evidence exists; it is not promoted to a complete household-stress or arrears finding.

## BEA / TV-TVC custody inspection

The canonical TVC provider credential binding task `TVC-PROVIDER-CREDENTIAL-BINDING-011` covers OpenAI, Anthropic, DeepSeek, and Kimi only. It requires TV/TVC-only custody, prohibits raw-secret export, and does not contain BEA registration.

The current `StegVerse-Labs/TVC/config/provider_operation_profiles.json` has admitted profiles for 0x, OpenAI, Anthropic, DeepSeek, Kimi, Z.ai, MIR, Gmail, Google Drive, App Store Connect, Facebook, LinkedIn, and Instagram. It has no BEA profile and no `BEA_API_KEY` secret reference. Repository search found no BEA registration artifact in TVC.

Therefore BEA execution is not currently admissible through the existing TV/TVC broker: `BEA TV/TVC credential availability = UNKNOWN`, with the stronger structural observation `BEA provider profile/registration = NOT MATERIALIZED`. No credential value was requested, exposed, interpolated, or embedded.

## Current canonical state

- task registry: `ACTIVE / CLAIMED_INTEGRATION`;
- ERL inventory/schema/fixture/validators: merged;
- Site page/fixture/validator/README: merged;
- exact official source identifiers: merged/bound;
- BLS/Board/Census credential-free current acquisition: authentic evidence retained;
- New York Fed class-level and age-distribution workbook maps: exact-bound and retained;
- required-cost burden: `PARTIAL` / ACS housing only;
- delinquency/arrears: `PARTIAL` / age-distributed 90+ transition context only;
- new borrowing: `UNKNOWN`;
- net disposable/take-home resources: `UNKNOWN`;
- necessary consumption: `UNKNOWN`;
- discretionary residual: `UNKNOWN`;
- saving/dissaving: `UNKNOWN`;
- unmet/foregone consumption: `UNKNOWN`;
- BEA TV/TVC credential availability: `UNKNOWN`;
- BEA TV/TVC provider profile: not materialized;
- authentic governed ERL-to-Site live-output binding: not yet implemented;
- current-iPhone Safari validation: pending;
- served-body/public activation verification: not observed;
- Site public activation: `FALSE / NOT AUTHORIZED`.

## Next work

Materialize a bounded read-only BEA TV/TVC provider profile/credential-registration path without exposing credential values, then execute BEA only when authentic resident custody is admissible. In parallel, continue exact official required-cost and distribution/cohort evidence acquisition, including household cost components and debt-class/cohort surfaces, while preserving unsupported household-state fields as `UNKNOWN`. Construct an authentic governed ERL output only after evidence admission rules are satisfied; bind Site to that governed output with stale/invalid fail-closed behavior; public activation remains separately gated on served-body proof.
