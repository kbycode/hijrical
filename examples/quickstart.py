#!/usr/bin/env python
"""
hijrical quickstart -- a tour of the main features.

Run it with:  python examples/quickstart.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

# Allow running straight from a checkout (no installation needed).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hijrical import (
    AstronomicalCalendar,
    HijriDate,
    days_until_holiday,
    from_gregorian,
    month_calendar,
    next_holiday,
    to_gregorian,
    year_holidays,
)
from hijrical.calendars import ArithmeticCalendar


def section(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    section("Basic conversion")
    print("2026-06-15  ->", from_gregorian(2026, 6, 15))
    print("1447-09-01  ->", to_gregorian(1447, 9, 1), "(start of Ramadan)")

    section("Parsing & localized formatting")
    h = HijriDate.parse("15 Ramadan 1447")
    for lang in ("en", "tr", "ar"):
        print(f"  [{lang}]", h.format("{day} {month_name} {year} {era}, {weekday}", lang=lang))

    section("Sunset (maghrib) day boundary in Istanbul")
    print("  12:00 ->", HijriDate.at(datetime(2026, 6, 15, 12, 0), "istanbul").isoformat())
    print("  22:00 ->", HijriDate.at(datetime(2026, 6, 15, 22, 0), "istanbul").isoformat(),
          "(after sunset: next Hijri day)")

    section("Where does Ramadan 1447 begin? (location matters)")
    rows = [
        ("arithmetic", ArithmeticCalendar()),
        ("Mecca / umm_al_qura", AstronomicalCalendar("mecca", "umm_al_qura")),
        ("Istanbul / ircica (local)", AstronomicalCalendar("istanbul", "ircica")),
        ("Global / ircica (unified)", AstronomicalCalendar("mecca", "ircica", scope="global")),
    ]
    for label, cal in rows:
        print(f"  {label:<28}: {HijriDate(1447, 9, 1, calendar=cal).to_gregorian()}")

    section("Religious days of 1447 (Turkish names)")
    for d in year_holidays(1447, ArithmeticCalendar())[:6]:
        eve = f"  (night begins {d.eve})" if d.eve else ""
        print(f"  {d.gregorian}  {d.name('tr')}{eve}")

    section("Countdown (special-day counter)")
    nh = next_holiday(key="ramadan_start")
    print(f"  Next Ramadan: {nh.gregorian} ({nh.name('tr')})")
    print(f"  Days until Ramadan: {days_until_holiday('ramadan_start')}")

    section("Month grid for Ramadan 1447 (calendar app)")
    print("  " + " ".join(f"{w[:2]:>2}" for w in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")))
    for week in month_calendar(1447, 9):
        print("  " + " ".join(f"{c.day:>2}" if c else "  " for c in week))


if __name__ == "__main__":
    main()
