"""HB-derived machine-continuation cadence.

This module derives a low-frequency continuation window from the canonical
100 Hz HeartBeat protocol reference. The derived trigger is non-authorizing:
it does not grant admission, execution, claim/fence, credential, repository,
merge, publication, or consequence authority.

A resident WorkerCoordinator may use this trigger to revisit already-admitted
machine-owned work. Missing windows collapse to the current window; they are
not replayed one-by-one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .independent_oscillator import PROTOCOL_ANCHOR_EPOCH, REFERENCE_FREQUENCY_HZ, encode_heartbeat_id

DEFAULT_CONTINUATION_SECONDS = 3600
DEFAULT_CONTINUATION_QUANTA = REFERENCE_FREQUENCY_HZ * DEFAULT_CONTINUATION_SECONDS
SCHEMA = "stegverse.hb-machine-continuation/v1"


@dataclass(frozen=True)
class ContinuationWindow:
    window_id: int
    start_epoch: int
    end_epoch_exclusive: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "start_epoch": self.start_epoch,
            "start_heartbeat_id": encode_heartbeat_id(self.start_epoch),
            "end_epoch_exclusive": self.end_epoch_exclusive,
            "period_quanta": self.end_epoch_exclusive - self.start_epoch,
        }


def derive_continuation_window(
    reference_epoch: int,
    *,
    period_quanta: int = DEFAULT_CONTINUATION_QUANTA,
) -> ContinuationWindow:
    if not isinstance(reference_epoch, int) or isinstance(reference_epoch, bool):
        raise TypeError("reference_epoch must be an integer")
    if reference_epoch < PROTOCOL_ANCHOR_EPOCH:
        raise ValueError("reference_epoch precedes the canonical HB protocol anchor")
    if not isinstance(period_quanta, int) or isinstance(period_quanta, bool) or period_quanta <= 0:
        raise ValueError("period_quanta must be a positive integer")
    elapsed = reference_epoch - PROTOCOL_ANCHOR_EPOCH
    window_id = elapsed // period_quanta
    start = PROTOCOL_ANCHOR_EPOCH + window_id * period_quanta
    return ContinuationWindow(window_id, start, start + period_quanta)


def build_continuation_trigger(
    reference_epoch: int,
    *,
    last_consumed_window_id: int | None,
    period_quanta: int = DEFAULT_CONTINUATION_QUANTA,
) -> dict[str, Any]:
    window = derive_continuation_window(reference_epoch, period_quanta=period_quanta)
    due = last_consumed_window_id is None or window.window_id > last_consumed_window_id
    return {
        "schema": SCHEMA,
        "reference_epoch": reference_epoch,
        "reference_heartbeat_id": encode_heartbeat_id(reference_epoch),
        "reference_frequency_hz": REFERENCE_FREQUENCY_HZ,
        "window": window.as_dict(),
        "last_consumed_window_id": last_consumed_window_id,
        "continuation_due": due,
        "missed_windows_replayed": False,
        "heartbeat_progression_effect": "NONE",
        "heartbeat_grants_execution_authority": False,
        "trigger_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_TRIGGER_ONLY",
    }


__all__ = [
    "SCHEMA",
    "DEFAULT_CONTINUATION_SECONDS",
    "DEFAULT_CONTINUATION_QUANTA",
    "ContinuationWindow",
    "derive_continuation_window",
    "build_continuation_trigger",
]
