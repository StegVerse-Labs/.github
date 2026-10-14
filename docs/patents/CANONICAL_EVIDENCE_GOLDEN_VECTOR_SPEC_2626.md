# Patent provenance: canonical evidence wire format and deterministic golden vectors (draft)

Parent: #2626; existing PR #3185. This is a **proposed embodiment**, not an accepted interoperability standard, certified implementation, patent filing or proof of novelty.

## Serialization contract (version PEP/0.1)
All byte commitments in this draft use UTF-8 JSON, lexicographically sorted object keys, no insignificant whitespace, ASCII-escaped control characters, and no NaN/Infinity. Numbers in signed records should be **typed decimal strings** (e.g. `"100.000"`) with an explicit unit and precision rather than binary floating-point. Arrays retain declared order. Reject duplicate keys, unsupported encodings, non-normalized identifiers and unrecognized critical fields. Hash algorithm: SHA-256 over the canonical bytes, with domain separation for each artifact class. A later implementation must pin its JSON canonicalization rules (including Unicode normalization and numeric representation) before claiming cross-language equivalence.

`H(domain,payload) = SHA256(UTF8(domain) || 0x00 || CanonicalJSON(payload))`

Supported domains in this draft: `PEP/0.1/OBS`, `PEP/0.1/EDGE`, `PEP/0.1/CAPTURE`, `PEP/0.1/REPLAY`, `PEP/0.1/COMPARE`. The domain tag prevents one artifact class from being silently substituted for another.

## Original acquisition
A minimal observation contains `capture_id`, `index`, `acquisition_source`, `scope`, `measurement` (value as decimal string, unit, precision), `clock_coordinates` (independent device/system/heartbeat entries with uncertainty), and `emitter_attribution` (KNOWN/UNKNOWN/DISPUTED). Do not conflate recorder identity with emitter identity. A capture manifest commits ordered observation digests, adjacency receipts, start/finish commitments, canonicalizer version and evidence locator. A chain with N observations has N-1 edges when N>=2; no edge is fabricated for N<2.

Each edge payload references `capture_id`, `edge_index`, `before_observation_digest`, `after_observation_digest`, and `previous_edge_digest` (null for first edge). A verifier recomputes every digest and checks contiguous indices, start/finish bindings, exact observation order and complete adjacency. Missing or altered originals return FAIL_CLOSED for **original-chain integrity**; a valid recorder record with unknown emitter may still be preserved.

## Replay
A replay request references an original capture digest and selected edge/observation digests. The verifier records VERIFIED, MISSING, CONTRADICTORY or UNSUPPORTED per requested interval. Any inferred samples belong to a separate derived artifact containing method/version/parameters, source refs, uncertainty and gap map. A replay never writes into original receipts, and a new derived identity is mandatory even when visually identical to the original.

## Comparison
Each input has an origin capture identity and a set of ancestry references. Comparison checks common ancestors before claiming independent corroboration. Identical origin, shared ancestor or unverifiable lineage prevents an independence SUPPORTED result. Time alignment is a separate bounded derived transform; unmatched clocks are not rewritten. Comparison output records agreement, divergence, unknown regions, alignment assumptions, uncertainty and lineage status.

## Golden vector definitions
The following **inputs** are normative only for the proposed fixture and are not empirical physical recordings. Their expected outputs are predicates rather than unverified literal digests.

| ID | Fixture | Expected outcome |
|---|---|---|
| GV-A1 | three ordered synthetic observations, complete start/finish, recorder bound, emitter UNKNOWN | 2 contiguous edges; original integrity VERIFIED; attribution UNKNOWN |
| GV-A2 | mutate middle observation after edge commitment | original integrity FAIL_CLOSED |
| GV-A3 | omit second edge receipt | original integrity FAIL_CLOSED |
| GV-A4 | identical payload encoded under OBS and EDGE domain tags | distinct digest outputs |
| GV-A5 | device/system/heartbeat disagree beyond uncertainty | preserve three coordinates; time alignment UNSUPPORTED until explicit transform |
| GV-B1 | intact original replay, no inference | verified replay with original source refs |
| GV-B2 | missing interval, labeled interpolation | separate derived identity, gap map, method, uncertainty; original remains incomplete |
| GV-C1 | two artifacts with distinct IDs but common origin | comparison allowed; independent-source standing NOT_ESTABLISHED |
| GV-C2 | independent acquisition identities but no lineage verification | independent-source standing NOT_ESTABLISHED |
| GV-C3 | two independently verified acquisition histories, bounded alignment | compare supported features, report agreement/divergence/unknown; no automatic causal emitter attribution |

## Implementation acceptance checks
1. One executable reference implementation computes actual canonical bytes and SHA-256 values for each vector; freeze its outputs in machine-readable fixture data.
2. An independent implementation reproduces the same bytes and digests, or reports a specific incompatibility.
3. Tests reject duplicate JSON keys, float ambiguity, missing edge, altered observation, swapped ordering, mismatched domains, broken ancestry and silent clock substitution.
4. No validation success is interpreted as evidence of real physical acquisition, identified emitter, permission to publish, or patentability.

## Patent figures (technical drawing instructions)
- Fig. 1: acquisition recorder and unknown emitter as separate identities; finite observations feed canonicalizer, edge chain and manifest.
- Fig. 2: three non-coincident clock coordinate tracks, uncertainty bands and a separate alignment transformation.
- Fig. 3: receipt verifier branching into VERIFIED originals and labeled degraded replay with a new identity.
- Fig. 4: provenance DAG with two distinct derived artifacts sharing an original ancestor, and a NOT_ESTABLISHED independence output.
- Fig. 5: three independent technical mechanisms A/B/C with optional downstream governance and no backward mutation path.

## Open filing questions
Prior-art search, inventor conception/disclosure dates, enablement examples, calibration assumptions, practical sensor embodiments, ownership, jurisdictions, filing type, and counsel claim language remain unresolved. This document is not an instruction to defer filing until every research candidate is proven; counsel must assess adequate written description and filing timing.
