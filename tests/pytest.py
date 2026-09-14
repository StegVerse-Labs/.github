"""Minimal unittest-discovery compatibility shim for pytest-style test modules.

`python -m unittest discover -v tests` places the tests directory on sys.path, so
pytest-style modules can import this shim when the external pytest package is not
installed. Real pytest runs import the actual pytest package before collection,
so this file does not replace pytest in the dedicated pytest validation lane.
"""
from __future__ import annotations

import re
from contextlib import AbstractContextManager
from typing import Pattern, Type


class _Raises(AbstractContextManager[None]):
    def __init__(self, expected: Type[BaseException], match: str | Pattern[str] | None = None) -> None:
        self.expected = expected
        self.match = re.compile(match) if isinstance(match, str) else match

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc_type is None:
            raise AssertionError(f"DID NOT RAISE {self.expected.__name__}")
        if not issubclass(exc_type, self.expected):
            return False
        if self.match is not None and not self.match.search(str(exc)):
            raise AssertionError(
                f"exception message {str(exc)!r} does not match {self.match.pattern!r}"
            )
        return True


def raises(expected: Type[BaseException], *, match: str | Pattern[str] | None = None) -> _Raises:
    return _Raises(expected, match)
