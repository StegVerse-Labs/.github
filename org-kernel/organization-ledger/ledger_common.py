#!/usr/bin/env python3
"""Shared rules for the organization-ledger component (RTC-EVIDENCE-CUSTODY-004 profiles).

Stdlib only. This module holds the three rules every ledger writer in the
component applies, so that no writer carries its own copy:

1. Supplied epoch. Every receipt's ``hb_reference`` comes from a supplied
   heartbeat epoch: an integer >= 32 (the HB32 anchor), carried in the
   manifest or the dispatch. When none is supplied the append is FAIL_CLOSED
   ``HB_EPOCH_NOT_SUPPLIED``; a malformed one is FAIL_CLOSED
   ``HB_EPOCH_INVALID``. Either way nothing is written and no clock is read.
2. Six fields. Every non-ALLOW carries failure_code, failed_predicate,
   required_evidence_or_repair, retry_entrypoint, owning_existing_goal and
   next_attempt. ``owning_existing_goal`` is a consumer parameter.
3. Component-relative loading. A sibling module is loaded from this
   component's own directory. The consumer's contracts are read from the
   consumer root (the working directory; the reusable workflow runs at the
   consumer checkout). The org kernel is the component's sibling
   ``../kernel.py`` (org-kernel layout). No new environment variable is read:
   the only names a runtime module reads remain the ledger locations
   (STEGVERSE_REPO_LEDGER_ROOT / _ORG_LEDGER_ROOT / _REPO_LEDGER_HOME), so the
   governed-ingress census holds unchanged.

A legacy layout fallback (resident-runtime/, .stegverse/transition-ledger/
under the consumer root) exists only so that an existing fork can converge
in place (D6). In the component layout, the sibling always wins.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
HB_ANCHOR_EPOCH = 32
LEGACY_OWNING_GOAL = "LLMA-DECLARED-PATH-CONFORMANCE-368"
PARAMETERS_RELATIVE = ".stegverse/transition-ledger/organization-ledger.parameters.json"
_LEGACY = {
    "ledger_store.py": "resident-runtime/ledger_store.py",
    "emit.py": ".stegverse/transition-ledger/emit.py",
    "aggregate_repo_transition.py": "resident-runtime/aggregate_repo_transition.py",
    "organization_ledger_readback.py": "resident-runtime/organization_ledger_readback.py",
}


_BOUND_ROOT: Path | None = None


def consumer_root(legacy: Path | None = None) -> Path:
    """The consuming organization's checkout.

    For a module still in a legacy fork layout, that layout's root. Otherwise
    the working directory (the consumer checkout the workflow runs in).
    """
    global _BOUND_ROOT
    root = legacy.resolve() if legacy else Path.cwd().resolve()
    _BOUND_ROOT = root
    return root


def legacy_root_of(module_file: str) -> Path | None:
    here = Path(module_file).resolve().parent
    if here.name == "resident-runtime":
        return here.parent
    if here.name == "transition-ledger" and here.parent.name == ".stegverse":
        return here.parents[1]
    return None


def contract_path(name: str, root: Path) -> Path:
    return root / ".stegverse/transition-ledger" / name


def load_contract(name: str, root: Path) -> dict[str, Any]:
    return json.loads(contract_path(name, root).read_text())


def sibling(name: str, near: Path, root: Path) -> Path:
    """The component's own copy of ``name``; the legacy layout only when absent."""
    own = near / name
    if own.is_file():
        return own
    legacy = root / _LEGACY.get(name, name)
    if legacy.is_file():
        return legacy
    raise FileNotFoundError("component module not found: " + name)


def kernel_path(root: Path) -> Path:
    own = HERE.parent / "kernel.py"          # org-kernel/organization-ledger/ -> org-kernel/kernel.py
    if HERE.name == "organization-ledger" and own.is_file():
        return own
    return root / "org-kernel/kernel.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def entrypoint(module_file: str, function: str | None = None) -> str:
    """This module's path as a retry entrypoint: its legacy path in a fork, its component path otherwise."""
    here = Path(module_file).resolve()
    legacy = legacy_root_of(module_file)
    rel = here.relative_to(legacy).as_posix() if legacy else "org-kernel/organization-ledger/" + here.name
    return rel + ("::" + function if function else "")


