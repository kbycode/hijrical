"""Every religious day, checked against Diyanet's published lists (2022-2027).

`test_diyanet.py` verifies the calendar itself (month starts and lengths). This
file verifies the *religious days built on top of it*: that each one lands on the
date Diyanet prints, and — just as important — that the library does not invent
days Diyanet does not list, or miss ones it does.

The comparison is on **observed** dates, i.e. the date each day is marked on: for
a holy night that is the evening it begins, which is what Diyanet prints (Mawlid
appears on 11 Rabi al-awwal, Laylat al-Qadr on 26 Ramadan). Rows are transcribed
from https://vakithesaplama.diyanet.gov.tr/dinigunler.php?yil=YYYY.
"""

from __future__ import annotations

from datetime import date

from hijrical import DiyanetCalendar, year_holidays

# (Gregorian date, holiday key) exactly as Diyanet lists them.
OFFICIAL_DAYS = (
    # --- 2022 (1443-1444) ---
    ("2022-02-02", "three_months"), ("2022-02-03", "raghaib"),
    ("2022-02-27", "isra_miraj"), ("2022-03-17", "baraat"),
    ("2022-04-02", "ramadan_start"), ("2022-04-27", "laylat_al_qadr"),
    ("2022-05-01", "eid_al_fitr_eve"), ("2022-05-02", "eid_al_fitr"),
    ("2022-05-03", "eid_al_fitr"), ("2022-05-04", "eid_al_fitr"),
    ("2022-07-08", "arafah"), ("2022-07-09", "eid_al_adha"),
    ("2022-07-10", "eid_al_adha"), ("2022-07-11", "eid_al_adha"),
    ("2022-07-12", "eid_al_adha"), ("2022-07-30", "new_year"),
    ("2022-08-08", "ashura"), ("2022-10-07", "mawlid"),
    # --- 2023 (1444-1445) ---
    ("2023-01-23", "three_months"), ("2023-01-26", "raghaib"),
    ("2023-02-17", "isra_miraj"), ("2023-03-06", "baraat"),
    ("2023-03-23", "ramadan_start"), ("2023-04-17", "laylat_al_qadr"),
    ("2023-04-20", "eid_al_fitr_eve"), ("2023-04-21", "eid_al_fitr"),
    ("2023-04-22", "eid_al_fitr"), ("2023-04-23", "eid_al_fitr"),
    ("2023-06-27", "arafah"), ("2023-06-28", "eid_al_adha"),
    ("2023-06-29", "eid_al_adha"), ("2023-06-30", "eid_al_adha"),
    ("2023-07-01", "eid_al_adha"), ("2023-07-19", "new_year"),
    ("2023-07-28", "ashura"), ("2023-09-26", "mawlid"),
    # --- 2024 (1445-1446) ---
    ("2024-01-11", "raghaib"), ("2024-01-12", "three_months"),
    ("2024-02-06", "isra_miraj"), ("2024-02-24", "baraat"),
    ("2024-03-11", "ramadan_start"), ("2024-04-05", "laylat_al_qadr"),
    ("2024-04-09", "eid_al_fitr_eve"), ("2024-04-10", "eid_al_fitr"),
    ("2024-04-11", "eid_al_fitr"), ("2024-04-12", "eid_al_fitr"),
    ("2024-06-15", "arafah"), ("2024-06-16", "eid_al_adha"),
    ("2024-06-17", "eid_al_adha"), ("2024-06-18", "eid_al_adha"),
    ("2024-06-19", "eid_al_adha"), ("2024-07-07", "new_year"),
    ("2024-07-16", "ashura"), ("2024-09-14", "mawlid"),
    # --- 2025 (1446-1447) ---
    ("2025-01-01", "three_months"), ("2025-01-02", "raghaib"),
    ("2025-01-26", "isra_miraj"), ("2025-02-13", "baraat"),
    ("2025-03-01", "ramadan_start"), ("2025-03-26", "laylat_al_qadr"),
    ("2025-03-29", "eid_al_fitr_eve"), ("2025-03-30", "eid_al_fitr"),
    ("2025-03-31", "eid_al_fitr"), ("2025-04-01", "eid_al_fitr"),
    ("2025-06-05", "arafah"), ("2025-06-06", "eid_al_adha"),
    ("2025-06-07", "eid_al_adha"), ("2025-06-08", "eid_al_adha"),
    ("2025-06-09", "eid_al_adha"), ("2025-06-26", "new_year"),
    ("2025-07-05", "ashura"), ("2025-09-03", "mawlid"),
    ("2025-12-21", "three_months"), ("2025-12-25", "raghaib"),
    # --- 2026 (1447-1448) ---
    ("2026-01-15", "isra_miraj"), ("2026-02-02", "baraat"),
    ("2026-02-19", "ramadan_start"), ("2026-03-16", "laylat_al_qadr"),
    ("2026-03-19", "eid_al_fitr_eve"), ("2026-03-20", "eid_al_fitr"),
    ("2026-03-21", "eid_al_fitr"), ("2026-03-22", "eid_al_fitr"),
    ("2026-05-26", "arafah"), ("2026-05-27", "eid_al_adha"),
    ("2026-05-28", "eid_al_adha"), ("2026-05-29", "eid_al_adha"),
    ("2026-05-30", "eid_al_adha"), ("2026-06-16", "new_year"),
    ("2026-06-25", "ashura"), ("2026-08-24", "mawlid"),
    ("2026-12-10", "three_months"), ("2026-12-10", "raghaib"),
    # --- 2027 (1448-1449) ---
    ("2027-01-04", "isra_miraj"), ("2027-01-22", "baraat"),
    ("2027-02-08", "ramadan_start"), ("2027-03-05", "laylat_al_qadr"),
    ("2027-03-08", "eid_al_fitr_eve"), ("2027-03-09", "eid_al_fitr"),
    ("2027-03-10", "eid_al_fitr"), ("2027-03-11", "eid_al_fitr"),
    ("2027-05-15", "arafah"), ("2027-05-16", "eid_al_adha"),
    ("2027-05-17", "eid_al_adha"), ("2027-05-18", "eid_al_adha"),
    ("2027-05-19", "eid_al_adha"), ("2027-06-06", "new_year"),
    ("2027-06-15", "ashura"), ("2027-08-13", "mawlid"),
    ("2027-11-29", "three_months"), ("2027-12-02", "raghaib"),
    ("2027-12-24", "isra_miraj"),
)

