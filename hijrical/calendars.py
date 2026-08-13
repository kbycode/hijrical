"""
Calendar engines.

Two interchangeable engines share one interface (``to_jdn``, ``from_jdn``,
``month_length``):

* :class:`ArithmeticCalendar` -- the tabular calendar. Pure integer arithmetic,
  perfectly reversible, **unbounded date range**. The right default for civil,
  database and historical use.
* :class:`AstronomicalCalendar` -- months begin when a real crescent becomes
  visible to a given :class:`~hijrical.observer.Observer` under a chosen
  :class:`~hijrical.criteria.Criterion`. Location-aware: Istanbul and Mecca can
  legitimately differ by a day. A close *prediction* of observed calendars, not
  a reversible guarantee.
"""

from __future__ import annotations

import math
from datetime import date

from ._julian import gregorian_to_jdn, jdn_to_gregorian
from ._moon import SYNODIC_MONTH, new_moon_jd_ut
from ._sun import datetime_to_jd_ut, sunset
from .criteria import compute_crescent, get_criterion
from .exceptions import InvalidDateError, OutOfRangeError
from .land import LAND_POINTS
from .observer import DEFAULT_OBSERVER, Observer, resolve_observer

_CYCLE_YEARS = 30
_CYCLE_DAYS = 10631  # 354*30 + 11


class Calendar:
    """Abstract base for calendar engines."""

    name = "calendar"

    def to_jdn(self, year: int, month: int, day: int) -> int:  # pragma: no cover
        raise NotImplementedError

    def from_jdn(self, jdn: int) -> tuple[int, int, int]:  # pragma: no cover
        raise NotImplementedError

    def month_length(self, year: int, month: int) -> int:  # pragma: no cover
        raise NotImplementedError

    def year_length(self, year: int) -> int:
        return self.to_jdn(year + 1, 1, 1) - self.to_jdn(year, 1, 1)

    def is_leap_year(self, year: int) -> bool:
        return self.year_length(year) == 355


# ---------------------------------------------------------------------------
# Arithmetic (tabular) calendar
# ---------------------------------------------------------------------------

class ArithmeticCalendar(Calendar):
    """Tabular Hijri calendar with a selectable leap-year pattern and epoch."""

    name = "arithmetic"

    def __init__(self, variant: str = "kuwaiti") -> None:
        if isinstance(variant, _Variant):
            self.variant = variant
        else:
            try:
                self.variant = VARIANTS[variant]
            except KeyError:
                opts = ", ".join(sorted(VARIANTS))
                raise InvalidDateError(
                    f"Unknown arithmetic variant: {variant!r}. Available: {opts}."
                ) from None

    def is_leap_year(self, year: int) -> bool:
        position = ((year - 1) % _CYCLE_YEARS) + 1
        return position in self.variant.leap_years

    def _leap_count(self, n: int) -> int:
        full, rem = divmod(n, _CYCLE_YEARS)
        return full * 11 + sum(1 for k in self.variant.leap_years if k <= rem)

    def month_length(self, year: int, month: int) -> int:
        if month == 12:
            return 30 if self.is_leap_year(year) else 29
        return 30 if month % 2 == 1 else 29

    def year_length(self, year: int) -> int:
        return 355 if self.is_leap_year(year) else 354

    def _days_before_year(self, year: int) -> int:
        return 354 * (year - 1) + self._leap_count(year - 1)

    def validate(self, year: int, month: int, day: int) -> None:
        if not 1 <= month <= 12:
            raise InvalidDateError(
                f"Month must be 1-12, got {month}. A Hijri year has 12 months "
                "(Muharram through Dhu al-Hijjah)."
            )
        upper = self.month_length(year, month)
        if not 1 <= day <= upper:
            raise InvalidDateError(
                f"Day {day} is out of range for {year}-{month:02d}, "
                f"which has {upper} days."
            )

    def to_jdn(self, year: int, month: int, day: int) -> int:
        self.validate(year, month, day)
        days = (
            self.variant.epoch_jdn
            + self._days_before_year(year)
            + sum(self.month_length(year, m) for m in range(1, month))
            + (day - 1)
        )
        return days

    def from_jdn(self, jdn: int) -> tuple[int, int, int]:
        n = jdn - self.variant.epoch_jdn
        year = (n * _CYCLE_YEARS) // _CYCLE_DAYS + 1
        while self._days_before_year(year) > n:
            year -= 1
        while self._days_before_year(year + 1) <= n:
            year += 1
        within = n - self._days_before_year(year)
        month = 1
        while month < 12:
            length = self.month_length(year, month)
            if within < length:
                break
            within -= length
            month += 1
        return year, month, within + 1


