#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path

OUT = Path("hygiene")
OUT.mkdir(exist_ok=True)
DEFAULT = os.environ.get("DEFAULT_BRANCH", "main")
STALE_DAYS = int(os.environ.get("STALE_DAYS", "30"))
PROTECT_RE = re.compile(os.environ.get("PROTECT_RE", r"^(main|master|gh-pages|release/.*|support/.*)$"))
APPROVAL_FILE = os.environ.get("APPROVAL_FILE", ".github/repository-hygiene-approved-retirements.txt")
NOW = dt.datetime.now(dt.timezone.utc)

HYGIENE_CONTROL_PATHS = {
    ".github/repository-hygiene-approved-retirements.txt",
    "docs/REPOSITORY_HYGIENE_MIRROR_HANDOFF.md",
    "docs/REPOSITORY_HYGIENE_ADOPTION_MIRROR_HANDOFF.md",
}
HYGIENE_CONTROL_PREFIXES = (
    "evidence/repository-hygiene/",
    "control/repository-hygiene-",
)

def is_hygiene_control_path(path: str) -> bool:
    return path in HYGIENE_CONTROL_PATHS or any(path.startswith(prefix) for prefix in HYGIENE_CONTROL_PREFIXES)

def run(*args: str, check: bool = True) -> str:
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode:
        raise SystemExit(f"command failed ({p.returncode}): {' '.join(args)}\\n{p.stderr}")
    return p.stdout

def source_ref_counts(branch: str) -> tuple[int, int]:
    p = subprocess.run(["git", "grep", "-F", "-n", "--", branch, f"origin/{DEFAULT}"], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if p.returncode not in (0, 1):
        raise SystemExit(f"git grep failed for {branch}")
    retained = 0
    ignored_hygiene_control = 0
    for line in p.stdout.splitlines():
        if not line.strip():
            continue
        try:
            _, rest = line.split(":", 1)
            path, _ = rest.split(":", 1)
        except ValueError:
            retained += 1
            continue
        if is_hygiene_control_path(path):
            ignored_hygiene_control += 1
        else:
            retained += 1
    return retained, ignored_hygiene_control

raw = run("git", "for-each-ref", "--format=%(refname:lstrip=3)|%(objectname)|%(committerdate:unix)", "refs/remotes/origin")
rows = []
candidates = []
review = []
retained = []
counts: dict[str, int] = {}

for line in raw.splitlines():
    if not line or line.startswith("HEAD|"):
        continue
    name, sha, ts_s = line.split("|", 2)
    if name == "HEAD":
        continue
    age_days = max(0, int((NOW.timestamp() - int(ts_s)) // 86400))
    protected = name == DEFAULT or bool(PROTECT_RE.search(name))
    if name == DEFAULT:
        ahead = behind = 0
    else:
        counts_raw = run("git", "rev-list", "--left-right", "--count", f"origin/{DEFAULT}...origin/{name}").strip().split()
        behind, ahead = map(int, counts_raw)
    if name == DEFAULT:
        refs, ignored_hygiene_refs = 0, 0
    else:
        refs, ignored_hygiene_refs = source_ref_counts(name)
    stale = age_days > STALE_DAYS

    if protected:
        category = "PROTECTED_RETAIN"
        retained.append(name)
    elif ahead == 0 and refs == 0:
        category = "RETIREMENT_CANDIDATE_REQUIRES_OWNER_CLEARANCE"
        candidates.append(name)
    elif ahead == 0 and refs > 0:
        category = "REVIEW_REQUIRED_SOURCE_REFERENCED"
        review.append(name)
    elif refs > 0:
        category = "REVIEW_REQUIRED_UNIQUE_COMMITS_AND_SOURCE_REFERENCES"
        review.append(name)
    elif stale:
        category = "REVIEW_REQUIRED_STALE_WITH_UNIQUE_COMMITS"
        review.append(name)
    else:
        category = "REVIEW_REQUIRED_RECENT_WITH_UNIQUE_COMMITS"
        review.append(name)

    counts[category] = counts.get(category, 0) + 1
    rows.append({
        "branch": name, "sha": sha, "age_days": age_days, "behind_by": behind,
        "ahead_by": ahead, "default_branch_source_refs": refs,
        "ignored_hygiene_control_refs": ignored_hygiene_refs, "category": category,
        "deletion_authorized": False,
    })

approved = []
invalid_approved = []
ap = Path(APPROVAL_FILE)
if ap.exists():
    candidate_set = set(candidates)
    for item in ap.read_text(encoding="utf-8").splitlines():
        item = item.strip()
        if not item or item.startswith("#"):
            continue
        (approved if item in candidate_set else invalid_approved).append(item)

(OUT / "report.json").write_text(json.dumps({
    "schema": "stegverse.repository-hygiene-inventory/v1",
    "repository": os.environ.get("REPOSITORY", ""),
    "default_branch": DEFAULT,
    "observed_at": NOW.isoformat(),
    "stale_days": STALE_DAYS,
    "authority_effect": "NONE",
    "automatic_ref_deletion": False,
    "branches": rows,
    "approved_manifest": APPROVAL_FILE if ap.exists() else None,
    "approved_retirement_ready": approved,
    "invalid_approved_entries": invalid_approved,
}, indent=2) + "\n", encoding="utf-8")

with (OUT / "report.tsv").open("w", encoding="utf-8") as f:
    f.write("branch\\tsha\\tage_days\\tbehind_by\\tahead_by\\tdefault_branch_source_refs\\tcategory\\n")
    for r in rows:
        f.write(f"{r['branch']}\\t{r['sha']}\\t{r['age_days']}\\t{r['behind_by']}\\t{r['ahead_by']}\\t{r['default_branch_source_refs']}\\t{r['category']}\\n")

for filename, values in [
    ("retirement-candidates.txt", candidates),
    ("review-required.txt", review),
    ("protected-retained.txt", retained),
    ("approved-retirement-ready.txt", approved),
    ("invalid-approved-entries.txt", invalid_approved),
]:
    (OUT / filename).write_text("\n".join(values) + ("\n" if values else ""), encoding="utf-8")

summary = [
    "## Repository hygiene inventory", "",
    f"Repository: \`{os.environ.get('REPOSITORY', '')}\`", f"Default branch: \`{DEFAULT}\`",
    f"Branches inspected: **{len(rows)}**", f"Retirement candidates requiring owner clearance: **{len(candidates)}**",
    f"Review required: **{len(review)}**", f"Protected/retained: **{len(retained)}**",
    f"Approval-manifest entries ready for retirement authority: **{len(approved)}**",
    f"Invalid approval-manifest entries: **{len(invalid_approved)}**", "",
    "**Authority boundary:** this workflow performs classification only. It never deletes refs, closes PRs/issues, or treats age/name as deletion authority.", "",
    "| Category | Count |", "|---|---:|"
]
for k in sorted(counts):
    summary.append(f"| \`{k}\` | {counts[k]} |")
if invalid_approved:
    summary += ["", "### Invalid approved-retirement entries", ""] + [f"- \`{x}\`" for x in invalid_approved]
summary_text = "\n".join(summary) + "\n"
(OUT / "summary.md").write_text(summary_text, encoding="utf-8")
print(summary_text)
summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
if summary_path:
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(summary_text)
if invalid_approved:
    raise SystemExit("approval manifest contains branches that are not current retirement candidates")
