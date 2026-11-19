# Canonical Task Discovery Mixed References Mirror Handoff

Updated: 2026-11-18 America/Chicago
Repository: StegVerse-Labs/.github
Existing coordination Goal Task ID: STEGVERSE-CANONICAL-WORK-COORDINATION-001
Canonical goal state: PROPOSED (G326 at 34ef695f2a0fcf0d2efd93ce6cb2d6352c510362).
Parent canonical handoff: docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md
Owner: https://github.com/StegVerse-Labs/.github/issues/3195

## Reproduction and bounded repair

At the pinned main, `python scripts/query_canonical_tasks.py --registry data/canonical-task-registry.json --include-closed Trumpality` raises `AttributeError: 'str' object has no attribute 'get'`. Current records contain both mapping and string dependencies/blockers. The first failure is the string dependency in MIR-AGENTENVELOPE-DERIVED-AUTHORITY-RECONCILIATION-001; later string blockers are independently affected.

The repair adds literal string references to the searchable text and retains the original selected mapping fields. Returned canonical records, lifecycle filters, AND term matching, and non-authorizing output remain unchanged. No canonical data, vectors, collision evaluator, claims, runtime, or admission mechanism changes.

## Validation and continuation

Run `python -m unittest discover -s tests -p test_query_canonical_tasks.py -v`.
Run the discovery command above on the complete current aggregate, and repeat with `--include-closed ERL research`. Search results are candidates, never proof of uniqueness or collision clearance. The full collision evaluator and authority-owner registration process in docs/TASK_REGISTRATION_GUIDE.md remain required.

This is source preparation for owner review. Merge, native registration, WorkerCoordinator claim/fence, runtime observation, and completion are not asserted. Read the PR's exact-head checks before integration; rebase and rerun on any change to main.
