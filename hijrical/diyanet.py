"""
Diyanet (Türkiye) calendar -- the official published Hijri calendar of Turkey.

Turkey's calendar follows the unified-calendar criteria adopted at the 2016
Istanbul congress (crescent elongation >= 8 deg and altitude >= 5 deg, judged
over land anywhere on Earth). :class:`~hijrical.calendars.AstronomicalCalendar`
with ``criterion="ircica", scope="global"`` reproduces that rule and agrees with
Diyanet in the overwhelming majority of months -- but not always: several month
boundaries are decided within **0.1 deg** of the threshold, where any difference
in ephemeris or refraction model flips the result. No independent computation
can therefore guarantee agreement.

So for the years Diyanet has published, this module does not compute anything:
it uses their **official table** verbatim, which is the only way to be exactly
right. Outside that range it falls back to the astronomical engine above, and
:func:`coverage` tells you which regime a date is in.

Source: T.C. Diyanet İşleri Başkanlığı, "Dini Günler" listings
(https://vakithesaplama.diyanet.gov.tr/dini_gunler.php), covering 2022-2027.
Each entry below is the Gregorian date of day 1 of that Hijri month, exactly as
published, and can be re-checked one by one against that source.
"""

from __future__ import annotations

from datetime import date

from ._julian import gregorian_to_jdn, jdn_to_gregorian
from .calendars import AstronomicalCalendar, Calendar
from .exceptions import InvalidDateError

#: Official first-of-month dates: (hijri_year, hijri_month, "YYYY-MM-DD").
#: Contiguous from 1443-06 to 1449-08 -- do not reorder or leave gaps.
DIYANET_MONTH_STARTS: tuple[tuple[int, int, str], ...] = (
    (1443, 6, "2022-01-04"), (1443, 7, "2022-02-02"), (1443, 8, "2022-03-04"),
    (1443, 9, "2022-04-02"), (1443, 10, "2022-05-02"), (1443, 11, "2022-05-31"),
    (1443, 12, "2022-06-30"),
    (1444, 1, "2022-07-30"), (1444, 2, "2022-08-28"), (1444, 3, "2022-09-27"),
    (1444, 4, "2022-10-27"), (1444, 5, "2022-11-25"), (1444, 6, "2022-12-24"),
    (1444, 7, "2023-01-23"), (1444, 8, "2023-02-21"), (1444, 9, "2023-03-23"),
    (1444, 10, "2023-04-21"), (1444, 11, "2023-05-21"), (1444, 12, "2023-06-19"),
    (1445, 1, "2023-07-19"), (1445, 2, "2023-08-17"), (1445, 3, "2023-09-16"),
    (1445, 4, "2023-10-16"), (1445, 5, "2023-11-14"), (1445, 6, "2023-12-14"),
    (1445, 7, "2024-01-12"), (1445, 8, "2024-02-11"), (1445, 9, "2024-03-11"),
    (1445, 10, "2024-04-10"), (1445, 11, "2024-05-09"), (1445, 12, "2024-06-07"),
    (1446, 1, "2024-07-07"), (1446, 2, "2024-08-05"), (1446, 3, "2024-09-04"),
    (1446, 4, "2024-10-04"), (1446, 5, "2024-11-03"), (1446, 6, "2024-12-02"),
    (1446, 7, "2025-01-01"), (1446, 8, "2025-01-31"), (1446, 9, "2025-03-01"),
    (1446, 10, "2025-03-30"), (1446, 11, "2025-04-29"), (1446, 12, "2025-05-28"),
    (1447, 1, "2025-06-26"), (1447, 2, "2025-07-26"), (1447, 3, "2025-08-24"),
    (1447, 4, "2025-09-23"), (1447, 5, "2025-10-23"), (1447, 6, "2025-11-21"),
    (1447, 7, "2025-12-21"), (1447, 8, "2026-01-20"), (1447, 9, "2026-02-19"),
    (1447, 10, "2026-03-20"), (1447, 11, "2026-04-18"), (1447, 12, "2026-05-18"),
    (1448, 1, "2026-06-16"), (1448, 2, "2026-07-15"), (1448, 3, "2026-08-14"),
    (1448, 4, "2026-09-12"), (1448, 5, "2026-10-12"), (1448, 6, "2026-11-10"),
    (1448, 7, "2026-12-10"), (1448, 8, "2027-01-09"), (1448, 9, "2027-02-08"),
    (1448, 10, "2027-03-09"), (1448, 11, "2027-04-08"), (1448, 12, "2027-05-07"),
    (1449, 1, "2027-06-06"), (1449, 2, "2027-07-05"), (1449, 3, "2027-08-03"),
    (1449, 4, "2027-09-02"), (1449, 5, "2027-10-01"), (1449, 6, "2027-10-31"),
    (1449, 7, "2027-11-29"), (1449, 8, "2027-12-29"),
)