class _Variant:
    __slots__ = ("label", "leap_years", "epoch_jdn")

    def __init__(self, label: str, leap_years: frozenset, epoch_jdn: int) -> None:
        self.label = label
        self.leap_years = leap_years
        self.epoch_jdn = epoch_jdn


#: Tabular variants. ``kuwaiti`` (Type II, civil epoch) is the default.
VARIANTS: dict[str, _Variant] = {
    "kuwaiti": _Variant(
        "Type II - Kuwaiti / Microsoft (civil epoch)",
        frozenset({2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29}), 1948440,
    ),
    "kuwaiti_astronomical": _Variant(
        "Type II - astronomical epoch (Thursday)",
        frozenset({2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29}), 1948439,
    ),
    "type1": _Variant(
        "Type I (15-based pattern)",
        frozenset({2, 5, 7, 10, 13, 15, 18, 21, 24, 26, 29}), 1948440,
    ),
    "type3": _Variant(
        "Type III (Fatimid / Egyptian)",
        frozenset({2, 5, 8, 10, 13, 16, 19, 21, 24, 27, 29}), 1948440,
    ),
    "type4": _Variant(
        "Type IV (Habash al-Hasib)",
        frozenset({2, 5, 8, 11, 13, 16, 19, 21, 24, 27, 30}), 1948440,
    ),
}


# ---------------------------------------------------------------------------
# Astronomical (location + visibility) calendar
# ---------------------------------------------------------------------------

GUARD_MIN_YEAR = 1
GUARD_MAX_YEAR = 1600


