"""Tiny test helpers (no pytest required)."""

from __future__ import annotations


def assert_raises(expected, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except expected:
        return
    except Exception as e:  # noqa: BLE001
        raise AssertionError(
            f"expected {expected.__name__}, got {type(e).__name__}: {e}"
        ) from e
    raise AssertionError(f"expected {expected.__name__}, but nothing was raised")
