"""
Solar astronomy: the Sun's apparent position and sunrise / sunset times.

Sunset matters twice in this library:

* it is the **Islamic day boundary** (a new day begins at maghrib), and
* it is the reference moment at which **crescent visibility** is judged.

The sunrise/sunset routine is the well-known NOAA solar-position algorithm,
implemented in pure Python; accuracy is on the order of a minute at ordinary
latitudes -- more than enough for a calendar day boundary.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone

from ._coords import mean_obliquity, nutation
from ._julian import gregorian_to_jdn

_DEG = math.pi / 180.0

# Standard zenith for sunrise/sunset: 90 deg 50' = 90.833 deg, accounting for
# atmospheric refraction (~34') and the Sun's semidiameter (~16').
_OFFICIAL_ZENITH = 90.833


def _sin(d: float) -> float:
    return math.sin(d * _DEG)


def _cos(d: float) -> float:
    return math.cos(d * _DEG)


def datetime_to_jd_ut(dt: datetime) -> float:
    """Convert a timezone-aware ``datetime`` to a UT Julian Day (float)."""
    if dt.tzinfo is None:
        raise ValueError("datetime_to_jd_ut requires a timezone-aware datetime")
    u = dt.astimezone(timezone.utc)
    frac = (u.hour + u.minute / 60.0 + (u.second + u.microsecond / 1e6) / 3600.0) / 24.0
    return gregorian_to_jdn(u.year, u.month, u.day) - 0.5 + frac


def sun_position(jde: float) -> tuple[float, float, float]:
    """Apparent solar position at ``jde`` (TT Julian Day).

    Returns ``(apparent_longitude_deg, right_ascension_deg, declination_deg)``.
    """
    t = (jde - 2451545.0) / 36525.0
    l0 = 280.46646 + t * (36000.76983 + t * 0.0003032)
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    c = (
        (1.914602 - t * (0.004817 + 0.000014 * t)) * _sin(m)
        + (0.019993 - 0.000101 * t) * _sin(2 * m)
        + 0.000289 * _sin(3 * m)
    )
    true_lon = l0 + c
    omega = 125.04 - 1934.136 * t
    app_lon = true_lon - 0.00569 - 0.00478 * _sin(omega)
    eps = mean_obliquity(jde) + 0.00256 * _cos(omega)
    ra = math.degrees(math.atan2(_cos(eps) * _sin(app_lon), _cos(app_lon))) % 360.0
    dec = math.degrees(math.asin(_sin(eps) * _sin(app_lon)))
    return app_lon % 360.0, ra, dec


def sunset(
    on: date, latitude: float, longitude: float, utc_offset_hours: float = 0.0
) -> datetime | None:
    """Sunset (start of maghrib) for a date and location.

    ``longitude`` is **east-positive**. ``utc_offset_hours`` is the local time
    zone's offset from UTC. Returns a timezone-aware ``datetime``, or ``None`` if
    the Sun does not set that day (polar regions).
    """
    return _horizon_event(on, latitude, longitude, utc_offset_hours, setting=True)


def sunrise(
    on: date, latitude: float, longitude: float, utc_offset_hours: float = 0.0
) -> datetime | None:
    """Sunrise for a date and location (see :func:`sunset`)."""
    return _horizon_event(on, latitude, longitude, utc_offset_hours, setting=False)


def _horizon_event(
    on: date,
    latitude: float,
    longitude: float,
    tz_hours: float,
    *,
    setting: bool,
) -> datetime | None:
    if on.month <= 2:
        y, mo = on.year - 1, on.month + 12
    else:
        y, mo = on.year, on.month
    a = y // 100
    b = 2 - a + a // 4
    jd = (
        math.floor(365.25 * (y + 4716))
        + math.floor(30.6001 * (mo + 1))
        + on.day + b - 1524.5
    )
    jc = (jd - 2451545.0) / 36525.0

    gml = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360.0
    gma = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    ecc = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    gma_r = gma * _DEG
    center = (
        math.sin(gma_r) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
        + math.sin(2 * gma_r) * (0.019993 - 0.000101 * jc)
        + math.sin(3 * gma_r) * 0.000289
    )
    true_lon = gml + center
    omega = 125.04 - 1934.136 * jc
    app_lon = true_lon - 0.00569 - 0.00478 * _sin(omega)
    obl = mean_obliquity(jd) + 0.00256 * _cos(omega)
    decl = math.degrees(math.asin(_sin(obl) * _sin(app_lon)))

    yy = math.tan((obl / 2.0) * _DEG) ** 2
    eot = 4.0 * math.degrees(
        yy * math.sin(2 * gml * _DEG)
        - 2 * ecc * math.sin(gma_r)
        + 4 * ecc * yy * math.sin(gma_r) * math.cos(2 * gml * _DEG)
        - 0.5 * yy * yy * math.sin(4 * gml * _DEG)
        - 1.25 * ecc * ecc * math.sin(2 * gma_r)
    )

    lat_r = latitude * _DEG
    decl_r = decl * _DEG
    cos_ha = (_cos(_OFFICIAL_ZENITH) - math.sin(lat_r) * math.sin(decl_r)) / (
        math.cos(lat_r) * math.cos(decl_r)
    )
    if cos_ha > 1.0 or cos_ha < -1.0:
        return None
    ha = math.degrees(math.acos(cos_ha))

    noon_min = 720.0 - 4.0 * longitude - eot + tz_hours * 60.0
    event_min = noon_min + (4.0 * ha if setting else -4.0 * ha)
    tz = timezone(timedelta(hours=tz_hours))
    start = datetime(on.year, on.month, on.day, tzinfo=tz)
    return start + timedelta(minutes=event_min)
