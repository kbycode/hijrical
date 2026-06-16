"""Crescent visibility engine and criteria."""

from __future__ import annotations

from datetime import date

from hijrical import compute_crescent, get_criterion, gregorian_to_jdn, sunset
from hijrical._moon import new_moon_jd_ut
from hijrical.observer import resolve_observer

from .util import assert_raises


def _nearest_new_moon(g_date: date) -> float:
    k = round((gregorian_to_jdn(g_date.year, g_date.month, g_date.day)
               - 2451550.09766) / 29.530588861)
    return new_moon_jd_ut(k)


def test_crescent_info_fields_sane():
    obs = resolve_observer("mecca")
    ss = sunset(date(2026, 2, 18), obs.latitude, obs.longitude, obs.utc_offset)
    info = compute_crescent(obs, ss, _nearest_new_moon(date(2026, 2, 18)))
    assert -90 <= info.altitude <= 90
    assert 0 <= info.elongation <= 180
    assert info.width_arcmin >= 0


def test_criteria_resolution():
    assert get_criterion("ircica").min_elongation == 8.0
    assert get_criterion("ircica").min_altitude == 5.0
    assert get_criterion("mabims").min_elongation == 6.4
    assert get_criterion("turkey").name == "ircica"
    assert get_criterion("umm_al_qura").name == "umm_al_qura"
    assert_raises(ValueError, get_criterion, "nope")


def test_ircica_stricter_than_conjunction():
    # For the same circumstances, IRCICA (8/5) should never be MORE permissive
    # than the bare conjunction rule.
    obs = resolve_observer("istanbul")
    ss = sunset(date(2026, 2, 17), obs.latitude, obs.longitude, obs.utc_offset)
    info = compute_crescent(obs, ss, _nearest_new_moon(date(2026, 2, 17)))
    ircica = get_criterion("ircica").is_visible(info)
    conjunction = get_criterion("conjunction").is_visible(info)
    assert not (ircica and not conjunction)
