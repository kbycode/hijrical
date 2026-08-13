"""App-builder conveniences: ranges, calendars, countdowns, formatting."""

from __future__ import annotations

from datetime import date

from hijrical import (
    HijriDate,
    days_in_month,
    days_until_holiday,
    hijri_range,
    iter_month,
    month_calendar,
    next_holiday,
    next_occurrence,
    upcoming_holidays,
)
from hijrical.exceptions import ParseError

from .util import assert_raises


def test_strftime_and_fstring():
    h = HijriDate(1447, 9, 1)
    assert h.strftime("%d %B %Y (%A)") == "01 Ramadan 1447 (Wednesday)"
    assert h.strftime("%d.%m.%Y") == "01.09.1447"
    assert f"{h:%d %B %Y}" == "01 Ramadan 1447"
    assert f"{h}" == str(h)
    assert h.strftime("%A", lang="tr") == "Çarşamba"


def test_replace_and_fromisoformat():
    h = HijriDate(1447, 9, 1)
    assert h.replace(day=15).isoformat() == "1447-09-15"
    assert h.replace(month=1, day=1).isoformat() == "1447-01-01"
    assert HijriDate.fromisoformat("1447-09-15") == HijriDate(1447, 9, 15)
    assert_raises(ParseError, HijriDate.fromisoformat, "not-a-date")


def test_to_dict():
    # 26 Ramadan is the evening Laylat al-Qadr (27 Ramadan) begins, so that is
    # where calendars mark it.
    d = HijriDate(1447, 9, 26).to_dict("en")
    assert d["iso"] == "1447-09-26"
    assert d["holiday"] == "Laylat al-Qadr"
    assert d["month_name"] == "Ramadan"


def test_days_until_and_age():
    a, b = HijriDate(1447, 9, 1), HijriDate(1447, 9, 30)
    assert a.days_until(b) == 29
    assert b.days_until(a) == -29
    assert a.days_until(date(2026, 2, 18)) == 0  # a is 2026-02-18
    assert HijriDate(1400, 6, 15).age_in_years(HijriDate(1447, 6, 15)) == 47
    assert HijriDate(1400, 6, 15).age_in_years(HijriDate(1447, 6, 14)) == 46


def test_day_of_year():
    assert HijriDate(1447, 1, 1).day_of_year() == 1
    # Day-of-year of 1 Ramadan = sum of months 1..8 lengths + 1.
    expected = sum(HijriDate(1447, m, 1).month_length() for m in range(1, 9)) + 1
    assert HijriDate(1447, 9, 1).day_of_year() == expected


def test_hijri_range():
    days = [d.day for d in hijri_range(HijriDate(1447, 9, 1), HijriDate(1447, 9, 5))]
    assert days == [1, 2, 3, 4]
    down = [d.day for d in hijri_range(HijriDate(1447, 9, 5), HijriDate(1447, 9, 2), step=-1)]
    assert down == [5, 4, 3]
    assert_raises(ValueError, lambda: list(hijri_range(HijriDate(1447, 9, 1), HijriDate(1447, 9, 2), step=0)))


def test_month_calendar():
    weeks = month_calendar(1447, 9)
    assert all(len(w) == 7 for w in weeks)
    flat = [c for w in weeks for c in w if c is not None]
    assert [c.day for c in flat] == list(range(1, days_in_month(1447, 9) + 1))
    # Leading pad equals the weekday of day 1.
    assert weeks[0].index(flat[0]) == HijriDate(1447, 9, 1).weekday()


def test_iter_month():
    days = iter_month(1447, 9)
    assert len(days) == days_in_month(1447, 9)
    assert days[0] == HijriDate(1447, 9, 1)


def test_next_occurrence():
    nxt = next_occurrence(9, 1, after=HijriDate(1447, 10, 1))
    assert nxt.year == 1448 and nxt.month == 9 and nxt.day == 1
    # Same date passed as 'after' rolls to next year (strictly after).
    assert next_occurrence(9, 1, after=HijriDate(1447, 9, 1)).year == 1448


def test_upcoming_and_countdown():
    after = date(2026, 2, 1)
    nh = next_holiday(after=after, key="ramadan_start")
    assert nh is not None and nh.gregorian == date(2026, 2, 18)
    assert days_until_holiday("ramadan_start", after=after) == 17
    several = upcoming_holidays(count=3, after=after, key="ramadan_start")
    assert len(several) == 3
    assert all(r.key == "ramadan_start" for r in several)
    assert several[0].gregorian < several[1].gregorian
