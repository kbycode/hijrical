"""
Convenience helpers for building calendar apps, countdown widgets and converters.

These sit on top of :class:`~hijrical.core.HijriDate` and the holidays module to
cover the things app authors reach for constantly: iterating dates, laying out a
month grid, finding the next occurrence of an annual date, and listing upcoming
religious days for a countdown.
"""

from __future__ import annotations

from datetime import date

from .core import HijriDate
from .exceptions import InvalidDateError
from .holidays import ReligiousDay, year_holidays


def hijri_range(start: HijriDate, end: HijriDate, step: int = 1):
    """Yield HijriDates from ``start`` (inclusive) to ``end`` (exclusive).

    Works like ``range``: ``step`` may be negative to count down. The calendar
    engine of ``start`` is preserved.

    >>> from hijrical import HijriDate
    >>> [d.day for d in hijri_range(HijriDate(1447, 9, 1), HijriDate(1447, 9, 4))]
    [1, 2, 3]
    """
    if step == 0:
        raise ValueError("step must not be zero")
    cal = start.calendar
    j, end_j = start.jdn, end.jdn
    if step > 0:
        while j < end_j:
            yield HijriDate.from_jdn(j, calendar=cal)
            j += step
    else:
        while j > end_j:
            yield HijriDate.from_jdn(j, calendar=cal)
            j += step


def days_in_month(year: int, month: int, calendar=None) -> int:
    """Number of days (29 or 30) in a Hijri month."""
    return HijriDate(year, month, 1, calendar=calendar).month_length()


def iter_month(year: int, month: int, calendar=None) -> list[HijriDate]:
    """Every day of a Hijri month, in order."""
    n = days_in_month(year, month, calendar)
    return [HijriDate(year, month, d, calendar=calendar) for d in range(1, n + 1)]


def month_calendar(year: int, month: int, calendar=None) -> list[list[HijriDate | None]]:
    """A month laid out as weeks of 7 cells (Monday-first), padded with ``None``.

    Perfect for rendering a calendar grid:

    >>> from hijrical import HijriDate
    >>> weeks = month_calendar(1447, 9)
    >>> len(weeks[0])
    7
    """
    days = iter_month(year, month, calendar)
    lead = days[0].weekday()  # 0 = Monday
    cells: list[HijriDate | None] = [None] * lead + days
    while len(cells) % 7:
        cells.append(None)
    return [cells[i:i + 7] for i in range(0, len(cells), 7)]


def next_occurrence(month: int, day: int, after=None, calendar=None) -> HijriDate:
    """The next time the annual date ``(month, day)`` falls strictly after ``after``.

    ``after`` defaults to today and may be a HijriDate or a ``datetime.date``.
    Handles the case where ``day`` is 30 but a given year's month has only 29
    days by skipping to the next valid year.

    >>> from hijrical import HijriDate
    >>> next_occurrence(9, 1, after=HijriDate(1447, 10, 1)).year
    1448
    """
    after = _as_hijri(after, calendar)
    cal = after.calendar
    year = after.year
    for _ in range(6):  # a few tries cover the 29/30-day edge case
        try:
            candidate = HijriDate(year, month, day, calendar=cal)
        except InvalidDateError:
            year += 1
            continue
        if candidate.jdn > after.jdn:
            return candidate
        year += 1
    raise InvalidDateError(
        f"Could not find an occurrence of month {month}, day {day}."
    )


def upcoming_holidays(count: int = 5, after=None, calendar=None,
                      key: str | None = None) -> list[ReligiousDay]:
    """The next ``count`` religious days after ``after`` (default today).

    Pass ``key`` to count only one kind of day (e.g. ``"ramadan_start"``).
    Returns :class:`~hijrical.holidays.ReligiousDay` objects in date order; call
    ``.name(lang)`` for a localized label.
    """
    after = _as_hijri(after, calendar)
    cal = after.calendar
    after_greg = after.to_gregorian()
    found: list[ReligiousDay] = []
    year = after.year
    horizon = after.year + 80  # bound the search for rare keys
    while len(found) < count and year <= horizon:
        for rd in year_holidays(year, cal):
            if rd.gregorian > after_greg and (key is None or rd.key == key):
                found.append(rd)
        year += 1
    found.sort(key=lambda r: r.gregorian)
    return found[:count]


def next_holiday(after=None, key: str | None = None, calendar=None) -> ReligiousDay | None:
    """The next religious day after ``after``; optionally filtered to a ``key``.

    Keys include ``ramadan_start``, ``eid_al_fitr``, ``eid_al_adha``,
    ``laylat_al_qadr``, ``mawlid`` ... Returns ``None`` if none is found.
    """
    items = upcoming_holidays(count=1, after=after, calendar=calendar, key=key)
    return items[0] if items else None


def days_until_holiday(key: str | None = None, after=None, calendar=None) -> int | None:
    """Days from ``after`` (default today) until the next holiday (optionally ``key``).

    Handy for a countdown: ``days_until_holiday("ramadan_start")``.
    """
    after = _as_hijri(after, calendar)
    rd = next_holiday(after=after, key=key, calendar=calendar)
    if rd is None:
        return None
    return after.days_until(rd.gregorian)


def _as_hijri(value, calendar) -> HijriDate:
    if value is None:
        return HijriDate.today(calendar=calendar)
    if isinstance(value, HijriDate):
        return value
    if isinstance(value, date):
        return HijriDate.from_date(value, calendar=calendar)
    raise TypeError("expected a HijriDate, a datetime.date, or None")
