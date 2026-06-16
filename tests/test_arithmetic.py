"""Arithmetic (tabular) calendar."""

from __future__ import annotations

from hijrical import gregorian_to_jdn, jdn_to_gregorian
from hijrical.calendars import VARIANTS, ArithmeticCalendar
from hijrical.exceptions import InvalidDateError

from .util import assert_raises


def test_epoch():
    assert jdn_to_gregorian(ArithmeticCalendar("kuwaiti").to_jdn(1, 1, 1)) == (622, 7, 19)


def test_known_reference():
    cal = ArithmeticCalendar("kuwaiti")
    assert cal.from_jdn(gregorian_to_jdn(2000, 1, 1)) == (1420, 9, 24)


def test_round_trip_all_variants():
    for name in VARIANTS:
        cal = ArithmeticCalendar(name)
        for year in range(1, 200):
            for month in range(1, 13):
                length = cal.month_length(year, month)
                for day in (1, length):
                    jdn = cal.to_jdn(year, month, day)
                    assert cal.from_jdn(jdn) == (year, month, day), name


def test_jdn_round_trip_wide():
    cal = ArithmeticCalendar("kuwaiti")
    for jdn in range(1948440, 1948440 + 500000, 17):
        y, m, d = cal.from_jdn(jdn)
        assert cal.to_jdn(y, m, d) == jdn


def test_leap_years():
    cal = ArithmeticCalendar("kuwaiti")
    assert sum(1 for y in range(1, 31) if cal.is_leap_year(y)) == 11
    assert cal.month_length(1447, 12) == 30  # leap
    assert cal.month_length(1448, 12) == 29


def test_negative_years():
    cal = ArithmeticCalendar("kuwaiti")
    assert cal.from_jdn(cal.to_jdn(-5, 6, 15)) == (-5, 6, 15)


def test_invalid():
    cal = ArithmeticCalendar("kuwaiti")
    assert_raises(InvalidDateError, cal.to_jdn, 1447, 13, 1)
    assert_raises(InvalidDateError, cal.to_jdn, 1448, 12, 30)
