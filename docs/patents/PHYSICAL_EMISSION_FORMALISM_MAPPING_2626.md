# Physical-Emission Provenance: Formalism Interface Mapping (Research Draft)

Parent: #2626. Status: proposed mapping, not certified, patent filing, or theorem proof.

## Boundaries
Independent technical paths: A acquisition/attestation; B replay/reconstruction of existing evidence; C comparison of independent presentations. No governance, canonical store, identified emitter, particular sensor, or external machine is a prerequisite to A/B/C. A governed projection is an optional downstream consumer, not the original evidence.

## Formalism mapping
| Technical artifact | Formal owner/interface | Mapping rule | Failure posture |
|---|---|---|---|
| Observed physical frequency composition | acquisition evidence -> RTG input | record actual sensed characteristics, uncertainty, sensor capability, environment and calibration; unknown emitter is permitted | mark attribution UNKNOWN, do not invent source |
| Adjacent observed snapshots | RTG transition geometry, AE resolution | N snapshots produce N-1 adjacent transitions; do not merge consequential distinctions without proof | retain gaps/under-resolution |
| Device, system and HB clocks | RTG evidence coordinates | retain identities, offsets, drift, ordering, uncertainty and HB relationships separately | inconsistent clock evidence remains visible |
| Start/finish commitments, receipt hash set | independent mechanism; STCM optional governed closure | canonicalized finite commitments and transition receipt lineage; hashes verify commitment integrity, not external truth | original chain fails verification if a required receipt is absent |
| Degraded reconstruction | independently receipted derived artifact | retain source references, inferred intervals, method, uncertainty and distinct identity | never claim original-chain completeness |
| Origin assertion | GTG scope/standing, TT allocation (optional) | distinguish emitter origin from recorder/acquisition provenance | DENY assertion only; preserve recording |
| Governed decision | GTG RTG_INPUT -> GTG TT_OUTPUT -> TT | keep GTG scope exclusions and dispositions; TT does not execute on ALLOW alone | DENY/DEFER/FAIL_CLOSED are receipt-bearing successor results |
| Temporal commit standing | STCM moment-bound validity, IICT candidate | revalidate at applicable commit boundary; do not infer universal IICT convergence | UNKNOWN/FAIL_CLOSED where required standing unavailable |

## Candidate technical invariants (not proven)
I1: Every original adjacent-pair transition has one stable index and its two referenced observations.
I2: An original evidence hash validates integrity only relative to authenticated commitment inputs and canonicalization.
I3: A derived projection never inherits the original artifact identity or fills missing originals silently.
I4: Unknown physical emitter origin does not negate authentic recorder/acquisition evidence.
I5: Governance disposition does not retroactively alter the original evidence commitment.
I6: Clock conflict is evidence of inconsistency, not a license to overwrite timestamps.

## Deterministic fixture matrix
| ID | Inputs | Expected technical result | Expected governance result |
|---|---|---|---|
| PE-01 | 3 genuine snapshots, two adjacent receipts, valid start/finish | 2 transitions, intact chain | no governance prerequisite |
| PE-02 | authentic recording, emitter unknown, human claims named emitter | recording verifiable; origin unverified | DENY unsupported attribution only |
| PE-03 | device time conflicts with system/HB, all preserved | intact chain with temporal uncertainty | no fabricated clock agreement |
| PE-04 | required middle original receipt missing | original chain verification fails | separate degraded projection possible with new receipt |
| PE-05 | valid capture, policy disallows publication | original capture integrity unchanged | DENY publication, receipt decision |
| PE-06 | reconstruction interpolates missing interval | separately identified derived artifact with gap and method | cannot assert original completeness |
| PE-07 | two recordings share common derivative ancestor | comparison possible | independence claim not established |
| PE-08 | GTG ALLOW without independent execution authority | evidence unchanged | no execution permitted from GTG alone |

## Proof obligations and falsifiers
- Formalize actual observation vs emitter attribution in RTG observation invariant; existing source_known language must not silently collapse the two.
- Define canonical byte serialization and cryptographic algorithms for bounded embodiments; demonstrate altered/missing receipt detection.
- Verify clock/HB cross-reference semantics under drift and unsynchronized cases without asserting absolute time truth.
- Show mapping compatibility with GTG RTG_INPUT_CONTRACT and TT_OUTPUT_CONTRACT; no authority inflation.
- STCM closure applies to governed transitions; do not impose it on independent physical acquisition.
- IICT convergence and STCM mathematical candidates remain unproven. Distinguish formal deductions from test evidence.
- Positive/negative fixtures above are specifications only until executable tests and independently verified results exist.

## Sources
- Admissible-Existence/AE docs/ADMISSIBLE_RESOLUTION_FUNCTION.md
- Admissible-Existence/RTG docs/invariants.md
- Admissible-Existence/GTG contracts/RTG_INPUT_CONTRACT.md and contracts/TT_OUTPUT_CONTRACT.md
- Admissible-Existence/TT docs/FORMALISM_COORDINATION_AUTHORITY.md
- Admissible-Existence/STCM docs/MATHEMATICAL_NOTATION.md and docs/FALSIFICATION_AND_LIMITS.md
- Admissible-Existence/IICT README.md

## Next action
Turn PE-01..PE-08 into deterministic executable tests; validate against exact source contracts and update this document with actual test receipts. Then map supported technical elements to claim paths A/B/C with patent counsel; avoid claiming abstract mathematics alone.
