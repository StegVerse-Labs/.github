#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

OWNER_PATH_PATTERNS = (
    re.compile(r"^tasks/"),
    re.compile(r"(^|/)docs/.*HANDOFF.*\.md$", re.I),
    re.compile(r"(^|/)coordination/"),
    re.compile(r"(^|/)control/"),
    re.compile(r"(^|/)data/canonical-task"),
)
RELEASE_WORDS = re.compile(r"\b(resolved|superseded|released|retired|closed|source[_ -]?retired|merged)\b", re.I)

def run(*args: str) -> str:
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise SystemExit(f"command failed ({p.returncode}): {' '.join(args)}\n{p.stderr}")
    return p.stdout

def owner_path(path: str) -> bool:
    return any(p.search(path) for p in OWNER_PATH_PATTERNS)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--hygiene-report", required=True)
    ap.add_argument("--output", default="hygiene/owner-transition-delta.json")
    args = ap.parse_args()

    report = json.loads(Path(args.hygiene_report).read_text(encoding="utf-8"))
    structural = [
        r["branch"] for r in report.get("branches", [])
        if r.get("category") == "RETIREMENT_CANDIDATE_REQUIRES_OWNER_CLEARANCE"
    ]
    approved = set(report.get("approved_retirement_ready", []))
    residual = [b for b in structural if b not in approved]

    changed = [x for x in run("git", "diff", "--name-only", f"{args.baseline}..{args.head}").splitlines() if x]
    changed_owner = [x for x in changed if owner_path(x)]

    newly_eligible = []
    touched_but_not_explicitly_released = []
    for branch in residual:
        refs = []
        explicit_release = False
        for path in changed_owner:
            try:
                text = run("git", "show", f"{args.head}:{path}")
            except SystemExit:
                continue
            if branch in text:
                refs.append(path)
                if RELEASE_WORDS.search(text):
                    explicit_release = True
        if refs and explicit_release:
            newly_eligible.append({"branch": branch, "changed_owner_refs": sorted(set(refs))})
        elif refs:
            touched_but_not_explicitly_released.append({"branch": branch, "changed_owner_refs": sorted(set(refs))})

    out = {
        "schema": "stegverse.repository-hygiene-owner-transition-delta/v1",
        "baseline": args.baseline,
        "head": args.head,
        "structural_candidates": len(structural),
        "approved_ready": len(approved),
        "residual_candidates": len(residual),
        "changed_paths": changed,
        "changed_owner_paths": changed_owner,
        "newly_eligible_candidates": newly_eligible,
        "owner_touched_but_not_explicitly_released": touched_but_not_explicitly_released,
        "zero_delta": len(newly_eligible) == 0,
        "authority_effect": "NONE",
        "deletion_authorized": False,
        "notes": "Fail-closed prefilter only. A candidate may advance to owner-clearance review only when its exact branch name appears in an owner-bearing file changed since baseline and that changed owner surface explicitly records a release/resolution/supersession/retirement state. Final containment and ownership checks remain required before approval."
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