def _build():
    index: dict[tuple[int, int], int] = {}
    jdns: list[int] = []
    for year, month, iso in DIYANET_MONTH_STARTS:
        y, m, d = (int(p) for p in iso.split("-"))
        jdn = gregorian_to_jdn(y, m, d)
        index[(year, month)] = jdn
        jdns.append(jdn)
    return index, tuple(jdns)


_INDEX, _JDNS = _build()
_FIRST_JDN = _JDNS[0]
_LAST_START_JDN = _JDNS[-1]
_ORDER = tuple(sorted(_INDEX))  # (year, month) pairs in calendar order


class DiyanetCalendar(Calendar):
    """Turkey's official (Diyanet) Hijri calendar.

    Inside the published range the answers come straight from Diyanet's table,
    so they match the official calendar exactly. Outside it, the astronomical
    unified-calendar engine takes over -- correct in principle, but a
    prediction, since Diyanet has not published those years yet.

    >>> from hijrical import HijriDate, DiyanetCalendar
    >>> HijriDate(1447, 9, 1, calendar=DiyanetCalendar()).to_gregorian()
    datetime.date(2026, 2, 19)
    """

    name = "diyanet"

    def __init__(self, fallback: Calendar | None = None) -> None:
        self.fallback = fallback or AstronomicalCalendar(
            "mecca", "ircica", scope="global"
        )

    # -- coverage -----------------------------------------------------------

    @staticmethod
    def coverage() -> tuple[tuple[int, int], tuple[int, int]]:
        """``((first_year, first_month), (last_year, last_month))`` of official data."""
        return _ORDER[0], _ORDER[-1]

    @staticmethod
    def covers(year: int, month: int) -> bool:
        """Whether this (year, month) is inside the official table."""
        return (year, month) in _INDEX

    def is_official(self, year: int, month: int, day: int = 1) -> bool:
        """Whether a date resolves from official data rather than the fallback."""
        return self.covers(year, month) and self._next_start(year, month) is not None

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _next_start(year: int, month: int) -> int | None:
        nxt = (year, month + 1) if month < 12 else (year + 1, 1)
        return _INDEX.get(nxt)

    # -- Calendar interface -------------------------------------------------

    def month_length(self, year: int, month: int) -> int:
        start = _INDEX.get((year, month))
        nxt = self._next_start(year, month)
        if start is not None and nxt is not None:
            return nxt - start
        return self.fallback.month_length(year, month)

    def to_jdn(self, year: int, month: int, day: int) -> int:
        if not 1 <= month <= 12:
            raise InvalidDateError(f"Month must be 1-12, got {month}.")
        start = _INDEX.get((year, month))
        if start is None:
            return self.fallback.to_jdn(year, month, day)
        length = self.month_length(year, month)
        if not 1 <= day <= length:
            raise InvalidDateError(
                f"Day {day} is out of range for {year}-{month:02d}, "
                f"which has {length} days in Diyanet's calendar."
            )
        return start + (day - 1)

    def from_jdn(self, jdn: int) -> tuple[int, int, int]:
        if jdn < _FIRST_JDN or jdn >= _LAST_START_JDN:
            return self.fallback.from_jdn(jdn)
        # Binary search for the last month start <= jdn.
        lo, hi = 0, len(_JDNS) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if _JDNS[mid] <= jdn:
                lo = mid
            else:
                hi = mid - 1
        year, month = _ORDER[lo]
        return year, month, jdn - _JDNS[lo] + 1


def official_range() -> tuple[date, date]:
    """Gregorian span covered by the official table."""
    y1, m1, d1 = jdn_to_gregorian(_FIRST_JDN)
    y2, m2, d2 = jdn_to_gregorian(_LAST_START_JDN)
    return date(y1, m1, d1), date(y2, m2, d2)