def owning_existing_goal(default: str = LEGACY_OWNING_GOAL) -> str:
    """The consumer's owning goal: its committed parameter file, then the caller's default."""
    params = (_BOUND_ROOT or consumer_root()) / PARAMETERS_RELATIVE
    if params.is_file():
        try:
            value = json.loads(params.read_text()).get("owning_existing_goal")
        except ValueError:
            value = None
        if isinstance(value, str) and value:
            return value
    return default


def failure_code_of(message: str) -> str:
    head = str(message).split(":", 1)[0]
    return re.sub(r"[^A-Z0-9]+", "_", head.upper()).strip("_")


class LedgerRefusal(SystemExit):
    """A refused ledger operation. Nothing was written when this is raised.

    It is a SystemExit whose code is the original message, so existing callers
    and command-line use behave as before. ``refusal`` carries the six fields.
    """

    def __init__(self, message: str, *, failed_predicate: str | None = None,
                 required_evidence_or_repair: str | None = None,
                 retry_entrypoint: str = "", next_attempt: str | None = None,
                 disposition: str = "FAIL_CLOSED", failure_code: str | None = None,
                 schema: str = "stegverse.organization-ledger-append-refusal/v1",
                 owning_goal_default: str = LEGACY_OWNING_GOAL):
        super().__init__(message)
        code = failure_code or failure_code_of(message)
        self.refusal = {
            "schema": schema,
            "disposition": disposition,
            "failure_code": code,
            "failed_predicate": failed_predicate or code,
            "detail": str(message),
            "required_evidence_or_repair": required_evidence_or_repair
                or "correct the input or ledger state named by failure_code; nothing was written",
            "retry_entrypoint": retry_entrypoint,
            "owning_existing_goal": owning_existing_goal(owning_goal_default),
            "next_attempt": next_attempt
                or "retry the same call unchanged once the repair is made; nothing was appended",
            "consequence_committed": False,
            "authority_effect": "NONE_REFUSAL_ONLY",
        }
        self.failure_code = code
        self.failed_predicate = self.refusal["failed_predicate"]


def require_supplied_epoch(hb_epoch: Any, retry_entrypoint: str) -> int:
    """The shared epoch rule. Returns the epoch or raises six-field FAIL_CLOSED. Never reads a clock."""
    if hb_epoch is None or hb_epoch == "":
        raise LedgerRefusal(
            "HB_EPOCH_NOT_SUPPLIED", failure_code="HB_EPOCH_NOT_SUPPLIED",
            failed_predicate="HB_EPOCH_IS_SUPPLIED_BY_THE_MANIFEST_OR_DISPATCH",
            required_evidence_or_repair="supply hb_epoch (an integer >= 32) from the carrier, in the committed request or the dispatch; no clock is read",
            retry_entrypoint=retry_entrypoint,
            next_attempt="re-dispatch the same transition with hb_epoch supplied; nothing was appended")
    # ASCII digits only (TVC#517 require_hb_epoch): '+33', ' 33', '3_3', '٣٣' are not accepted,
    # although int() would accept them. CLIs therefore pass the epoch through as text.
    if isinstance(hb_epoch, str):
        if not re.fullmatch(r"[0-9]+", hb_epoch, flags=re.ASCII):
            raise LedgerRefusal(
                "HB_EPOCH_INVALID", failure_code="HB_EPOCH_INVALID",
                failed_predicate="HB_EPOCH_IS_AN_INTEGER_AT_OR_AFTER_THE_HB32_ANCHOR",
                required_evidence_or_repair="supply hb_epoch as ASCII digits only, >= 32; no clock is read",
                retry_entrypoint=retry_entrypoint,
                next_attempt="re-dispatch the same transition with a valid hb_epoch; nothing was appended")
        hb_epoch = int(hb_epoch)
    if isinstance(hb_epoch, bool) or not isinstance(hb_epoch, int) or hb_epoch < HB_ANCHOR_EPOCH:
        raise LedgerRefusal(
            "HB_EPOCH_INVALID", failure_code="HB_EPOCH_INVALID",
            failed_predicate="HB_EPOCH_IS_AN_INTEGER_AT_OR_AFTER_THE_HB32_ANCHOR",
            required_evidence_or_repair="supply hb_epoch as digits only, >= 32; no clock is read",
            retry_entrypoint=retry_entrypoint,
            next_attempt="re-dispatch the same transition with a valid hb_epoch; nothing was appended")
    return hb_epoch


def supplied_hb_reference(kernel: Any, hb_epoch: Any, retry_entrypoint: str) -> dict[str, Any]:
    return kernel.hb_reference(epoch=require_supplied_epoch(hb_epoch, retry_entrypoint))
