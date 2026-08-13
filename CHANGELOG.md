# Changelog

All notable changes to **hijrical** are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.2.1] - 2026-08-13

### Fixed
- **Astronomical drift.** Month starts were derived from the previous month and
  clamped to 29/30 days, so small errors accumulated: ~150 months past the
  anchor the calendar had slipped more than **two weeks**. Each month is now
  anchored to its own conjunction and only then clamped, which removes the drift
  entirely. Measured against the official Umm al-Qura table (1440-1455, all 192
  month starts):

  | engine | before | after |
  |---|---|---|
  | `mecca` / `umm_al_qura` | 80.7%, up to 15 days out | **99.0%, never more than 1 day** |
  | global / `ircica` | 71.9%, up to 15 days out | **89.6%, never more than 1 day** |

  `DiyanetCalendar` was unaffected inside its published range (it reads the
  official table), but its fallback years were, as were long-range uses of the
  astronomical engine.

### Added
- `tools/update_diyanet_table.py` — rebuilds the official table from Diyanet's
  saved pages when they publish further years, verifying contiguity and 29/30
  month lengths before emitting anything.

## [1.2.0] - 2026-08-13

### Added
- **`DiyanetCalendar`** — Turkey's official Hijri calendar, backed by Diyanet's
  published tables (1443-06 … 1449-08, i.e. 2022-2027), verified row by row
  against 160 official Hijri/Gregorian pairs. Outside that range it falls back
  to the astronomical unified engine; `coverage()` / `is_official()` say which.
  Also selectable as `calendar="diyanet"` and `--method diyanet`.
- `ReligiousDay.observed` — the date a day is actually **published/observed** on.
  For holy nights that is the eve, which is how Diyanet (and others) print
  kandils: Mi'raj appears on 26 Rajab, the evening 27 Rajab begins.
- Religious days now include `three_months` (1 Rajab) and `eid_al_fitr_eve`
  (last day of Ramadan), completing the official Turkish list.
- `--scope {local,global}` on the CLI.

### Fixed
- **Global scope now honours the land rule.** The 2016 Istanbul congress counts
  a crescent only if it is visible over land; sightings falling on open ocean
  are disregarded. The previous grid accepted mid-Pacific points and so started
  some months a day early. Agreement with Diyanet's official anchors went from
  9/10 to 10/10 on the 2025 table.
- Localized holiday names fall back to English when a third-party locale
  predates a holiday key, instead of raising `KeyError`.

### Changed
- Guidance corrected: for Turkey use `DiyanetCalendar` (exact), or
  `AstronomicalCalendar("mecca", "ircica", scope="global")` for years beyond the
  published tables. A *local* observer with `ircica` is **not** the Turkish rule
  and matched only 5 of 10 official anchors.

## [1.1.1] - 2026-06-16

### Fixed
- Corrected the project metadata URLs (Homepage / Repository / Issues) to the
  real repository, and added Repository and Changelog links.

### Changed
- Packaging/repository housekeeping: added CI and Trusted-Publishing release
  workflows, `.gitattributes`, and PyPI/CI badges. No code or API changes.

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
