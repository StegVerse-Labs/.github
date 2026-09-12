#!/usr/bin/env python3
"""Install ERL active-research request wiring into existing resident source.

Source transformation only. No listener, scheduler, WorkerCoordinator, claim,
fence, credential, transport event, provider operation, or runtime receipt is
created by this installer.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER = ROOT / "scripts/dispatch_resident_execution_requests.py"
MATERIALIZER = ROOT / "scripts/install_sovereign_heartbeat_service.py"

CONSUMER_ROWS = (
    '    ("erl_active_research_intr_runtime_binding", "control/resident-execution-request.d/consume-erl-active-research-intr-runtime-binding.py"),\n',
    '    ("erl_active_research_intr_submission", "control/resident-execution-request.d/consume-erl-active-research-intr-submission.py"),\n',
)
CONSUMER_ANCHOR = '    ("stegos_kv_intr_chain", "scripts/consume_stegos_kv_intr_chain_request.py"),\n'
ENV_ROWS = (
    '    "STEGVERSE_ERL_ROOT",\n',
    '    "STEGVERSE_ERL_ACTIVE_RESEARCH_DISPATCH_PATH",\n',
    '    "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL",\n',
)
ENV_ANCHOR = '    "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID", "STEGVERSE_OWNER_BINDING_DIGEST", "STEGVERSE_STEGFIN_SOURCE_ROOT",\n'
COPY_ROWS = (
    '    "scripts/prepare_erl_active_research_intr_runtime_source.py",\n',
    '    "scripts/install_erl_active_research_universal_intr_route.py",\n',
    '    "scripts/install_erl_device_kv_prior_lineage.py",\n',
    '    "scripts/install_erl_resident_request_wiring.py",\n',
    '    "scripts/materialize_erl_active_research_intr_resident_local_input.py",\n',
    '    "scripts/submit_erl_active_research_intr_binding.py",\n',
    '    "scripts/submit_erl_active_research_intr_binding_local.py",\n',
    '    "workers/erl_active_research_transport.py",\n',
    '    "workers/erl_device_kv_terminal.py",\n',
)
COPY_ANCHOR = '    "scripts/consume_stegos_kv_intr_chain_request.py",\n'
REQUIRED_ROWS = (
    '        target_root / "scripts" / "prepare_erl_active_research_intr_runtime_source.py",\n',
    '        target_root / "scripts" / "install_erl_active_research_universal_intr_route.py",\n',
    '        target_root / "scripts" / "install_erl_device_kv_prior_lineage.py",\n',
    '        target_root / "scripts" / "install_erl_resident_request_wiring.py",\n',
    '        target_root / "scripts" / "materialize_erl_active_research_intr_resident_local_input.py",\n',
    '        target_root / "scripts" / "submit_erl_active_research_intr_binding.py",\n',
    '        target_root / "scripts" / "submit_erl_active_research_intr_binding_local.py",\n',
    '        target_root / "workers" / "erl_active_research_transport.py",\n',
    '        target_root / "workers" / "erl_device_kv_terminal.py",\n',
)
REQUIRED_ANCHOR = '        target_root / "scripts" / "consume_stegos_kv_intr_chain_request.py",\n'


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def transform_dispatcher(text: str) -> str:
    result = text
    if any(row not in result for row in CONSUMER_ROWS):
        require(result.count(CONSUMER_ANCHOR) == 1, "dispatcher consumer anchor drift")
        insertion = ''.join(row for row in CONSUMER_ROWS if row not in result)
        result = result.replace(CONSUMER_ANCHOR, CONSUMER_ANCHOR + insertion, 1)
    if any(row not in result for row in ENV_ROWS):
        require(result.count(ENV_ANCHOR) == 1, "dispatcher env anchor drift")
        insertion = ''.join(row for row in ENV_ROWS if row not in result)
        result = result.replace(ENV_ANCHOR, ENV_ANCHOR + insertion, 1)
    return result


def transform_materializer(text: str) -> str:
    result = text
    if any(row not in result for row in COPY_ROWS):
        require(result.count(COPY_ANCHOR) == 1, "materializer copy anchor drift")
        insertion = ''.join(row for row in COPY_ROWS if row not in result)
        result = result.replace(COPY_ANCHOR, COPY_ANCHOR + insertion, 1)
    if any(row not in result for row in REQUIRED_ROWS):
        require(result.count(REQUIRED_ANCHOR) == 1, "materializer required anchor drift")
        insertion = ''.join(row for row in REQUIRED_ROWS if row not in result)
        result = result.replace(REQUIRED_ANCHOR, REQUIRED_ANCHOR + insertion, 1)
    return result


def apply(path: Path, transform, check: bool) -> None:
    before = path.read_text(encoding="utf-8")
    after = transform(before)
    if check:
        require(after == before, f"{path.name} ERL request wiring not installed")
    elif after != before:
        path.write_text(after, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    apply(DISPATCHER, transform_dispatcher, args.check)
    apply(MATERIALIZER, transform_materializer, args.check)
    print("PASS: ERL resident request wiring is consistent")
    print("NONCLAIM: source wiring does not prove request consumption or Universal InTr transport")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