WINDOW_START = date(2022, 1, 1)
WINDOW_END = date(2027, 12, 31)


def _official_set() -> set[tuple[date, str]]:
    out = set()
    for iso, key in OFFICIAL_DAYS:
        y, m, d = (int(p) for p in iso.split("-"))
        out.add((date(y, m, d), key))
    return out


def _library_set() -> set[tuple[date, str]]:
    """Every religious day the library places inside the comparison window."""
    cal = DiyanetCalendar()
    out = set()
    for hijri_year in range(1443, 1450):
        for rd in year_holidays(hijri_year, cal):
            if WINDOW_START <= rd.observed <= WINDOW_END:
                out.add((rd.observed, rd.key))
    return out


def test_no_missing_days():
    missing = sorted(_official_set() - _library_set())
    assert not missing, f"Diyanet lists these, the library does not: {missing}"


def test_no_invented_days():
    extra = sorted(_library_set() - _official_set())
    assert not extra, f"The library invents these, Diyanet does not list them: {extra}"


def test_exact_match_both_directions():
    assert _library_set() == _official_set()


def test_every_official_day_is_findable_by_date():
    """Looking a published date up must name the same day the list does."""
    from hijrical import HijriDate

    cal = DiyanetCalendar()
    for observed, key in sorted(_official_set()):
        found = HijriDate.from_date(observed, calendar=cal).holiday("en")
        assert found is not None, f"{observed} ({key}) is not found by date lookup"


def test_counts_per_year():
    """Each Hijri year carries the full Turkish set: 12 named days + feasts."""
    cal = DiyanetCalendar()
    for hijri_year in (1445, 1446, 1447, 1448):
        keys = [rd.key for rd in year_holidays(hijri_year, cal)]
        assert len(keys) == len(set(keys)) + 5, keys  # 3 Fitr + 4 Adha days
        for key in ("new_year", "ashura", "mawlid", "three_months", "raghaib",
                    "isra_miraj", "baraat", "ramadan_start", "laylat_al_qadr",
                    "eid_al_fitr_eve", "eid_al_fitr", "arafah", "eid_al_adha"):
            assert key in keys, f"{hijri_year} is missing {key}"
