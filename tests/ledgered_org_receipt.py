"""An organization receipt that is the organization ledger's own, for tests of its outbound carriage.

submit_org_transition_to_master_records.py publishes only a receipt its
organization ledger holds, reachable from HEAD (VALIDATOR row 4). This mints
one with the aggregate CLI, under the POSIX ledger locus declaration the CLI
tests use (tests/posix_ledger_locus), at a supplied root. The returned env
locates that ledger for the next CLI. Nothing is pushed or ledgered for real.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSIX_LEDGER_LOCUS = str(ROOT / "tests" / "posix_ledger_locus")


def ledger_env(base_env: dict, org_ledger_root: Path) -> dict:
    """`base_env` with the POSIX locus declaration and this organization ledger root."""
    return {**base_env, "STEGVERSE_ORG_LEDGER_ROOT": str(org_ledger_root),
            "PYTHONPATH": os.pathsep.join(filter(None, (POSIX_LEDGER_LOCUS, base_env.get("PYTHONPATH"))))}


def ledgered_org_receipt(work: Path, epoch: int, *, base_env: dict | None = None,
                         transition_id: str = "ledgered-org-receipt") -> tuple[Path, dict, dict]:
    """(receipt path, receipt, env) for an organization receipt appended to a ledger under `work`."""
    work = Path(work)
    env = ledger_env(dict(os.environ if base_env is None else base_env), work / "org-ledger")
    source = work / (transition_id + ".source.json")
    source.write_text(json.dumps({"schema": "stegverse.canonical-state-transition-receipt/v1",
                                  "transition_id": transition_id, "transition_sequence": 1,
                                  "subject_or_correlation_id": transition_id, "transition_outcome": "OBSERVED",
                                  "required_evidence_manifest": []}))
    # Loaded as a module, not run as __main__, so the locus declaration applies to it.
    entry = ("import importlib.util,sys; s=importlib.util.spec_from_file_location('aggregate_cli',sys.argv[1]); "
             "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); sys.argv=sys.argv[1:]; "
             "raise SystemExit(m.kernel.run_writer_cli(lambda: m.main() or 0, retry_entrypoint='test'))")
    completed = subprocess.run([sys.executable, "-B", "-c", entry, str(ROOT / "resident-runtime/aggregate_repo_transition.py"),
                                "--transition-receipt", str(source), "--hb-epoch", str(epoch)],
                               capture_output=True, text=True, env=env, cwd=str(work), timeout=120)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    receipt = json.loads(completed.stdout)
    path = work / (transition_id + ".org-receipt.json")
    path.write_text(json.dumps(receipt))
    return path, receipt, env
