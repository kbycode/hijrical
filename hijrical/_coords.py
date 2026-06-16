"""
Spherical-astronomy coordinate transforms.

Small, dependency-free helpers shared by the Sun and Moon engines: obliquity
of the ecliptic, ecliptic -> equatorial conversion, sidereal time, equatorial
-> horizontal (altitude/azimuth) conversion, parallax and angular separation.

All angles are in **degrees** unless noted. Functions take/return plain floats.
"""

from __future__ import annotations

import math

_DEG = math.pi / 180.0
EARTH_RADIUS_KM = 6378.14


def _sin(d: float) -> float:
    return math.sin(d * _DEG)


def _cos(d: float) -> float:
    return math.cos(d * _DEG)


def julian_centuries(jd: float) -> float:
    """Julian centuries (T) since J2000.0 for a Julian Day ``jd``."""
    return (jd - 2451545.0) / 36525.0


def mean_obliquity(jd: float) -> float:
    """Mean obliquity of the ecliptic (deg), Meeus 22.2."""
    t = julian_centuries(jd)
    seconds = 21.448 - t * (46.8150 + t * (0.00059 - t * 0.001813))
    return 23.0 + (26.0 + seconds / 60.0) / 60.0


def nutation(jd: float) -> tuple[float, float]:
    """Approximate nutation in longitude and obliquity (deg), Meeus 22 (low precision)."""
    t = julian_centuries(jd)
    omega = 125.04452 - 1934.136261 * t
    ls = 280.4665 + 36000.7698 * t
    lm = 218.3165 + 481267.8813 * t
    dpsi = (
        -17.20 * _sin(omega)
        - 1.32 * _sin(2 * ls)
        - 0.23 * _sin(2 * lm)
        + 0.21 * _sin(2 * omega)
    ) / 3600.0
    deps = (
        9.20 * _cos(omega)
        + 0.57 * _cos(2 * ls)
        + 0.10 * _cos(2 * lm)
        - 0.09 * _cos(2 * omega)
    ) / 3600.0
    return dpsi, deps


def ecliptic_to_equatorial(
    lon: float, lat: float, obliquity: float
) -> tuple[float, float]:
    """Ecliptic (lon, lat) -> equatorial (right ascension, declination), all deg."""
    sl, cl = _sin(lon), _cos(lon)
    sb, cb = _sin(lat), _cos(lat)
    se, ce = _sin(obliquity), _cos(obliquity)
    ra = math.degrees(math.atan2(sl * ce - (sb / cb) * se, cl)) % 360.0
    dec = math.degrees(math.asin(sb * ce + cb * se * sl))
    return ra, dec


def apparent_sidereal_time(jd_ut: float) -> float:
    """Greenwich apparent sidereal time (deg) for a UT Julian Day, Meeus 12.4."""
    t = julian_centuries(jd_ut)
    gmst = (
        280.46061837
        + 360.98564736629 * (jd_ut - 2451545.0)
        + 0.000387933 * t * t
        - t * t * t / 38710000.0
    )
    dpsi, _ = nutation(jd_ut)
    eps = mean_obliquity(jd_ut) + nutation(jd_ut)[1]
    gmst += dpsi * _cos(eps)  # equation of the equinoxes
    return gmst % 360.0


def equatorial_to_horizontal(
    ra: float, dec: float, jd_ut: float, lat: float, lon: float
) -> tuple[float, float]:
    """Equatorial (ra, dec) -> local (altitude, azimuth) in deg.

    ``lon`` is **east-positive**. Azimuth is measured from the North, eastward.
    Altitude is geocentric (apply parallax separately for the Moon).
    """
    lst = (apparent_sidereal_time(jd_ut) + lon) % 360.0
    h = (lst - ra) % 360.0  # local hour angle
    sphi, cphi = _sin(lat), _cos(lat)
    sdec, cdec = _sin(dec), _cos(dec)
    ch = _cos(h)
    alt = math.degrees(math.asin(sphi * sdec + cphi * cdec * ch))
    az = math.degrees(math.atan2(_sin(h), ch * sphi - (sdec / cdec) * cphi))
    az = (az + 180.0) % 360.0
    return alt, az


def topocentric_altitude(geocentric_alt: float, distance_km: float) -> float:
    """Correct a geocentric altitude for lunar parallax -> topocentric altitude (deg).

    The Moon sits ~0.95 deg lower in the sky for a surface observer than for the
    geocentre; this matters a great deal near the horizon, where the young
    crescent is seen.
    """
    parallax = math.degrees(math.asin(EARTH_RADIUS_KM / distance_km))
    return geocentric_alt - parallax * _cos(geocentric_alt)


def angular_separation(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Great-circle angle between two equatorial positions (deg)."""
    sd = _sin(dec1) * _sin(dec2) + _cos(dec1) * _cos(dec2) * _cos(ra1 - ra2)
    sd = max(-1.0, min(1.0, sd))
    return math.degrees(math.acos(sd))
