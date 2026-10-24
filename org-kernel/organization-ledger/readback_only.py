#!/usr/bin/env python3
"""Readback-only run: read the designated ledger back and record the invocation under a run id.

P1-FC-11 (ECOSYSTEM_CAPABILITY_ABSENT, StegVerse-org/.github#163, INDEX H51): the
federation readback sweep was a lane script (fetch each ref, run the readback,
record command, ref SHA and output sha256) with no Actions run id. This module
is the step the reusable workflow runs in `mode: readback`. It runs the
component's own `organization_ledger_readback.py` unchanged against a fresh
fetch of the designated ref, then writes `invocation.json`
(`stegverse.organization-ledger-readback-invocation/v1`). That file names the run
id, the ledger ref and the SHA it was read at, the component commit, the exact
command, the exit code and the sha256 of the readback output bytes.

It appends nothing, publishes nothing, reads no clock and adds no dependency.
The disposition is the readback's own disposition, copied as it is. The run
passes only on readback ALLOW with exit 0. An absent run id, component ref or
readback output, or an unreadable output, is a six-field FAIL_CLOSED, and the
invocation record is still written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

SCHEMA = "stegverse.organization-ledger-readback-invocation/v1"
GOAL = "StegVerse-org/.github#163"
RETRY = ".github/workflows/organization-ledger-transition-reusable.yml (mode: readback) step \"Read the designated ledger back (readback mode, nothing appended)\""
HERE = Path(__file__).resolve().parent
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


def refusal(code, predicate, repair, next_attempt):
    return {"disposition": "FAIL_CLOSED", "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": RETRY,
            "owning_existing_goal": GOAL, "next_attempt": next_attempt}


def run(location, out_dir, run_id, component_ref, ledger_ref, ref_sha, organization,
        org_contract=None, repository_namespace=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    readback_out = out_dir / "readback.json"
    command = [sys.executable, str(HERE / "organization_ledger_readback.py"), "--location", location,
               "--out", str(readback_out)]
    if org_contract:
        command += ["--org-contract", str(org_contract)]
    if repository_namespace:
        command += ["--repository-namespace", repository_namespace]
    record = {"schema": SCHEMA, "organization": organization, "run_id": run_id or None,
              "component_ref": component_ref or None, "ledger_ref": ledger_ref,
              "ledger_ref_sha": ref_sha or None, "appended": False,
              "authority_effect": "NONE_READBACK_ONLY",
              "command": ["organization_ledger_readback.py"] + command[2:]}
    gate = None
    if not run_id:
        gate = refusal("READBACK_RUN_ID_ABSENT", "READBACK_IS_RECORDED_UNDER_A_RUN_ID",
                       "pass the Actions run id (github.run_id) as --run-id; a readback with no run id is the lane-script case FC-11 replaces",
                       "re-dispatch mode readback; nothing was appended")
    elif not (isinstance(component_ref, str) and len(component_ref) == 40
              and all(c in "0123456789abcdef" for c in component_ref)):
        gate = refusal("COMPONENT_REF_NOT_PINNED", "REF_IS_A_40_HEX_COMMIT",
                       "pass the component commit the readback ran from",
                       "re-dispatch mode readback with the pinned component_ref; nothing was appended")
    if gate is None:
        proc = subprocess.run(command, capture_output=True, text=True)
        record["exit_code"] = proc.returncode
        try:
            raw = readback_out.read_bytes()
            result = json.loads(raw)
        except (OSError, ValueError) as exc:
            record["readback_sha256"] = None
            gate = refusal("READBACK_OUTPUT_UNREADABLE", "READBACK_WRITES_ITS_RESULT",
                           "the readback wrote no readable --out (%s); stderr: %s" % (type(exc).__name__, proc.stderr.strip()[-400:]),
                           "re-dispatch mode readback; nothing was appended")
        else:
            record["readback_sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
            disposition = result.get("disposition") if isinstance(result, dict) else None
            record["disposition"] = disposition
            if disposition != "ALLOW" or proc.returncode != 0:
                # The readback's own six fields are the finding; copied as they are, never re-labelled.
                if isinstance(result, dict) and all(isinstance(result.get(f), str) and result[f].strip() for f in SIX):
                    record.update({f: result[f] for f in SIX})
                    record["disposition"] = disposition if disposition in ("DENY", "FAIL_CLOSED") else "FAIL_CLOSED"
                else:
                    gate = refusal("READBACK_DISPOSITION_NOT_ALLOW", "READBACK_DISPOSITION_IS_ALLOW_WITH_EXIT_0",
                                   "the readback returned disposition %r with exit %d and no six fields" % (disposition, proc.returncode),
                                   "repair the ledger named by the readback, then re-dispatch mode readback")
    if gate is not None:
        record.update(gate)
    (out_dir / "invocation.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--location", required=True)
    p.add_argument("--out-dir", required=True, type=Path)
    p.add_argument("--run-id", default="")
    p.add_argument("--component-ref", default="")
    p.add_argument("--ledger-ref", required=True)
    p.add_argument("--ledger-ref-sha", default="")
    p.add_argument("--organization", required=True)
    p.add_argument("--org-contract", type=Path, default=None)
    p.add_argument("--repository-namespace", default=None)
    a = p.parse_args(argv)
    record = run(a.location, a.out_dir, a.run_id, a.component_ref, a.ledger_ref, a.ledger_ref_sha,
                 a.organization, a.org_contract, a.repository_namespace)
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if record.get("disposition") == "ALLOW" and record.get("exit_code") == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
