"""Religious days, localization and parsing."""

from __future__ import annotations

from hijrical import (
    HijriDate,
    available_languages,
    month_name,
    register_locale,
    year_holidays,
)
from hijrical.calendars import ArithmeticCalendar
from hijrical.holidays import holiday_key
from hijrical.parsing import month_from_name, parse_fields

from .util import assert_raises


def test_holiday_keys():
    assert holiday_key(1, 1) == "new_year"
    assert holiday_key(9, 27) == "laylat_al_qadr"
    assert holiday_key(12, 10) == "eid_al_adha"
    assert holiday_key(12, 13) == "eid_al_adha"  # 4th day
    assert holiday_key(5, 5) is None


def test_holiday_localized():
    assert HijriDate(1447, 9, 27).holiday("tr") == "Kadir Gecesi"
    assert HijriDate(1447, 9, 27).holiday("en") == "Laylat al-Qadr"
    assert HijriDate(1447, 12, 10).holiday("ar") == "عيد الأضحى"


def test_holy_night_is_previous_evening():
    cal = ArithmeticCalendar("kuwaiti")
    days = {d.key: d for d in year_holidays(1447, cal)}
    mawlid = days["mawlid"]
    assert mawlid.eve is not None
    assert (mawlid.gregorian - mawlid.eve).days == 1


def test_raghaib_is_friday_in_rajab():
    cal = ArithmeticCalendar("kuwaiti")
    days = {d.key: d for d in year_holidays(1447, cal)}
    raghaib = days["raghaib"]
    assert raghaib.hijri[1] == 7
    friday = HijriDate(*raghaib.hijri)
    assert friday.weekday_name() == "Friday"


def test_multiday_feast_naming():
    cal = ArithmeticCalendar("kuwaiti")
    eids = [d for d in year_holidays(1447, cal) if d.key == "eid_al_fitr"]
    assert len(eids) == 3
    assert eids[1].name("en") == "Eid al-Fitr (Day 2)"
    assert eids[1].name("tr") == "Ramazan Bayramı (2. Gün)"


def test_languages_available():
    assert set(available_languages()) >= {"en", "tr", "ar"}
    assert month_name(9, "tr") == "Ramazan"


def test_parse_fields_variants():
    assert parse_fields("1447-09-01") == (1447, 9, 1)
    assert parse_fields("1 Ramadan 1447") == (1447, 9, 1)
    assert parse_fields("Ramadan 1, 1447") == (1447, 9, 1)
    assert parse_fields("15 Ramazan 1447") == (1447, 9, 15)
    assert month_from_name("Dhu al-Hijjah") == 12
    assert month_from_name("zilhicce") == 12


def test_register_custom_locale():
    register_locale({
        "code": "xx",
        "name": "Test",
        "era": "E",
        "day_suffix": " #{n}",
        "months": tuple(f"M{i}" for i in range(1, 13)),
        "weekdays": tuple(f"W{i}" for i in range(7)),
        "holidays": {k: k.upper() for k in (
            "new_year", "ashura", "mawlid", "raghaib", "isra_miraj", "baraat",
            "ramadan_start", "laylat_al_qadr", "eid_al_fitr", "arafah", "eid_al_adha")},
    })
    assert "xx" in available_languages()
    assert HijriDate(1447, 9, 1).month_name("xx") == "M9"
    # New locale's month names become parseable too.
    assert month_from_name("M9") == 9


def test_invalid_locale_rejected():
    assert_raises(ValueError, register_locale, {"code": "bad"})
