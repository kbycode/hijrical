# hijrical 🌙

**Accurate, location-aware Hijri ⇄ Gregorian date conversion for Python.**

A modern, professional alternative to `hijridate` — without its limitations and
with the things it lacks: an *unbounded* exact calendar, real **crescent
visibility** that depends on **where you are**, the **sunset day boundary**, and
**internationalization** (English / Turkish / Arabic, easily extended).

[![PyPI](https://img.shields.io/pypi/v/hijrical)](https://pypi.org/project/hijrical/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/kbycode/hijrical/actions/workflows/ci.yml/badge.svg)](https://github.com/kbycode/hijrical/actions/workflows/ci.yml)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](pyproject.toml)
[![Live demo](https://img.shields.io/badge/▶_Live_demo-hijrical_Studio-2dd4bf)](https://kbycode.github.io/hijrical-studio/)

```python
from hijrical import HijriDate, from_gregorian, to_gregorian

from_gregorian(2026, 6, 15)          # HijriDate(1447, 12, 29, calendar='arithmetic')
to_gregorian(1447, 9, 1)             # datetime.date(2026, 2, 18)
HijriDate.parse("15 Ramadan 1447")   # parse human input
```

> 🌙 **Try every feature in your browser — [hijrical Studio](https://kbycode.github.io/hijrical-studio/).**
> An interactive playground (converter, Hijri/Gregorian dual calendar, crescent
> visibility, religious days) that runs **fully client-side** via Pyodide — no
> install. Source: [kbycode/hijrical-studio](https://github.com/kbycode/hijrical-studio).

---

## Why hijrical?

| | `hijridate` | **hijrical** |
|---|---|---|
| Date range | **1343–1500 AH only** (1924–2077) | Arithmetic: **unbounded**; astronomical: 1–1600 AH |
| Methods | One (Umm al-Qura table) | **Arithmetic** + **astronomical/visibility** |
| Location-aware | ❌ | ✅ Istanbul and Mecca can differ by a day |
| Sunset (maghrib) day boundary | ❌ | ✅ `HijriDate.at(instant, place)` |
| Reversible | table-bound | **Pure-integer, exact round-trip** |
| Religious days / holy nights | ❌ | ✅ with i18n + correct night eves |
| Languages | English | **en / tr / ar**, pluggable |
| Dependencies | none | none |

> `hijridate` is backed by the Umm al-Qura **table**, so it only works for
> 1924–2077 and raises outside it. hijrical's arithmetic engine is pure integer
> math: it works for **any** date and round-trips perfectly. On top of that,
> hijrical adds a real astronomical engine that models crescent visibility per
> location — the thing that actually decides when a Hijri month begins.

---

## Installation

```bash
pip install hijrical
```

Zero dependencies, pure Python 3.9+. The package also works straight from a
checkout (`import hijrical` with the folder on your path).

---

## Quick start

```python
from hijrical import HijriDate, from_gregorian, to_gregorian

# Gregorian -> Hijri
h = from_gregorian(2026, 6, 15)
print(h)                       # 29 Dhu al-Hijjah 1447 AH
print(h.isoformat())           # 1447-12-29
print(h.to_gregorian())        # 2026-06-15

# Hijri -> Gregorian
print(to_gregorian(1447, 9, 1))               # 2026-02-18  (start of Ramadan)

# Parse anything reasonable
HijriDate.parse("1447-09-01")
HijriDate.parse("15 Ramadan 1447")
HijriDate.parse("12 Rebiülevvel 1447")        # Turkish month name
HijriDate.parse("١ رمضان ١٤٤٧")               # Arabic digits + name

# Formatting & localization
h = HijriDate(1447, 9, 1)
h.format("{day} {month_name} {year}")               # '1 Ramadan 1447'
h.format("{day} {month_name} {year}", lang="tr")    # '1 Ramazan 1447'
h.format("{day} {month_name} {year} {era}", lang="ar")  # '1 رمضان 1447 هـ'

# Arithmetic & comparison
h + 30                          # 30 days later, as a HijriDate
HijriDate(1447, 12, 29) - HijriDate(1447, 9, 1)   # day difference (int)
```

---

## The two engines

```python
from hijrical import ArithmeticCalendar, AstronomicalCalendar, HijriDate

# Arithmetic (default): exact, reversible, unbounded
HijriDate(1447, 9, 1, calendar=ArithmeticCalendar("kuwaiti"))

# Astronomical: real crescent visibility for a place + criterion
HijriDate(1447, 9, 1, calendar=AstronomicalCalendar("istanbul", "ircica"))
```

| Engine | Use it for | Guarantee |
|---|---|---|
| `ArithmeticCalendar` | civil/database use, history, anything needing a stable, reversible mapping | Mathematically exact; same input → same output, forever |
| `AstronomicalCalendar` | predicting real religious dates as observed somewhere | A close **prediction**; may differ ±1 day from official decrees |

Arithmetic variants: `kuwaiti` (default, Type II / Microsoft), `type1`,
`type3`, `type4`, `kuwaiti_astronomical`.

---

## 🌍 Location-based crescent visibility (the interesting part)

A Hijri month begins when the new crescent (*hilal*) is **seen** — and whether
it can be seen depends on **where you stand**. Right after the astronomical new
moon the crescent is thin and low; from one city it clears the horizon by
sunset, from another it does not. That is exactly why **Ramadan sometimes starts
a day later in Türkiye than in Saudi Arabia.**

hijrical models this directly. For a given `Observer` and `Criterion` it computes
the Moon's real position at sunset and decides visibility:

```python
from hijrical import HijriDate, AstronomicalCalendar

ramadan = lambda obs, crit: HijriDate(
    1447, 9, 1, calendar=AstronomicalCalendar(obs, crit)
).to_gregorian()

ramadan("mecca",    "umm_al_qura")   # 2026-02-18
ramadan("istanbul", "ircica")        # 2026-02-19   ← one day later
ramadan("jakarta",  "mabims")        # 2026-02-19
```

Or from the command line:

```text
$ hijrical compare 1447 9 1
Hijri 1447-09-01 in Gregorian, by method/location:
  arithmetic            : 2026-02-18
  Mecca      umm_al_qura: 2026-02-18
  Mecca      ircica     : 2026-02-19
  İstanbul   umm_al_qura: 2026-02-18
  İstanbul   ircica     : 2026-02-19
  Jakarta    umm_al_qura: 2026-02-19
  Jakarta    ircica     : 2026-02-19
  Rabat      umm_al_qura: 2026-02-18
  Rabat      ircica     : 2026-02-19
```

### What the engine actually computes

For the sunset of each candidate evening it derives, from a full Meeus lunar +
solar model (validated to arc-seconds against Meeus' own worked example):

- **elongation** (arc of light) — Sun–Moon separation,
- **altitude** — the Moon's *topocentric* altitude (parallax-corrected; the Moon
  sits ~0.95° lower for a surface observer, which matters near the horizon),
- **arc of vision** (ARCV) — Moon altitude minus Sun altitude,
- **moon age** — time since conjunction,
- **lag** — how long after the Sun the Moon sets,
- **crescent width** — illuminated width in arcminutes.

You can inspect these yourself:

```python
from datetime import date
from hijrical import compute_crescent, sunset
from hijrical.observer import resolve_observer
from hijrical._moon import new_moon_jd_ut

obs = resolve_observer("istanbul")
ss = sunset(date(2026, 2, 17), obs.latitude, obs.longitude, obs.utc_offset)
info = compute_crescent(obs, ss, new_moon_jd_ut(323))
print(info)   # elong=…, alt=…, ARCV=…, age=…, lag=…, width=…
```

### Built-in criteria

| Criterion | Rule | Notes |
|---|---|---|
| `ircica` *(default)* | elongation ≥ 8°, altitude ≥ 5° | Türkiye / IRCICA unified-calendar thresholds |
| `mabims` | elongation ≥ 6.4°, altitude ≥ 3° | Southeast Asia (Indonesia/Malaysia/Brunei/Singapore) |
| `umm_al_qura` | Moon sets after the Sun (lag > 0) and conjunction before sunset | close to the Saudi official calendar |
| `odeh` | Odeh (2004) ARCV vs crescent-width *q*-test | naked-eye / optical zones |
| `conjunction` | conjunction before sunset | simplest baseline |

Bring your own:

```python
from hijrical.criteria import AltitudeElongationCriterion
from hijrical import AstronomicalCalendar

my_rule = AltitudeElongationCriterion(min_elongation=7.0, min_altitude=4.0, name="custom")
AstronomicalCalendar("ankara", my_rule)
```

### Local vs. global ("unified") calendars

The criteria above judge visibility **at the observer's own location**. Some
national calendars (e.g. Türkiye's official *Türkiye Takvimi*, adopted in 2016)
instead use a **global** rule: the month turns over for everyone once the
crescent is visible *anywhere* on Earth within certain bounds. hijrical supports
both via the `scope` argument:

```python
from hijrical import AstronomicalCalendar, HijriDate

local  = AstronomicalCalendar("istanbul", "ircica")                  # "is it visible here?"
global_ = AstronomicalCalendar("mecca", "ircica", scope="global")    # "is it visible anywhere?"

HijriDate(1447, 9, 1, calendar=local).to_gregorian()    # 2026-02-19
HijriDate(1447, 9, 1, calendar=global_).to_gregorian()  # 2026-02-18  (the world has seen it)
```

The global mode samples a worldwide grid of locations at their local sunsets and
declares the crescent seen as soon as any of them satisfies the criterion. It is
therefore never *later* than a single-location result, and it approximates the
"unified" calendars used by several authorities. For matching a specific
authority exactly, pick the engine/criterion closest to its policy
(`umm_al_qura` for Saudi Arabia, `scope="global"` + `ircica` for a Türkiye-style
unified calendar) and treat results as predictions — the final word always
belongs to the official sighting/announcement.

---

## 🌇 Sunset (maghrib) day boundary

The Islamic day begins at **sunset**, not midnight — so the eve of a feast is
already, religiously, the feast's first night. `HijriDate.at()` handles this:

```python
from datetime import datetime
from hijrical import HijriDate

HijriDate.at(datetime(2026, 6, 15, 12, 0), "istanbul").isoformat()  # '1447-12-29'
HijriDate.at(datetime(2026, 6, 15, 22, 0), "istanbul").isoformat()  # '1447-12-30'
```

The same idea drives **holy-night eves** in the holidays API (below).

---

## 🕌 Religious days

```python
from hijrical import year_holidays, ArithmeticCalendar

for d in year_holidays(1447, ArithmeticCalendar("kuwaiti")):
    print(d.gregorian, d.name(lang="tr"), "| night:", d.eve)
```

Covers Islamic New Year, Ashura, Mawlid, Raghaib (first Friday eve of Rajab),
Isra & Mi'raj, Mid-Sha'ban, Ramadan, Laylat al-Qadr, Eid al-Fitr (3 days),
Arafah and Eid al-Adha (4 days). Holy nights carry an `eve` (the Gregorian
evening the night begins). A single date's holiday:

```python
HijriDate(1447, 9, 27).holiday("en")   # 'Laylat al-Qadr'
HijriDate(1447, 9, 27).holiday("tr")   # 'Kadir Gecesi'
```

---

## 🧰 Recipes for app builders

Everything you need for **calendar apps, countdown widgets and converters**.

**Format dates (strftime-style, works in f-strings):**

```python
h = HijriDate(1447, 9, 1)
h.strftime("%d %B %Y (%A)")      # '01 Ramadan 1447 (Wednesday)'
f"{h:%d.%m.%Y}"                  # '01.09.1447'
h.strftime("%d %B %Y", lang="tr")
```

**Iterate and lay out a month grid:**

```python
from hijrical import hijri_range, iter_month, month_calendar

for d in hijri_range(HijriDate(1447, 9, 1), HijriDate(1447, 10, 1)):
    ...                                  # every day of Ramadan 1447

weeks = month_calendar(1447, 9)          # list of weeks, Monday-first
for week in weeks:                       # each week is 7 cells (HijriDate or None)
    print(" ".join(f"{c.day:2}" if c else "  " for c in week))
```

**Countdowns and special-day counters:**

```python
from hijrical import next_holiday, days_until_holiday, next_occurrence

days_until_holiday("ramadan_start")      # e.g. 247  (days from today)
nh = next_holiday(key="eid_al_fitr")     # next Eid al-Fitr as a ReligiousDay
print(nh.gregorian, nh.name("tr"))

next_occurrence(1, 1)                    # next Islamic New Year (annual recurrence)
HijriDate.today().days_until(nh.gregorian)   # generic day countdown
```

**Serialize for an API / converter UI:**

```python
HijriDate(1447, 9, 27).to_dict("tr")
# {'year': 1447, 'month': 9, 'day': 27, 'iso': '1447-09-27',
#  'gregorian': '2026-03-16', 'jdn': 2461116, 'weekday_index': 0,
#  'weekday': 'Pazartesi', 'month_name': 'Ramazan', 'method': 'arithmetic',
#  'holiday': 'Kadir Gecesi'}
```

**Misc helpers:** `HijriDate.fromisoformat("1447-09-01")`, `.replace(day=15)`,
`.day_of_year()`, `.age_in_years(birth_on)`, `days_in_month(year, month)`.

On the command line:

```bash
hijrical calendar 1447 9 --lang tr      # print a month grid
hijrical next --lang tr --count 8       # upcoming religious days with countdowns
hijrical next --key ramadan_start       # next start of Ramadan
hijrical g2h 2026-03-16 --json          # machine-readable output
```

---

## 🌐 Internationalization

Three languages ship in the box; adding one is a dictionary:

```python
from hijrical import register_locale, HijriDate

register_locale({
    "code": "fr", "name": "Français", "era": "AH", "day_suffix": " (jour {n})",
    "months": ("Mouharram", "Safar", "Rabi al-awwal", "Rabi al-thani",
               "Joumada al-oula", "Joumada al-thania", "Rajab", "Chaabane",
               "Ramadan", "Chawwal", "Dhou al-qida", "Dhou al-hijja"),
    "weekdays": ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"),
    "holidays": { "new_year": "Nouvel an hégirien", "ramadan_start": "Début du Ramadan",
                  # … the remaining keys …
    },
})

HijriDate(1447, 9, 1).format("{day} {month_name} {year}", lang="fr")  # '1 Ramadan 1447'
```

Newly registered month names become parseable automatically.

---

## 🖥️ Command line

```bash
hijrical today
hijrical g2h 2026-06-15
hijrical h2g "15 Ramadan 1447" --lang tr
hijrical g2h 2026-02-18 --method astronomical --observer istanbul --criterion ircica
hijrical holidays 1447 --lang tr
hijrical compare 1447 9 1
hijrical at "2026-06-15T22:00" --observer istanbul
```

(Use `python -m hijrical …` if the script isn't on your PATH.)

---

## API reference (essentials)

| Symbol | Purpose |
|---|---|
| `HijriDate(year, month, day, calendar=None)` | Construct a Hijri date |
| `HijriDate.from_gregorian(y, m, d, calendar=None)` / `from_gregorian(...)` | Gregorian → Hijri |
| `HijriDate.from_jdn(jdn)` / `from_date(date)` | From JDN / `date` |
| `HijriDate.parse(text)` / `parse(text)` | Parse a string |
| `HijriDate.today()` | Now (civil) |
| `HijriDate.at(instant, observer)` | Sunset-aware date |
| `.to_gregorian()` / `to_gregorian(y, m, d)` | Hijri → Gregorian `date` |
| `.format(pattern, lang)` / `.isoformat()` | Formatting |
| `.month_name(lang)` / `.weekday_name(lang)` | Localized names |
| `.holiday(lang)` | Religious-day name or `None` |
| `.month_length()` / `.year_length()` / `.is_leap_year()` | Calendar info |
| `ArithmeticCalendar(variant)` | Tabular engine |
| `AstronomicalCalendar(observer, criterion, scope="local"\|"global")` | Visibility engine (local or unified) |
| `Observer(name, latitude, longitude, utc_offset)` | A location |
| `compute_crescent(observer, sunset, conj_jd)` → `CrescentInfo` | Visibility geometry |
| `get_criterion(name)` / `available_criteria()` | Criteria |
| `year_holidays(year, calendar)` | Religious days of a year |
| `hijri_range(start, end, step)` / `HijriDate.range(...)` | Iterate dates |
| `month_calendar(year, month)` / `iter_month(...)` | Month grid / days |
| `next_occurrence(month, day, after)` | Next annual recurrence |
| `next_holiday(after, key)` / `upcoming_holidays(...)` / `days_until_holiday(...)` | Countdowns |
| `.strftime(fmt)` / `f"{d:%d %B %Y}"` / `.to_dict()` | Formatting & serialization |
| `.days_until(other)` / `.age_in_years(on)` / `.replace(...)` / `.fromisoformat(...)` | Date math |
| `register_locale(dict)` / `available_languages()` | i18n |

`.format()` fields: `{year} {month} {day} {month02} {day02} {month_name}
{weekday} {era} {method}`.

---

## Accuracy & validation

- **JDN round-trip:** 0 errors over hundreds of thousands of random dates.
- **Arithmetic round-trip:** 0 errors across all variants and a 600k-day sweep.
- **Lunar model:** matches Meeus' worked example 47.a to ~0.00004° in longitude;
  distance and latitude exact to the quoted precision.
- **Umm al-Qura:** the `mecca` + `umm_al_qura` configuration reproduces seven
  official anchor dates (Ramadan starts and both Eids) exactly.
- 54 unit tests + 25 doctests, including round-trips, the location/`scope`
  behaviour, i18n and the app-builder helpers. Run them with
  `python run_tests.py` (no pytest needed) or `pytest`.

> **Disclaimer.** Astronomical/visibility results are predictions. Actual
> religious dates depend on local moon sighting and the rulings of competent
> authorities (e.g. Diyanet İşleri Başkanlığı). Use the arithmetic engine when
> you need determinism and reversibility.

---

## License

MIT — see [LICENSE](LICENSE).
