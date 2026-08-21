from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .independent_oscillator import OSCILLATOR_PERIOD_NS, derive_reference


@dataclass(frozen=True)
class OscillatorPulseBatch:
    """A time-derived heartbeat production record.

    A batch represents every oscillator reference that became due since the last
    emitted reference. Normal operation produces one reference per batch. If a
    consumer is delayed, the producer compresses the missed reference interval
    into one bounded record rather than manufacturing an event per missed beat.
    """

    first_epoch: int
    last_epoch: int
    count: int
    produced_unix_ns: int
    period_ns: int = OSCILLATOR_PERIOD_NS

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "stegverse.heartbeat-oscillator-pulse-batch/v1",
            "mechanism": "INDEPENDENT_PHASE_OSCILLATOR",
            "progression_dependency": "OSCILLATOR_ONLY",
            "first_epoch": self.first_epoch,
            "last_epoch": self.last_epoch,
            "count": self.count,
            "produced_unix_ns": self.produced_unix_ns,
            "period_ns": self.period_ns,
            "event_trigger_required": False,
            "worker_or_task_gating": False,
            "authority_effect": "NONE",
        }


def next_due_unix_ns(oscillator: dict[str, Any], *, last_emitted_epoch: int) -> int:
    """Return the exact oscillator phase boundary for the next reference.

    This converts the producer from "sleep after an event" to "wake for the
    next oscillator phase boundary". The deadline is derived solely from the
    immutable oscillator anchor and period.
    """
    period_ns = int(oscillator["period_ns"])
    anchor_epoch = int(oscillator["anchor_epoch"])
    anchor_unix_ns = int(oscillator["anchor_unix_ns"])
    if period_ns != OSCILLATOR_PERIOD_NS:
        raise RuntimeError("heartbeat oscillator period must remain exactly 10 ms")
    next_epoch = int(last_emitted_epoch) + 1
    if next_epoch <= anchor_epoch:
        return anchor_unix_ns
    return anchor_unix_ns + (next_epoch - anchor_epoch) * period_ns


def due_pulse_batch(
    oscillator: dict[str, Any],
    *,
    now_ns: int,
    last_emitted_epoch: int,
) -> OscillatorPulseBatch | None:
    """Return oscillator-produced references due at ``now_ns``.

    No event, worker, task, claim, fence, route, credential, or repository
    mutation participates in the calculation. Calling this function more often
    cannot advance the oscillator because the current reference is derived only
    from phase travel relative to the immutable oscillator anchor.
    """
    reference = derive_reference(oscillator, now_ns=now_ns)
    current_epoch = int(reference["epoch"])
    if current_epoch <= int(last_emitted_epoch):
        return None
    first_epoch = int(last_emitted_epoch) + 1
    return OscillatorPulseBatch(
        first_epoch=first_epoch,
        last_epoch=current_epoch,
        count=current_epoch - first_epoch + 1,
        produced_unix_ns=now_ns,
    )


class OscillatorProducer:
    """Produce heartbeat reference batches from oscillator phase travel only.

    The producer is deliberately ignorant of GitHub events and worker/task
    state. A resident runtime waits for ``next_due_unix_ns`` and calls
    ``run_once`` at that oscillator-derived phase boundary. The supplied sink is
    downstream observation/transport only and cannot influence which references
    exist.
    """

    def __init__(
        self,
        oscillator: dict[str, Any],
        *,
        initial_emitted_epoch: int,
        clock_ns: Callable[[], int],
        sink: Callable[[OscillatorPulseBatch], None],
    ) -> None:
        self._oscillator = dict(oscillator)
        self._last_emitted_epoch = int(initial_emitted_epoch)
        self._clock_ns = clock_ns
        self._sink = sink

    @property
    def last_emitted_epoch(self) -> int:
        return self._last_emitted_epoch

    @property
    def next_due_unix_ns(self) -> int:
        return next_due_unix_ns(self._oscillator, last_emitted_epoch=self._last_emitted_epoch)

    def run_once(self) -> OscillatorPulseBatch | None:
        now_ns = int(self._clock_ns())
        batch = due_pulse_batch(
            self._oscillator,
            now_ns=now_ns,
            last_emitted_epoch=self._last_emitted_epoch,
        )
        if batch is None:
            return None
        self._sink(batch)
        self._last_emitted_epoch = batch.last_epoch
        return batch


__all__ = [
    "OscillatorPulseBatch",
    "OscillatorProducer",
    "due_pulse_batch",
    "next_due_unix_ns",
]
