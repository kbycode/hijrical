"""HijriDate public API."""

from __future__ import annotations

from datetime import date, datetime

from hijrical import HijriDate, from_gregorian, to_gregorian
from hijrical.calendars import ArithmeticCalendar, AstronomicalCalendar
from hijrical.exceptions import InvalidDateError

from .util import assert_raises


def test_basic_conversion():
    h = from_gregorian(2026, 6, 15)
    assert (h.year, h.month, h.day) == (1447, 12, 29)
    assert h.to_gregorian() == date(2026, 6, 15)
    assert h.isoformat() == "1447-12-29"


def test_to_gregorian_helper():
    assert to_gregorian(1447, 9, 1) == date(2026, 2, 18)


def test_round_trip():
    h = HijriDate(1447, 9, 1)
    assert HijriDate.from_date(h.to_gregorian()) == h


def test_parse_examples():
    assert HijriDate.parse("1447-09-01").to_gregorian() == date(2026, 2, 18)
    assert HijriDate.parse("15 Ramadan 1447").isoformat() == "1447-09-15"
    assert HijriDate.parse("12 Rebiülevvel 1447").month == 3


def test_format_i18n():
    h = HijriDate(1447, 9, 1)
    assert h.format("{day} {month_name} {year}") == "1 Ramadan 1447"
    assert h.format("{day} {month_name} {year}", lang="tr") == "1 Ramazan 1447"
    assert h.month_name("ar") == "رمضان"
    assert h.format("{day} {month_name} {year}, {weekday}") == "1 Ramadan 1447, Wednesday"


def test_weekday():
    assert from_gregorian(2026, 6, 15).weekday_name() == "Monday"
    assert from_gregorian(2026, 6, 15).weekday_name("tr") == "Pazartesi"


def test_arithmetic_and_comparison():
    h = HijriDate(1447, 9, 1)
    assert (h + 30).month == 10
    assert (h + 40) - h == 40
    assert HijriDate(1447, 9, 1) < HijriDate(1447, 9, 2)
    assert len({HijriDate(1447, 9, 1), HijriDate(1447, 9, 1)}) == 1


def test_immutability():
    assert_raises(AttributeError, setattr, HijriDate(1447, 9, 1), "_year", 1400)


def test_invalid_date():
    assert_raises(InvalidDateError, HijriDate, 1447, 13, 1)


def test_sunset_boundary():
    noon = HijriDate.at(datetime(2026, 6, 15, 12, 0), "istanbul")
    night = HijriDate.at(datetime(2026, 6, 15, 22, 0), "istanbul")
    assert night.jdn == noon.jdn + 1


def test_method_selection():
    h_ar = HijriDate.from_gregorian(2025, 3, 1, calendar="arithmetic")
    h_as = HijriDate.from_gregorian(2025, 3, 1, calendar=AstronomicalCalendar("mecca", "umm_al_qura"))
    assert h_ar.method == "arithmetic"
    assert h_as.method == "astronomical"
    # Both reversible.
    assert HijriDate.from_date(h_ar.to_gregorian(), calendar=ArithmeticCalendar()) == h_ar
