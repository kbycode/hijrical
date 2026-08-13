"""
hijrical -- accurate, location-aware Hijri <-> Gregorian date conversion.

Highlights
----------
* **Two engines.** ``ArithmeticCalendar`` is exact, reversible and unbounded in
  range; ``AstronomicalCalendar`` predicts real crescent visibility for a given
  location and criterion.
* **Location matters.** The same new moon can be visible in Mecca but not yet in
  Istanbul -- which is why Ramadan sometimes starts a day later in Türkiye than
  in the Gulf. ``AstronomicalCalendar(observer, criterion)`` models exactly this.
* **Sunset day boundary.** The Islamic day starts at maghrib;
  :meth:`HijriDate.at` returns the correct date for an instant + location.
* **i18n.** English, Turkish and Arabic out of the box, easily extended with
  :func:`register_locale`.
* **Zero dependencies.** Pure Python standard library.

Quick start
-----------
>>> from hijrical import HijriDate, from_gregorian, to_gregorian
>>> from_gregorian(2026, 6, 15)
HijriDate(1447, 12, 29, calendar='arithmetic')
>>> to_gregorian(1447, 9, 1)
datetime.date(2026, 2, 18)
>>> HijriDate(1447, 9, 1).format("{day} {month_name} {year}", lang="tr")
'1 Ramazan 1447'
"""

from __future__ import annotations

from ._julian import gregorian_to_jdn, jdn_to_gregorian, jdn_weekday
from ._sun import sunrise, sunset
from .calendars import (
    VARIANTS,
    ArithmeticCalendar,
    AstronomicalCalendar,
    Calendar,
)
from .core import (
    HijriDate,
    from_gregorian,
    parse,
    to_gregorian,
    today,
)
from .criteria import (
    CrescentInfo,
    Criterion,
    available_criteria,
    compute_crescent,
    get_criterion,
)
from .diyanet import DIYANET_MONTH_STARTS, DiyanetCalendar, official_range
from .exceptions import (
    HijriError,
    InvalidDateError,
    LocationRequiredError,
    OutOfRangeError,
    ParseError,
)
from .holidays import ReligiousDay, holiday_key, year_holidays
from .locales import (
    available_languages,
    get_locale,
    month_name,
    register_locale,
    weekday_name,
)
from .observer import DEFAULT_OBSERVER, PRESETS, Observer
from .tools import (
    days_in_month,
    days_until_holiday,
    hijri_range,
    iter_month,
    month_calendar,
    next_holiday,
    next_occurrence,
    upcoming_holidays,
)

__version__ = "1.2.0"

__all__ = [
    # core
    "HijriDate",
    "from_gregorian",
    "to_gregorian",
    "parse",
    "today",
    # engines
    "Calendar",
    "ArithmeticCalendar",
    "AstronomicalCalendar",
    "DiyanetCalendar",
    "DIYANET_MONTH_STARTS",
    "official_range",
    "VARIANTS",
    # location & visibility
    "Observer",
    "PRESETS",
    "DEFAULT_OBSERVER",
    "Criterion",
    "CrescentInfo",
    "compute_crescent",
    "get_criterion",
    "available_criteria",
    "sunset",
    "sunrise",
    # holidays
    "ReligiousDay",
    "year_holidays",
    "holiday_key",
    # app-builder conveniences
    "hijri_range",
    "iter_month",
    "month_calendar",
    "days_in_month",
    "next_occurrence",
    "next_holiday",
    "upcoming_holidays",
    "days_until_holiday",
    # i18n
    "register_locale",
    "available_languages",
    "get_locale",
    "month_name",
    "weekday_name",
    # julian
    "gregorian_to_jdn",
    "jdn_to_gregorian",
    "jdn_weekday",
    # exceptions
    "HijriError",
    "InvalidDateError",
    "OutOfRangeError",
    "LocationRequiredError",
    "ParseError",
    "__version__",
]
