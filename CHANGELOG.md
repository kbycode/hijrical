# Changelog

All notable changes to **hijrical** are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-06-16

### Added
- App-builder conveniences for calendars, counters and converters:
  - `hijri_range`, `iter_month`, `days_in_month`, `month_calendar` (week grid).
  - `next_occurrence`, `next_holiday`, `upcoming_holidays`, `days_until_holiday`.
- `HijriDate` gains `strftime` (and `__format__`, so `f"{d:%d %B %Y}"` works),
  `to_dict` (JSON-friendly), `replace`, `fromisoformat`, `day_of_year`,
  `days_until`, `age_in_years` and `HijriDate.range`.
- CLI: `--json` output, plus `next` (upcoming days with countdowns) and
  `calendar` (month grid) commands.

## [1.0.0] - 2026-06-15

### Added
- `HijriDate`: immutable, comparable, hashable Hijri date with arithmetic,
  formatting, ISO output, weekday/month names and religious-day lookup.
- Two interchangeable engines:
  - `ArithmeticCalendar` — exact, reversible tabular calendar with five
    leap-year variants and unbounded date range.
  - `AstronomicalCalendar` — location- and criterion-aware crescent-visibility
    calendar (months are always 29 or 30 days).
- Crescent-visibility engine (`compute_crescent`, `CrescentInfo`) computing
  elongation, altitude, arc of vision, moon age, moonset lag and crescent width
  from a full Meeus lunar/solar model.
- Visibility criteria: `ircica` (default), `mabims`, `umm_al_qura`,
  `conjunction`, `odeh`.
- Global / "unified" calendar mode via `AstronomicalCalendar(..., scope="global")`,
  which declares a month begun once the crescent is visible anywhere on Earth
  (approximating national unified calendars such as the Türkiye Takvimi).
- `HijriDate.at()` — sunset-aware (maghrib) day boundary for an instant + place.
- `Observer` with built-in city presets.
- Forgiving `parse()` understanding ISO strings and month names in any
  registered language.
- Internationalization (`en`, `tr`, `ar`) with `register_locale()` for adding
  more languages.
- Religious-day calendar including holy-night eves (`year_holidays`).
- Command-line interface (`hijrical` / `python -m hijrical`) with `today`,
  `g2h`, `h2g`, `holidays`, `at` and `compare`.
- Zero runtime dependencies; ships `py.typed`.
