# DC vacuous-local-pass counterexample and typed SDK candidacy (generation 262)

Existing task `ADMISSIBLE-EXISTENCE-MATHEMATICAL-PROCESSING-INTEGRATION`, COSV `10111110111000`. Source authority remains `Admissible-Existence/DC`, whose canonical handoff `docs/DC_MIRROR_HANDOFF.md` is `IMPLEMENTATION_COMPLETE_DETERMINISTICALLY_AND_HOSTED_VALIDATED — BOUNDED_TRIFORM_COMPLETE_MERGED`. Its four proof candidates remain candidates, not proven theorems.

Pinned source: `Admissible-Existence/DC/tools/run_dc_fixtures.py::evaluate`, Git blob `15bfb04e483777a9f829c9f69d56b2d97d6510e1`; native handoff blob `5dee9d3de051afc8f60ef881c27ca2c07bc3f732`; proof candidates blob `8510903f0ecd78a74f8fd4566aa33c19b61b40b5`.

## Exact implementation theorem and counterexamples

For mapping input whose `nodes` is iterable over mapping nodes, `observed_posture=ALLOW-CANDIDATE` iff every supplied node has `local_coherence=PASS` **and** `global_reconciliation=PASS`. Otherwise the source reports FAIL-CLOSED. This is a finite-list predicate equivalence, not a proof of DC-PC-001..004, nor any global coherence, identity, authority or lineage theorem.

The implementation uses `all(node.get("local_coherence") == "PASS" for node in data.get("nodes", []))`. Empty lists satisfy `all([])=True`, so `evaluate({"nodes":[],"global_reconciliation":"PASS"})["observed_posture"] == "ALLOW-CANDIDATE"`. A missing `nodes` key has the same behavior. A node list with every local PASS but global FAIL returns FAIL-CLOSED and illustrates the bounded DC-PC-001 separation. An empty population is not evidence of distributed coherence. Nonmapping nodes, noniterable `nodes` or nonmapping root can raise rather than return FAIL-CLOSED.

The returned `result` field is **fixture comparison**: PASS iff `observed_posture == expected_posture`. An attacker-supplied `expected_posture` can cause fixture PASS even when observed posture is FAIL-CLOSED, and missing `expected_posture` causes comparison FAIL even for a source ALLOW-CANDIDATE. Neither fixture comparison nor ALLOW-CANDIDATE is InTr ALLOW.

## Required native-owner / existing SDK contract

Do not change released DC source from this integration task. Native DC ownership must separately admit an installed adapter for the existing generic `stegverse.route.source-native-math.v1`, around the unchanged callable. Before calling it, bind a frozen exact original specimen and matching typed native_input, require a nonempty list of typed node mappings, explicit local-coherence vocabulary and explicit global-reconciliation vocabulary, reject missing/unknown states and malformed roots, and distinguish independently computed observed posture from fixture `expected_posture` comparison. Include negative controls for empty/missing nodes, one local FAIL, all local PASS/global FAIL, unknown categories, nonmapping node/root, contradictory expected posture, forged source blob, specimen bytes, canonical native result and request binding. Obtain original installed adapter Git blob, frozen specimen SHA256, canonical native result SHA256, SDK manifest SHA256, dispatch request SHA256 and pre-enrichment result SHA256 from actual original-owner SDK invocation before changing census status.

This coordination assessment is not a source fix, installed SDK invocation, universal proof, WorkerCoordinator/InTr disposition or original organization/Master Records execution evidence. DC stays `NOT_ESTABLISHED` for SDK invocation.
