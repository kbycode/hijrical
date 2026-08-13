"""
Inhabited-land sample used by the global ("unified calendar") visibility scope.

Unified Hijri calendars do not accept a crescent that is only theoretically
visible in the middle of an ocean: the 2016 Istanbul congress explicitly
evaluated sighting chances **over land** (notably the American continent) and
disregarded sightings that fall on open sea only. Sampling real inhabited
places is therefore not a shortcut -- it is part of the rule, and it is what
makes the global scope reproduce official calendars such as Diyanet's.

The sample is deliberately a list of well-known cities rather than a raster
land mask: every entry is independently verifiable, and no point can silently
fall in the sea. Crescent visibility zones span thousands of kilometres, so a
worldwide spread of this density resolves the day boundary reliably.

``LAND_POINTS`` holds ``(name, latitude, longitude)`` with longitude
**east-positive**. Local mean solar time (``longitude / 15``) is used as each
point's time zone, which is what fixes the instant of its sunset.
"""

from __future__ import annotations

#: Worldwide sample of inhabited continental locations, ordered west to east.
LAND_POINTS: tuple[tuple[str, float, float], ...] = (
    # --- Americas: the last lands to see sunset, so they decide the boundary ---
    ("Anchorage", 61.2, -149.9),
    ("Fairbanks", 64.8, -147.7),
    ("Vancouver", 49.3, -123.1),
    ("Seattle", 47.6, -122.3),
    ("San Francisco", 37.8, -122.4),
    ("Los Angeles", 34.1, -118.2),
    ("Tijuana", 32.5, -117.0),
    ("Phoenix", 33.4, -112.1),
    ("Salt Lake City", 40.8, -111.9),
    ("Denver", 39.7, -105.0),
    ("Acapulco", 16.9, -99.9),
    ("Mexico City", 19.4, -99.1),
    ("Houston", 29.8, -95.4),
    ("Winnipeg", 49.9, -97.1),
    ("Guatemala City", 14.6, -90.5),
    ("Chicago", 41.9, -87.6),
    ("Lima", -12.0, -77.0),
    ("Quito", -0.2, -78.5),
    ("Panama City", 9.0, -79.5),
    ("Bogota", 4.7, -74.1),
    ("Miami", 25.8, -80.2),
    ("New York", 40.7, -74.0),
    ("La Paz", -16.5, -68.1),
    ("Santiago", -33.5, -70.7),
    ("Ushuaia", -54.8, -68.3),
    ("Caracas", 10.5, -66.9),
    ("Manaus", -3.1, -60.0),
    ("Buenos Aires", -34.6, -58.4),
    ("Halifax", 44.6, -63.6),
    ("Sao Paulo", -23.5, -46.6),
    ("Rio de Janeiro", -22.9, -43.2),
    ("Recife", -8.0, -34.9),
    # --- Atlantic edge, Europe, Africa ---
    ("Nuuk", 64.2, -51.7),
    ("Reykjavik", 64.1, -21.9),
    ("Dakar", 14.7, -17.5),
    ("Casablanca", 33.6, -7.6),
    ("Lisbon", 38.7, -9.1),
    ("Madrid", 40.4, -3.7),
    ("London", 51.5, -0.1),
    ("Accra", 5.6, -0.2),
    ("Paris", 48.9, 2.4),
    ("Algiers", 36.8, 3.1),
    ("Lagos", 6.5, 3.4),
    ("Rome", 41.9, 12.5),
    ("Tripoli", 32.9, 13.2),
    ("Berlin", 52.5, 13.4),
    ("Kinshasa", -4.3, 15.3),
    ("Cape Town", -33.9, 18.4),
    ("Windhoek", -22.6, 17.1),
    ("Johannesburg", -26.2, 28.0),
    ("Cairo", 30.0, 31.2),
    ("Istanbul", 41.0, 29.0),
    ("Kyiv", 50.5, 30.5),
    ("Khartoum", 15.6, 32.5),
    ("Nairobi", -1.3, 36.8),
    ("Moscow", 55.8, 37.6),
    ("Mecca", 21.4, 39.8),
    ("Antananarivo", -18.9, 47.5),
    ("Riyadh", 24.7, 46.7),
    ("Tehran", 35.7, 51.4),
    # --- Asia, Oceania ---
    ("Karachi", 24.9, 67.0),
    ("Tashkent", 41.3, 69.3),
    ("Mumbai", 19.1, 72.9),
    ("Delhi", 28.6, 77.2),
    ("Colombo", 6.9, 79.9),
    ("Kathmandu", 27.7, 85.3),
    ("Dhaka", 23.8, 90.4),
    ("Yangon", 16.8, 96.2),
    ("Bangkok", 13.8, 100.5),
    ("Singapore", 1.4, 103.8),
    ("Jakarta", -6.2, 106.8),
    ("Perth", -31.9, 115.9),
    ("Beijing", 39.9, 116.4),
    ("Shanghai", 31.2, 121.5),
    ("Manila", 14.6, 121.0),
    ("Darwin", -12.5, 130.8),
    ("Adelaide", -34.9, 138.6),
    ("Tokyo", 35.7, 139.7),
    ("Vladivostok", 43.1, 131.9),
    ("Melbourne", -37.8, 145.0),
    ("Port Moresby", -9.5, 147.2),
    ("Sydney", -33.9, 151.2),
    ("Magadan", 59.6, 150.8),
    ("Auckland", -36.9, 174.8),
    ("Anadyr", 64.7, 177.5),
)
