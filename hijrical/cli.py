"""
Command-line interface: ``python -m hijrical`` (or ``hijrical`` once installed).

Examples
--------
    hijrical today
    hijrical g2h 2026-06-15
    hijrical h2g 1447-09-01
    hijrical h2g "15 Ramadan 1447" --lang tr
    hijrical g2h 2026-02-18 --method astronomical --observer istanbul --criterion ircica
    hijrical holidays 1447 --lang tr
    hijrical compare 1447 9 1            # Ramadan start across locations
    hijrical at "2026-06-15T22:00" --observer istanbul
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from . import __version__
from .calendars import ArithmeticCalendar, AstronomicalCalendar
from .core import HijriDate
from .holidays import year_holidays
from .observer import PRESETS, resolve_observer
from .parsing import parse_fields


def _build_calendar(args):
    if args.method == "diyanet":
        from .diyanet import DiyanetCalendar
        return DiyanetCalendar()
    if args.method == "astronomical":
        return AstronomicalCalendar(args.observer, args.criterion, scope=args.scope)
    return ArithmeticCalendar(args.variant)


def _emit(h: HijriDate, args) -> None:
    if getattr(args, "json", False):
        print(json.dumps(h.to_dict(args.lang), ensure_ascii=False, indent=2))
        return
    lang = args.lang
    print(f"  Hijri    : {h.format('{day} {month_name} {year} {era}', lang=lang)} "
          f"({h.weekday_name(lang)})")
    print(f"  ISO      : {h.isoformat()}   [method: {h.method}]")
    print(f"  Gregorian: {h.to_gregorian().isoformat()}")
    holiday = h.holiday(lang)
    if holiday:
        print(f"  Holiday  : * {holiday}")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    # Common options usable before *or* after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--lang", default="en", help="Output language (en, tr, ar, ...).")
    common.add_argument("--method", default="arithmetic",
                        choices=["arithmetic", "astronomical", "diyanet"])
    common.add_argument("--variant", default="kuwaiti", help="Arithmetic variant.")
    common.add_argument("--observer", default="mecca", help="Observer/location key.")
    common.add_argument("--criterion", default="ircica", help="Visibility criterion.")
    common.add_argument("--scope", default="local", choices=["local", "global"],
                        help="Astronomical scope: local observer or worldwide land.")
    common.add_argument("--json", action="store_true", help="Emit JSON instead of text.")

    p = argparse.ArgumentParser(
        prog="hijrical", parents=[common],
        description="Accurate Hijri <-> Gregorian conversion.")
    p.add_argument("--version", action="version", version=f"hijrical {__version__}")

    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("today", parents=[common], help="Today's Hijri date.")
    s = sub.add_parser("g2h", parents=[common], help="Gregorian -> Hijri (YYYY-MM-DD).")
    s.add_argument("date")
    s = sub.add_parser("h2g", parents=[common], help="Hijri -> Gregorian (string or YYYY-MM-DD).")
    s.add_argument("date")
    s = sub.add_parser("holidays", parents=[common], help="Religious days of a Hijri year.")
    s.add_argument("year", type=int)
    s = sub.add_parser("at", parents=[common], help="Sunset-aware Hijri date for an instant + location.")
    s.add_argument("instant", help="YYYY-MM-DD or YYYY-MM-DDTHH:MM")
    s = sub.add_parser("compare", parents=[common], help="Compare a Hijri date across locations.")
    s.add_argument("year", type=int)
    s.add_argument("month", type=int)
    s.add_argument("day", type=int)
    s = sub.add_parser("next", parents=[common], help="Upcoming religious days with countdowns.")
    s.add_argument("--count", type=int, default=8)
    s.add_argument("--key", default=None, help="Filter to one holiday key.")
    s = sub.add_parser("calendar", parents=[common], help="Print a Hijri month as a grid.")
    s.add_argument("year", type=int)
    s.add_argument("month", type=int)

    args = p.parse_args(argv)
    cal = _build_calendar(args)
    lang = args.lang

    if args.command == "today":
        _emit(HijriDate.today(calendar=cal), args)

    elif args.command == "g2h":
        y, m, d = (int(x) for x in args.date.replace("/", "-").replace(".", "-").split("-"))
        _emit(HijriDate.from_gregorian(y, m, d, calendar=cal), args)

    elif args.command == "h2g":
        y, m, d = parse_fields(args.date)
        _emit(HijriDate(y, m, d, calendar=cal), args)

    elif args.command == "holidays":
        print(f"Religious days of {args.year} AH (method: {args.method}):")
        has_night = False
        for r in year_holidays(args.year, cal):
            mark = " (*)" if r.is_holy_night else ""
            has_night = has_night or r.is_holy_night
            print(f"  {r.observed.isoformat()}  {r.name(lang)}{mark}")
        if has_night:
            print("  (*) holy night: starts at sunset on the date shown.")

    elif args.command == "at":
        text = args.instant.replace("T", " ")
        try:
            instant = datetime.fromisoformat(text)
        except ValueError:
            y, m, d = parse_fields(args.instant)
            instant = datetime(y, m, d, 23, 0)
        h = HijriDate.at(instant, args.observer, calendar=cal)
        if not args.json:
            print(f"Instant {instant.isoformat()} at {args.observer}:")
        _emit(h, args)

    elif args.command == "compare":
        y, m, d = args.year, args.month, args.day
        from .diyanet import DiyanetCalendar
        arith = HijriDate(y, m, d, calendar=ArithmeticCalendar(args.variant))
        diy = DiyanetCalendar()
        glob = AstronomicalCalendar("mecca", "ircica", scope="global")
        print(f"Hijri {y}-{m:02d}-{d:02d} in Gregorian, by method/location:")
        print(f"  arithmetic                 : {arith.to_gregorian().isoformat()}")
        tag = "official" if diy.is_official(y, m) else "predicted"
        print(f"  Diyanet (Türkiye)          : "
              f"{HijriDate(y, m, d, calendar=diy).to_gregorian().isoformat()}  [{tag}]")
        print(f"  global/ircica (unified)    : "
              f"{HijriDate(y, m, d, calendar=glob).to_gregorian().isoformat()}")
        for key in ("mecca", "istanbul", "jakarta", "rabat"):
            obs = resolve_observer(key)
            for crit in ("umm_al_qura", "ircica"):
                hd = HijriDate(y, m, d, calendar=AstronomicalCalendar(obs, crit))
                print(f"  {obs.name:<14} {crit:<12}: {hd.to_gregorian().isoformat()}")

    elif args.command == "next":
        from .core import HijriDate as _HD
        from .tools import upcoming_holidays
        ref = _HD.today(calendar=cal)
        items = upcoming_holidays(count=args.count, calendar=cal, key=args.key)
        if args.json:
            out = [{"name": r.name(lang), "key": r.key, "gregorian": r.gregorian.isoformat(),
                    "days_until": ref.days_until(r.gregorian),
                    "eve": r.eve.isoformat() if r.eve else None} for r in items]
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(f"Upcoming religious days (from {ref.to_gregorian().isoformat()}):")
            for r in items:
                days = ref.days_until(r.gregorian)
                print(f"  {r.gregorian.isoformat()}  in {days:>4} days  {r.name(lang)}")

    elif args.command == "calendar":
        from .locales import get_locale
        from .tools import month_calendar
        loc = get_locale(lang)
        title = HijriDate(args.year, args.month, 1, calendar=cal)
        print(f"{title.month_name(lang)} {args.year} ({title.format('{month_name}', lang='en')})")
        print(" ".join(f"{d[:2]:>2}" for d in loc["weekdays"]))
        for week in month_calendar(args.year, args.month, calendar=cal):
            print(" ".join(f"{c.day:>2}" if c else "  " for c in week))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
