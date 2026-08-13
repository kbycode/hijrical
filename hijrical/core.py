"""
The public :class:`HijriDate` type and the high-level conversion helpers.

This is the everyday surface of the library. A :class:`HijriDate` is immutable,
comparable, hashable and arithmetic-friendly, and it can be produced from a
Gregorian date, a JDN, a string, "now", or a precise instant + location (which
honours the sunset day-boundary).
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

from ._julian import gregorian_to_jdn, jdn_to_gregorian, jdn_weekday
from ._sun import sunset
from .calendars import ArithmeticCalendar, AstronomicalCalendar, Calendar
from .exceptions import HijriError, ParseError
from .holidays import holiday_key, raghaib
from .locales import DEFAULT_LANGUAGE, get_locale, month_name, weekday_name
from .observer import resolve_observer
from .parsing import parse_fields

# Reusable default engines (so caches are shared, not rebuilt per call).
_DEFAULT_ARITHMETIC = ArithmeticCalendar("kuwaiti")
_NAMED_CACHE: dict[str, Calendar] = {}


def _resolve_calendar(calendar) -> Calendar:
    if calendar is None:
        return _DEFAULT_ARITHMETIC
    if isinstance(calendar, Calendar):
        return calendar
    if isinstance(calendar, str):
        key = calendar.strip().lower()
        if key in ("arithmetic", "tabular", "civil"):
            return _DEFAULT_ARITHMETIC
        if key in ("astronomical", "visibility", "crescent"):
            return _NAMED_CACHE.setdefault("astronomical", AstronomicalCalendar())
        if key in ("diyanet", "turkey", "turkiye"):
            from .diyanet import DiyanetCalendar
            return _NAMED_CACHE.setdefault("diyanet", DiyanetCalendar())
        raise HijriError(
            f"Unknown calendar {calendar!r}. Use 'arithmetic', 'astronomical', "
            "'diyanet', or pass a Calendar instance."
        )
    raise HijriError(f"Invalid calendar: {calendar!r}.")


class HijriDate:
    """An immutable Hijri (lunar Islamic) calendar date.

    Examples
    --------
    >>> HijriDate.from_gregorian(2026, 6, 15)
    HijriDate(1447, 12, 29, calendar='arithmetic')
    >>> HijriDate(1447, 9, 1).to_gregorian()
    datetime.date(2026, 2, 18)
    >>> str(HijriDate(1447, 9, 1))
    '1 Ramadan 1447 AH'
    """

    __slots__ = ("_year", "_month", "_day", "_jdn", "_calendar")

    def __init__(self, year: int, month: int, day: int, calendar=None) -> None:
        cal = _resolve_calendar(calendar)
        jdn = cal.to_jdn(year, month, day)  # validates and may raise
        object.__setattr__(self, "_year", year)
        object.__setattr__(self, "_month", month)
        object.__setattr__(self, "_day", day)
        object.__setattr__(self, "_jdn", jdn)
        object.__setattr__(self, "_calendar", cal)

    def __setattr__(self, *_):  # immutability
        raise AttributeError("HijriDate is immutable.")

    # -- constructors --------------------------------------------------------

    @classmethod
    def from_jdn(cls, jdn: int, calendar=None) -> "HijriDate":
        """Build from a Julian Day Number."""
        cal = _resolve_calendar(calendar)
        y, m, d = cal.from_jdn(jdn)
        return cls(y, m, d, calendar=cal)

    @classmethod
    def from_gregorian(cls, year: int, month: int, day: int, calendar=None) -> "HijriDate":
        """Build from a Gregorian (year, month, day)."""
        return cls.from_jdn(gregorian_to_jdn(year, month, day), calendar=calendar)

    @classmethod
    def from_date(cls, value: date, calendar=None) -> "HijriDate":
        """Build from a ``datetime.date`` (or ``datetime``)."""
        return cls.from_gregorian(value.year, value.month, value.day, calendar=calendar)

    @classmethod
    def parse(cls, text: str, calendar=None) -> "HijriDate":
        """Parse a Hijri date string (see :mod:`hijrical.parsing`).

        >>> HijriDate.parse("15 Ramadan 1447").to_gregorian()
        datetime.date(2026, 3, 4)
        """
        y, m, d = parse_fields(text)
        return cls(y, m, d, calendar=calendar)

    @classmethod
    def today(cls, calendar=None) -> "HijriDate":
        """Today's Hijri date by the system clock (civil; ignores sunset)."""
        return cls.from_date(date.today(), calendar=calendar)

    @classmethod
    def at(cls, instant: datetime, observer, calendar=None) -> "HijriDate":
        """Hijri date for a precise instant at a location, honouring **sunset**.

        Because the Islamic day starts at maghrib, an instant after local sunset
        already belongs to the next Hijri day.

        >>> from datetime import datetime
        >>> HijriDate.at(datetime(2026, 6, 15, 12, 0), "istanbul").isoformat()
        '1447-12-29'
        >>> HijriDate.at(datetime(2026, 6, 15, 22, 0), "istanbul").isoformat()
        '1447-12-30'
        """
        obs = resolve_observer(observer)
        tz = timezone(timedelta(hours=obs.utc_offset))
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=tz)
        local = instant.astimezone(tz)
        d = local.date()
        ss = sunset(d, obs.latitude, obs.longitude, obs.utc_offset)
        jdn = gregorian_to_jdn(d.year, d.month, d.day)
        if ss is not None and local >= ss:
            jdn += 1
        return cls.from_jdn(jdn, calendar=calendar)

    # -- conversions ---------------------------------------------------------

    def to_jdn(self) -> int:
        return self._jdn

    def to_gregorian(self) -> date:
        y, m, d = jdn_to_gregorian(self._jdn)
        return date(y, m, d)

    def to_gregorian_tuple(self) -> tuple[int, int, int]:
        return jdn_to_gregorian(self._jdn)

    # -- fields --------------------------------------------------------------

    @property
    def year(self) -> int:
        return self._year

    @property
    def month(self) -> int:
        return self._month

    @property
    def day(self) -> int:
        return self._day

    @property
    def jdn(self) -> int:
        return self._jdn

    @property
    def calendar(self) -> Calendar:
        return self._calendar

    @property
    def method(self) -> str:
        return self._calendar.name

    # -- calendar info -------------------------------------------------------

    def weekday(self) -> int:
        """Weekday index, 0=Monday ... 6=Sunday."""
        return jdn_weekday(self._jdn)

    def weekday_name(self, lang: str | None = None) -> str:
        return weekday_name(self.weekday(), lang)

    def month_name(self, lang: str | None = None) -> str:
        return month_name(self._month, lang)

    def month_length(self) -> int:
        return self._calendar.month_length(self._year, self._month)

    def year_length(self) -> int:
        return self._calendar.year_length(self._year)

    def is_leap_year(self) -> bool:
        return self._calendar.is_leap_year(self._year)

    def holiday(self, lang: str | None = None) -> str | None:
        """Localized religious-day name if this date is one, else ``None``."""
        key = holiday_key(self._month, self._day)
        if key is None and self._month == 7:
            rg = raghaib(self._calendar, self._year)
            if rg.hijri[1:] == (self._month, self._day):
                key = "raghaib"
        if key is None:
            return None
        return get_locale(lang)["holidays"][key]

    # -- formatting ----------------------------------------------------------

    def isoformat(self) -> str:
        """ISO-like zero-padded representation, ``YYYY-MM-DD``."""
        return f"{self._year:04d}-{self._month:02d}-{self._day:02d}"

    def format(self, pattern: str = "{day} {month_name} {year} {era}",
               lang: str | None = None) -> str:
        """Format with ``str.format`` fields.

        Fields: ``{year} {month} {day} {month02} {day02} {month_name}
        {weekday} {era} {method}``.

        >>> HijriDate(1447, 9, 1).format("{day} {month_name} {year}, {weekday}")
        '1 Ramadan 1447, Wednesday'
        """
        loc = get_locale(lang)
        fields = {
            "year": self._year,
            "month": self._month,
            "day": self._day,
            "month02": f"{self._month:02d}",
            "day02": f"{self._day:02d}",
            "month_name": loc["months"][self._month - 1],
            "weekday": loc["weekdays"][self.weekday()],
            "era": loc["era"],
            "method": self._calendar.name,
        }
        return pattern.format(**fields)

    def day_of_year(self) -> int:
        """1-based day number within the Hijri year."""
        return sum(self._calendar.month_length(self._year, m)
                   for m in range(1, self._month)) + self._day

    def strftime(self, fmt: str, lang: str | None = None) -> str:
        """Format with strftime-style codes; also powers f-strings.

        Codes: ``%Y %y %m %d %B %b %A %a %j %E %%``. Both of these work::

            d.strftime("%d %B %Y (%A)")
            f"{d:%d %B %Y}"

        >>> HijriDate(1447, 9, 1).strftime("%d %B %Y (%A)")
        '01 Ramadan 1447 (Wednesday)'
        """
        loc = get_locale(lang)
        wd = self.weekday()
        table = {
            "Y": f"{self._year:04d}", "y": f"{self._year % 100:02d}",
            "m": f"{self._month:02d}", "d": f"{self._day:02d}",
            "B": loc["months"][self._month - 1],
            "b": loc["months"][self._month - 1][:3],
            "A": loc["weekdays"][wd], "a": loc["weekdays"][wd][:3],
            "j": f"{self.day_of_year():03d}", "E": loc["era"], "%": "%",
        }
        return re.sub(r"%(.)", lambda mo: table.get(mo.group(1), mo.group(0)), fmt)

    def __format__(self, spec: str) -> str:
        return str(self) if not spec else self.strftime(spec)

    # -- developer conveniences (apps, counters, converters) ----------------

    def replace(self, *, year: int | None = None, month: int | None = None,
                day: int | None = None) -> "HijriDate":
        """A copy with selected fields replaced (same calendar)."""
        return HijriDate(
            self._year if year is None else year,
            self._month if month is None else month,
            self._day if day is None else day,
            calendar=self._calendar,
        )

    @classmethod
    def fromisoformat(cls, text: str, calendar=None) -> "HijriDate":
        """Strict ``YYYY-MM-DD`` parser (companion to :meth:`isoformat`)."""
        try:
            y, m, d = (int(p) for p in text.split("-"))
        except ValueError:
            raise ParseError(f"Expected 'YYYY-MM-DD', got {text!r}.") from None
        return cls(y, m, d, calendar=calendar)

    def to_dict(self, lang: str | None = None) -> dict:
        """A JSON-friendly dict -- handy for APIs and converter UIs."""
        return {
            "year": self._year,
            "month": self._month,
            "day": self._day,
            "iso": self.isoformat(),
            "gregorian": self.to_gregorian().isoformat(),
            "jdn": self._jdn,
            "weekday_index": self.weekday(),
            "weekday": self.weekday_name(lang),
            "month_name": self.month_name(lang),
            "method": self.method,
            "holiday": self.holiday(lang),
        }

    def days_until(self, other) -> int:
        """Whole days from this date to ``other`` (a HijriDate or a ``date``).

        Negative if ``other`` is in the past -- ideal for countdown widgets.
        """
        if isinstance(other, HijriDate):
            return other._jdn - self._jdn
        if isinstance(other, date):
            return gregorian_to_jdn(other.year, other.month, other.day) - self._jdn
        raise TypeError("days_until expects a HijriDate or datetime.date")

    def age_in_years(self, on=None) -> int:
        """Completed Hijri years from this (birth) date to ``on`` (default today)."""
        if on is None:
            on = HijriDate.today(calendar=self._calendar)
        elif isinstance(on, date):
            on = HijriDate.from_date(on, calendar=self._calendar)
        years = on._year - self._year
        if (on._month, on._day) < (self._month, self._day):
            years -= 1
        return years

    @classmethod
    def range(cls, start: "HijriDate", end: "HijriDate", step: int = 1):
        """Iterate HijriDates from ``start`` (inclusive) to ``end`` (exclusive)."""
        from .tools import hijri_range
        return hijri_range(start, end, step)

    # -- arithmetic & comparison --------------------------------------------

    def __add__(self, days: int) -> "HijriDate":
        if not isinstance(days, int):
            return NotImplemented
        return HijriDate.from_jdn(self._jdn + days, calendar=self._calendar)

    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, int):
            return HijriDate.from_jdn(self._jdn - other, calendar=self._calendar)
        if isinstance(other, HijriDate):
            return self._jdn - other._jdn
        if isinstance(other, date):
            return self._jdn - gregorian_to_jdn(other.year, other.month, other.day)
        return NotImplemented

    def __eq__(self, other) -> bool:
        return isinstance(other, HijriDate) and self._jdn == other._jdn

    def __lt__(self, other):
        if not isinstance(other, HijriDate):
            return NotImplemented
        return self._jdn < other._jdn

    def __le__(self, other):
        if not isinstance(other, HijriDate):
            return NotImplemented
        return self._jdn <= other._jdn

    def __gt__(self, other):
        if not isinstance(other, HijriDate):
            return NotImplemented
        return self._jdn > other._jdn

    def __ge__(self, other):
        if not isinstance(other, HijriDate):
            return NotImplemented
        return self._jdn >= other._jdn

    def __hash__(self) -> int:
        return hash(("HijriDate", self._jdn))

    def __str__(self) -> str:
        return self.format("{day} {month_name} {year} {era}")

    def __repr__(self) -> str:
        return f"HijriDate({self._year}, {self._month}, {self._day}, calendar={self._calendar.name!r})"


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

def from_gregorian(year: int, month: int, day: int, calendar=None) -> HijriDate:
    """Gregorian -> :class:`HijriDate` (shorthand for :meth:`HijriDate.from_gregorian`)."""
    return HijriDate.from_gregorian(year, month, day, calendar=calendar)


def to_gregorian(year: int, month: int, day: int, calendar=None) -> date:
    """Hijri (year, month, day) -> Gregorian ``date``."""
    return HijriDate(year, month, day, calendar=calendar).to_gregorian()


def parse(text: str, calendar=None) -> HijriDate:
    """Parse a Hijri date string -> :class:`HijriDate`."""
    return HijriDate.parse(text, calendar=calendar)


def today(calendar=None) -> HijriDate:
    """Today's Hijri date (civil)."""
    return HijriDate.today(calendar=calendar)
