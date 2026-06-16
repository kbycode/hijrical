"""
Observer / geographic location for sunset and crescent-visibility calculations.

Because sunset (and therefore the Islamic day boundary and the moment a crescent
becomes visible) depends on geography, location-aware calculations take an
:class:`Observer`. A handful of presets are provided for convenience.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Observer:
    """A geographic observing location.

    Attributes
    ----------
    name : str
        Human-readable label.
    latitude : float
        Degrees, north positive.
    longitude : float
        Degrees, **east positive**, west negative.
    utc_offset : float
        Local time-zone offset from UTC, in hours (e.g. ``3`` for Türkiye).
    elevation : float
        Height above sea level in metres (currently informational).
    """

    name: str
    latitude: float
    longitude: float
    utc_offset: float
    elevation: float = 0.0

    @classmethod
    def preset(cls, key: str) -> "Observer":
        """Return a built-in observer by key, e.g. ``Observer.preset("istanbul")``."""
        try:
            return PRESETS[_normalize(key)]
        except KeyError:
            options = ", ".join(sorted(PRESETS))
            raise KeyError(
                f"Unknown observer preset: {key!r}. Available: {options}. "
                "Or build one with Observer(name, latitude, longitude, utc_offset)."
            ) from None


def _normalize(key: str) -> str:
    return (
        str(key).strip().lower()
        .replace("İ", "i").replace("ı", "i")
        .replace("ş", "s").replace("ç", "c").replace("ö", "o")
        .replace("ü", "u").replace("ğ", "g").replace(" ", "_")
    )


#: Built-in observers (key -> Observer). Extend freely in your own code.
PRESETS: dict[str, Observer] = {
    "mecca": Observer("Mecca", 21.422487, 39.826206, 3.0, 277.0),
    "medina": Observer("Medina", 24.4672, 39.6111, 3.0, 620.0),
    "istanbul": Observer("İstanbul", 41.0082, 28.9784, 3.0, 40.0),
    "ankara": Observer("Ankara", 39.9334, 32.8597, 3.0, 938.0),
    "izmir": Observer("İzmir", 38.4237, 27.1428, 3.0, 25.0),
    "cairo": Observer("Cairo", 30.0444, 31.2357, 2.0, 23.0),
    "jakarta": Observer("Jakarta", -6.2088, 106.8456, 7.0, 8.0),
    "kuala_lumpur": Observer("Kuala Lumpur", 3.1390, 101.6869, 8.0, 56.0),
    "jerusalem": Observer("Jerusalem", 31.7683, 35.2137, 2.0, 754.0),
    "london": Observer("London", 51.5074, -0.1278, 0.0, 11.0),
    "new_york": Observer("New York", 40.7128, -74.0060, -5.0, 10.0),
    "rabat": Observer("Rabat", 34.0209, -6.8417, 1.0, 46.0),
}

# Common aliases.
PRESETS["mekke"] = PRESETS["mecca"]
PRESETS["medine"] = PRESETS["medina"]
PRESETS["kudus"] = PRESETS["jerusalem"]

#: The default reference observer for astronomical calculations (Mecca).
DEFAULT_OBSERVER = PRESETS["mecca"]


def resolve_observer(observer: "Observer | str") -> Observer:
    """Accept either an :class:`Observer` or a preset key and return an Observer."""
    if isinstance(observer, Observer):
        return observer
    return Observer.preset(observer)
