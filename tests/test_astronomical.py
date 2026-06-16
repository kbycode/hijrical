"""Astronomical / visibility calendar and the lunar engine."""

from __future__ import annotations

from hijrical import gregorian_to_jdn, jdn_to_gregorian
from hijrical._moon import moon_position, new_moon_jd_ut
from hijrical.calendars import AstronomicalCalendar
from hijrical.exceptions import OutOfRangeError

from .util import assert_raises

# Official Umm al-Qura anchors (Hijri -> Gregorian).
UMM_AL_QURA = [
    ((1443, 1, 1), (2021, 8, 9)),
    ((1444, 9, 1), (2023, 3, 23)),
    ((1444, 10, 1), (2023, 4, 21)),
    ((1445, 1, 1), (2023, 7, 19)),
    ((1446, 1, 1), (2024, 7, 7)),
    ((1446, 9, 1), (2025, 3, 1)),
    ((1446, 10, 1), (2025, 3, 30)),
]


def test_moon_position_meeus_example():
    # Meeus example 47.a: 1992-04-12 0h TD (JDE 2448724.5).
    lon, lat, dist = moon_position(2448724.5)
    assert abs(lon - 133.16727) < 0.001
    assert abs(lat - (-3.22913)) < 0.001
    assert abs(dist - 368409.7) < 1.0


def test_new_moon_reference():
    jd = new_moon_jd_ut(0)  # 2000-01-06 ~18:14 UT
    y, m, d = jdn_to_gregorian(int(jd + 0.5))
    frac = (jd + 0.5) - int(jd + 0.5)
    assert (y, m, d) == (2000, 1, 6)
    assert abs(frac * 24 - 18.23) < 0.3


def test_umm_al_qura_anchors():
    cal = AstronomicalCalendar("mecca", "umm_al_qura")
    for hijri, greg in UMM_AL_QURA:
        got = jdn_to_gregorian(cal.to_jdn(*hijri))
        diff = gregorian_to_jdn(*got) - gregorian_to_jdn(*greg)
        assert diff == 0, f"{hijri}: {got} vs {greg}"


def test_months_are_29_or_30():
    cal = AstronomicalCalendar("istanbul", "ircica")
    for year in range(1443, 1452):
        for month in range(1, 13):
            assert cal.month_length(year, month) in (29, 30)


def test_round_trip():
    cal = AstronomicalCalendar("istanbul", "ircica")
    for year in range(1443, 1452):
        for month in range(1, 13):
            length = cal.month_length(year, month)
            for day in (1, length):
                jdn = cal.to_jdn(year, month, day)
                assert cal.from_jdn(jdn) == (year, month, day)


def test_location_matters():
    # Istanbul/IRCICA should differ from Mecca/UmmAlQura in at least one Ramadan.
    ist = AstronomicalCalendar("istanbul", "ircica")
    mec = AstronomicalCalendar("mecca", "umm_al_qura")
    diffs = [
        ist.to_jdn(y, 9, 1) - mec.to_jdn(y, 9, 1) for y in range(1443, 1450)
    ]
    assert any(d != 0 for d in diffs)
    assert all(abs(d) <= 2 for d in diffs)


def test_out_of_range():
    cal = AstronomicalCalendar("mecca", "umm_al_qura")
    assert_raises(OutOfRangeError, cal.to_jdn, 3000, 1, 1)


def test_global_scope_months_and_round_trip():
    glob = AstronomicalCalendar("mecca", "ircica", scope="global")
    for year in range(1444, 1450):
        for month in range(1, 13):
            length = glob.month_length(year, month)
            assert length in (29, 30)
            for day in (1, length):
                assert glob.from_jdn(glob.to_jdn(year, month, day)) == (year, month, day)


def test_global_no_later_than_local():
    # "Visible anywhere" can only make a month start earlier than (or same as) a
    # single local observer.
    glob = AstronomicalCalendar("mecca", "ircica", scope="global")
    local = AstronomicalCalendar("istanbul", "ircica")
    for year in range(1444, 1450):
        assert glob.to_jdn(year, 9, 1) <= local.to_jdn(year, 9, 1)


def test_modern_conversion_does_not_overbuild_chain():
    # Regression: from_jdn must estimate from the modern anchor, not from year 1
    # AH, so converting a present-day date stays cheap.
    cal = AstronomicalCalendar("mecca", "ircica", scope="global")
    cal.to_jdn(1447, 9, 1)
    cal.from_jdn(gregorian_to_jdn(2026, 2, 18))
    assert len(cal._starts) < 200
