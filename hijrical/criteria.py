"""
Crescent-visibility engine and criteria.

This is what makes location matter: the very same astronomical new moon can be
*visible* from one place and *not yet* from another, which is exactly why
Ramadan (or a feast) sometimes begins a day later in Türkiye than in the Gulf.

:func:`compute_crescent` works out, for a given observer and the sunset of a
candidate evening, the quantities crescent-visibility criteria care about:

* **elongation** (arc of light, ARCL) -- Sun-Moon angular separation,
* **altitude** -- the Moon's topocentric altitude at sunset,
* **arc of vision** (ARCV) -- Moon altitude minus Sun altitude,
* **moon age** -- time since conjunction,
* **lag** -- how long after the Sun the Moon sets,
* **width** -- the crescent's illuminated width.

A :class:`Criterion` then turns those numbers into a yes/no decision. Several
established criteria are bundled; the default is **Türkiye / IRCICA**.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from ._coords import (
    angular_separation,
    apparent_sidereal_time,
    ecliptic_to_equatorial,
    equatorial_to_horizontal,
    mean_obliquity,
    nutation,
    topocentric_altitude,
    EARTH_RADIUS_KM,
)
from ._moon import delta_t_seconds, moon_position
from ._sun import datetime_to_jd_ut, sun_position

_DEG = math.pi / 180.0
_MOON_RADIUS_KM = 1737.4
# Moon's hour angle increases ~14.49 deg/hr (sidereal rate minus its own motion).
_MOON_HA_RATE_DEG_PER_HR = 14.492


@dataclass(frozen=True)
class CrescentInfo:
    """Geometric circumstances of a crescent at a given sunset."""

    observer_name: str
    sunset: datetime
    elongation: float          #: ARCL, Sun-Moon separation (deg)
    altitude: float            #: Moon topocentric altitude at sunset (deg)
    arc_of_vision: float       #: ARCV, Moon alt minus Sun alt (deg)
    relative_azimuth: float    #: DAZ, Moon azimuth minus Sun azimuth (deg)
    age_hours: float           #: hours from conjunction to sunset
    lag_minutes: float         #: minutes from sunset to moonset (negative if before)
    width_arcmin: float        #: crescent illuminated width (arcminutes)

    def __str__(self) -> str:
        return (
            f"{self.observer_name}: elong={self.elongation:.2f} deg, "
            f"alt={self.altitude:.2f} deg, ARCV={self.arc_of_vision:.2f} deg, "
            f"age={self.age_hours:.1f} h, lag={self.lag_minutes:.0f} min, "
            f"width={self.width_arcmin:.2f}'"
        )


def compute_crescent(
    observer, sunset_dt: datetime, conjunction_jd_ut: float
) -> CrescentInfo:
    """Compute crescent circumstances for ``observer`` at ``sunset_dt``.

    ``conjunction_jd_ut`` is the UT Julian Day of the relevant new moon.
    """
    jd_ut = datetime_to_jd_ut(sunset_dt)
    year = 2000.0 + (jd_ut - 2451545.0) / 365.25
    jde = jd_ut + delta_t_seconds(year) / 86400.0

    eps = mean_obliquity(jde) + nutation(jde)[1]
    lat, lon = observer.latitude, observer.longitude

    # Sun
    _, sun_ra, sun_dec = sun_position(jde)
    sun_alt, sun_az = equatorial_to_horizontal(sun_ra, sun_dec, jd_ut, lat, lon)

    # Moon
    moon_lon, moon_lat, dist = moon_position(jde)
    moon_ra, moon_dec = ecliptic_to_equatorial(moon_lon, moon_lat, eps)
    geo_alt, moon_az = equatorial_to_horizontal(moon_ra, moon_dec, jd_ut, lat, lon)
    moon_alt = topocentric_altitude(geo_alt, dist)

    elongation = angular_separation(sun_ra, sun_dec, moon_ra, moon_dec)
    arcv = moon_alt - sun_alt
    daz = ((moon_az - sun_az + 180.0) % 360.0) - 180.0
    age_hours = (jd_ut - conjunction_jd_ut) * 24.0

    semidiameter = math.degrees(math.asin(_MOON_RADIUS_KM / dist)) * 60.0
    width = semidiameter * (1.0 - math.cos(elongation * _DEG))

    lag = _moonset_lag_minutes(moon_ra, moon_dec, dist, jd_ut, lat, lon)

    return CrescentInfo(
        observer_name=observer.name,
        sunset=sunset_dt,
        elongation=elongation,
        altitude=moon_alt,
        arc_of_vision=arcv,
        relative_azimuth=daz,
        age_hours=age_hours,
        lag_minutes=lag,
        width_arcmin=width,
    )


def _moonset_lag_minutes(
    ra: float, dec: float, dist_km: float, jd_ut: float, lat: float, lon: float
) -> float:
    """Estimate minutes from sunset to moonset (analytic, ~minute accuracy)."""
    parallax = math.degrees(math.asin(EARTH_RADIUS_KM / dist_km))
    h0 = 0.7275 * parallax - 0.5667  # altitude of Moon centre at moonset
    cphi, sphi = math.cos(lat * _DEG), math.sin(lat * _DEG)
    cdec, sdec = math.cos(dec * _DEG), math.sin(dec * _DEG)
    denom = cphi * cdec
    if denom == 0:
        return 0.0
    cos_h0 = (math.sin(h0 * _DEG) - sphi * sdec) / denom
    if cos_h0 < -1.0 or cos_h0 > 1.0:
        # Moon is circumpolar or never rises that night.
        return 999.0 if cos_h0 < -1.0 else -999.0
    set_ha = math.degrees(math.acos(cos_h0))  # west setting hour angle
    lst = (apparent_sidereal_time(jd_ut) + lon) % 360.0
    current_ha = ((lst - ra + 180.0) % 360.0) - 180.0
    delta = ((set_ha - current_ha + 180.0) % 360.0) - 180.0
    return delta / _MOON_HA_RATE_DEG_PER_HR * 60.0


# ---------------------------------------------------------------------------
# Visibility criteria
# ---------------------------------------------------------------------------

class Criterion:
    """Base class: decide whether a crescent is visible from a :class:`CrescentInfo`."""

    name = "base"
    description = ""

    def is_visible(self, info: CrescentInfo) -> bool:  # pragma: no cover - abstract
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<Criterion {self.name}>"


class ConjunctionCriterion(Criterion):
    """Simplest rule: the crescent counts once conjunction is before sunset.

    Ignores true visibility; useful as a fast, transparent baseline (close to
    the Umm al-Qura *calendar* rule without the moonset check).
    """

    name = "conjunction"
    description = "Conjunction occurs before sunset (moon age > 0)."

    def is_visible(self, info: CrescentInfo) -> bool:
        return info.age_hours > 0.0


class MoonsetLagCriterion(Criterion):
    """Umm al-Qura style: the Moon sets after the Sun and conjunction precedes sunset."""

    name = "umm_al_qura"
    description = "Moon sets after the Sun (lag > 0) and conjunction before sunset."

    def is_visible(self, info: CrescentInfo) -> bool:
        return info.age_hours > 0.0 and info.lag_minutes > 0.0


class AltitudeElongationCriterion(Criterion):
    """Visible if elongation and Moon altitude both clear given thresholds."""

    def __init__(self, min_elongation: float, min_altitude: float, name: str,
                 description: str = "") -> None:
        self.min_elongation = min_elongation
        self.min_altitude = min_altitude
        self.name = name
        self.description = description or (
            f"Elongation >= {min_elongation} deg and altitude >= {min_altitude} deg."
        )

    def is_visible(self, info: CrescentInfo) -> bool:
        return (
            info.age_hours > 0.0
            and info.elongation >= self.min_elongation
            and info.altitude >= self.min_altitude
        )


class OdehCriterion(Criterion):
    """Mohammad Odeh's (2004) crescent-visibility test using ARCV and crescent width.

    Computes ``q = ARCV - f(W)`` and compares against a threshold. The default
    threshold ``-0.96`` corresponds to "visible, possibly needing optical aid".
    """

    name = "odeh"

    def __init__(self, threshold: float = -0.96) -> None:
        self.threshold = threshold
        self.description = (
            f"Odeh (2004) q-test, threshold q > {threshold} "
            "(>5.65 easy naked eye, >2 naked eye, >-0.96 optical aid)."
        )

    def is_visible(self, info: CrescentInfo) -> bool:
        if info.age_hours <= 0.0:
            return False
        w = info.width_arcmin
        f = -0.1018 * w ** 3 + 0.7319 * w ** 2 - 6.3226 * w + 7.1651
        q = info.arc_of_vision - f
        return q > self.threshold


# Built-in named criteria. ``ircica`` is the library default.
_CRITERIA = {
    "ircica": lambda: AltitudeElongationCriterion(
        8.0, 5.0, "ircica",
        "Türkiye / IRCICA unified calendar: elongation >= 8 deg, altitude >= 5 deg.",
    ),
    "turkey": lambda: AltitudeElongationCriterion(
        8.0, 5.0, "ircica",
        "Türkiye / IRCICA unified calendar: elongation >= 8 deg, altitude >= 5 deg.",
    ),
    "mabims": lambda: AltitudeElongationCriterion(
        6.4, 3.0, "mabims",
        "MABIMS (Southeast Asia): elongation >= 6.4 deg, altitude >= 3 deg.",
    ),
    "umm_al_qura": MoonsetLagCriterion,
    "conjunction": ConjunctionCriterion,
    "odeh": OdehCriterion,
}

DEFAULT_CRITERION = "ircica"


def get_criterion(criterion: "Criterion | str") -> Criterion:
    """Resolve a :class:`Criterion` instance or a name to a Criterion."""
    if isinstance(criterion, Criterion):
        return criterion
    key = str(criterion).strip().lower()
    try:
        factory = _CRITERIA[key]
    except KeyError:
        options = ", ".join(sorted(_CRITERIA))
        raise ValueError(
            f"Unknown criterion: {criterion!r}. Available: {options}."
        ) from None
    return factory()


def available_criteria() -> list[str]:
    """Names of the built-in criteria."""
    return sorted(_CRITERIA)
