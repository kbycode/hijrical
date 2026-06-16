"""Julian Day Number core."""

from __future__ import annotations

import random

from hijrical import gregorian_to_jdn, jdn_to_gregorian
from hijrical._julian import is_valid_gregorian, jdn_weekday


def test_known_values():
    assert gregorian_to_jdn(2000, 1, 1) == 2451545
    assert gregorian_to_jdn(1970, 1, 1) == 2440588
    assert gregorian_to_jdn(622, 7, 19) == 1948440  # Hijri civil epoch


def test_round_trip():
    rng = random.Random(7)
    for _ in range(50000):
        y, m, d = rng.randint(-2000, 5000), rng.randint(1, 12), rng.randint(1, 28)
        assert jdn_to_gregorian(gregorian_to_jdn(y, m, d)) == (y, m, d)


def test_weekday():
    assert jdn_weekday(gregorian_to_jdn(2026, 6, 15)) == 0  # Monday
    assert jdn_weekday(gregorian_to_jdn(2000, 1, 1)) == 5   # Saturday


def test_validity():
    assert is_valid_gregorian(2024, 2, 29) is True
    assert is_valid_gregorian(2023, 2, 29) is False
    assert is_valid_gregorian(2023, 13, 1) is False