class AstronomicalCalendar(Calendar):
    """Crescent-visibility calendar.

    Parameters
    ----------
    observer
        An :class:`~hijrical.observer.Observer` (or preset key). In ``"local"``
        scope it is *the* observer; in ``"global"`` scope it only fixes the
        civil-date reference while visibility is tested worldwide.
    criterion
        A :class:`~hijrical.criteria.Criterion` (or name) such as ``"ircica"``.
    scope
        ``"local"`` (default) judges visibility at ``observer`` only.
        ``"global"`` judges it worldwide over **inhabited land** -- the month
        turns over once the crescent is visible anywhere on land, which is how
        "unified" national calendars work (e.g. Diyanet's Türkiye calendar,
        following the 2016 Istanbul congress). Sightings that would fall only
        on open ocean are disregarded, exactly as the congress specified.
    sample
        Optional iterable of ``(name, latitude, longitude)`` overriding the
        built-in land sample used by the global scope.
    """

    name = "astronomical"

    def __init__(self, observer="mecca", criterion="ircica", *,
                 scope: str = "local", sample=None) -> None:
        self.observer = resolve_observer(observer) if observer is not None else DEFAULT_OBSERVER
        self.criterion = get_criterion(criterion)
        if scope not in ("local", "global"):
            raise InvalidDateError("scope must be 'local' or 'global'.")
        self.scope = scope
        self._sample = tuple(sample) if sample is not None else LAND_POINTS
        self._starts: dict[int, int] = {}      # k -> JDN of day 1
        self._k0: int | None = None            # offset: month index N=0 maps to k0
        self._anchor_k: int = 0
        self._lo: int = 0                       # contiguous cached range [lo, hi]
        self._hi: int = 0

    # -- crescent visibility on a candidate evening --------------------------

    def _visible_at(self, obs, evening_jdn: int, conjunction_jd_ut: float) -> bool:
        y, m, d = jdn_to_gregorian(evening_jdn)
        ss = sunset(date(y, m, d), obs.latitude, obs.longitude, obs.utc_offset)
        if ss is None or datetime_to_jd_ut(ss) < conjunction_jd_ut:
            return False
        return self.criterion.is_visible(compute_crescent(obs, ss, conjunction_jd_ut))

    def _visible(self, evening_jdn: int, conjunction_jd_ut: float) -> bool:
        """Whether the crescent is visible on the evening of ``evening_jdn``.

        In ``"local"`` scope this checks the configured observer; in ``"global"``
        scope it returns ``True`` as soon as any grid location qualifies.
        """
        if self.scope == "local":
            return self._visible_at(self.observer, evening_jdn, conjunction_jd_ut)
        for name, lat, lon in self._sample:
            # Local mean solar time fixes the instant of that place's sunset.
            obs = Observer(name, lat, lon, lon / 15.0)
            if self._visible_at(obs, evening_jdn, conjunction_jd_ut):
                return True
        return False

    def _independent_start(self, k: int) -> int:
        """First-visible-evening month start for lunation ``k`` (used only to anchor)."""
        conj = new_moon_jd_ut(k)
        conj_date_jdn = math.floor(conj + self.observer.utc_offset / 24.0 + 0.5)
        for offset in range(0, 5):
            if self._visible(conj_date_jdn + offset, conj):
                return conj_date_jdn + offset + 1
        return conj_date_jdn + 2

    # -- chained month starts (each month is 29 or 30 days) ------------------

    def month_start_jdn(self, k: int) -> int:
        """JDN of day 1 of the lunar month anchored on new moon ``k``.

        Months are linked so that each one lasts 29 or 30 days: the crescent is
        sought on the 29th evening; if it is not visible the month is completed
        to 30 days (never more), exactly as observational calendars work.
        """
        self._calibrate()
        if k in self._starts:
            return self._starts[k]
        # Each month is anchored to *its own* conjunction and only then clamped
        # to 29/30 days from its neighbour. Deriving a month solely from the
        # previous one (chaining) lets small errors accumulate: over ~150 months
        # that drifted by more than two weeks.
        while k > self._hi:                     # extend forward
            nxt = self._hi + 1
            prev = self._starts[self._hi]
            candidate = self._independent_start(nxt)
            self._starts[nxt] = min(max(candidate, prev + 29), prev + 30)
            self._hi = nxt
        while k < self._lo:                     # extend backward
            cur = self._lo
            this_start = self._starts[cur]
            candidate = self._independent_start(cur - 1)
            self._starts[cur - 1] = min(max(candidate, this_start - 30),
                                        this_start - 29)
            self._lo = cur - 1
        return self._starts[k]

    def _cheap_start(self, k: int) -> int:
        """Conjunction-only month-start estimate (±1-2 days); cheap, for picking k0."""
        conj = new_moon_jd_ut(k)
        return math.floor(conj + self.observer.utc_offset / 24.0 + 0.5) + 1

    def _calibrate(self) -> int:
        if self._k0 is not None:
            return self._k0
        anchor_jdn = gregorian_to_jdn(2021, 8, 9)  # 1 Muharram 1443 AH
        anchor_n = (1443 - 1) * 12
        guess = round((anchor_jdn - 2451550.09766) / SYNODIC_MONTH)
        # Pick the lunation with a cheap estimate, then anchor with the full method.
        best_k = min(range(guess - 3, guess + 4),
                     key=lambda k: abs(self._cheap_start(k) - anchor_jdn))
        self._anchor_k = best_k
        self._lo = self._hi = best_k
        self._starts[best_k] = self._independent_start(best_k)
        self._k0 = best_k - anchor_n
        return self._k0

    def _index(self, year: int, month: int) -> int:
        return (year - 1) * 12 + (month - 1)

    def _guard(self, year: int) -> None:
        if not GUARD_MIN_YEAR <= year <= GUARD_MAX_YEAR:
            raise OutOfRangeError(
                f"The astronomical method is reliable for {GUARD_MIN_YEAR}-"
                f"{GUARD_MAX_YEAR} AH; got year {year}. Use the arithmetic method "
                "outside this range."
            )

    def month_length(self, year: int, month: int) -> int:
        k = self._calibrate() + self._index(year, month)
        return self.month_start_jdn(k + 1) - self.month_start_jdn(k)

    def to_jdn(self, year: int, month: int, day: int) -> int:
        self._guard(year)
        if not 1 <= month <= 12:
            raise InvalidDateError(f"Month must be 1-12, got {month}.")
        k = self._calibrate() + self._index(year, month)
        start = self.month_start_jdn(k)
        length = self.month_start_jdn(k + 1) - start
        if not 1 <= day <= length:
            raise InvalidDateError(
                f"Day {day} is out of range for {year}-{month:02d} "
                f"(astronomical month length {length})."
            )
        return start + (day - 1)

    def from_jdn(self, jdn: int) -> tuple[int, int, int]:
        k0 = self._calibrate()
        # Estimate from the cached modern anchor, not k0 (= year 1 AH), so the
        # chain only extends near the target instead of all the way back.
        anchor_start = self.month_start_jdn(self._anchor_k)
        k = self._anchor_k + round((jdn - anchor_start) / SYNODIC_MONTH)
        while self.month_start_jdn(k) > jdn:
            k -= 1
        while self.month_start_jdn(k + 1) <= jdn:
            k += 1
        start = self.month_start_jdn(k)
        n = k - k0
        year = n // 12 + 1
        month = n % 12 + 1
        self._guard(year)
        return year, month, jdn - start + 1
