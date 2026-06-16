"""
Exception hierarchy for :mod:`hijrical`.

All errors raised by the library derive from :class:`HijriError`, so a single
``except HijriError`` will catch every library-specific failure.
"""

from __future__ import annotations


class HijriError(Exception):
    """Base class for every error raised by :mod:`hijrical`."""


class InvalidDateError(HijriError, ValueError):
    """The given year/month/day do not form a valid calendar date.

    Also derives from :class:`ValueError`, so ordinary ``except ValueError``
    handlers will catch it too.
    """


class OutOfRangeError(HijriError, ValueError):
    """The date falls outside the reliable range of the selected method.

    The arithmetic calendar has no range limit, but astronomical/visibility
    methods rely on truncated series whose accuracy degrades far from the
    present era.
    """


class LocationRequiredError(HijriError, ValueError):
    """A sunset/visibility computation was requested without a location.

    Sunset (and therefore the Islamic day boundary) depends on geographic
    position, so latitude/longitude must be supplied.
    """


class ParseError(HijriError, ValueError):
    """A date string could not be parsed into a Hijri date."""
