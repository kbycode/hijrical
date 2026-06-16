"""
Julian Day Number (JDN) core.

Calendar conversion is done through the Julian Day Number: every system is
mapped onto a single integer axis (one integer per day), and arithmetic is
performed there. We use **pure integer arithmetic** end to end, which is what
makes the conversions exact and perfectly reversible -- no floating-point
rounding that can shift a date by a day at month boundaries.

The civil calendar used is the **proleptic Gregorian** calendar (Gregorian
rules extended backwards before 1582), matching ISO 8601 and the convention
of virtually all software.
"""

from __future__ import annotations

#: JDN of 1970-01-01 (the Unix epoch), provided as a convenience constant.
JDN_UNIX_EPOCH = 2440588


def gregorian_to_jdn(year: int, month: int, day: int) -> int:
    """Convert a proleptic Gregorian (year, month, day) to a Julian Day Number.

    Works for any date, including BCE years using astronomical year numbering
    (year 0 = 1 BCE).

    >>> gregorian_to_jdn(2000, 1, 1)
    2451545
    >>> gregorian_to_jdn(1970, 1, 1)
    2440588
    """
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return (
        day
        + (153 * m + 2) // 5
        + 365 * y
        + y // 4
        - y // 100
        + y // 400
        - 32045
    )


def jdn_to_gregorian(jdn: int) -> tuple[int, int, int]:
    """Convert a Julian Day Number to a proleptic Gregorian (year, month, day).

    Exact inverse of :func:`gregorian_to_jdn`.

    >>> jdn_to_gregorian(2451545)
    (2000, 1, 1)
    """
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    return year, month, day


def jdn_weekday(jdn: int) -> int:
    """Weekday index for a JDN. ``0=Monday`` ... ``6=Sunday`` (ISO / ``date.weekday()``)."""
    return jdn % 7


def is_valid_gregorian(year: int, month: int, day: int) -> bool:
    """Return whether (year, month, day) is a real Gregorian calendar date."""
    if month < 1 or month > 12 or day < 1 or day > 31:
        return False
    return jdn_to_gregorian(gregorian_to_jdn(year, month, day)) == (year, month, day)
