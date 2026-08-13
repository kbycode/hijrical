"""
Religious days and holy nights.

The notable subtlety here is that a **holy night begins at sunset of the
previous Gregorian day**, because the Islamic day starts at maghrib. For
example *Mawlid* falls on 12 Rabi al-awwal, but the *night* of Mawlid begins
the evening before -- which is why the ``eve`` field is provided.

Names are localized; pass ``lang`` (``"en"``, ``"tr"``, ``"ar"`` or any
registered language) to :meth:`ReligiousDay.name`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ._julian import jdn_to_gregorian, jdn_weekday
from .locales import get_locale

# Holiday kinds.
FEAST = "feast"
HOLY_NIGHT = "holy_night"
OBSERVANCE = "observance"
FAST = "fast"

# (month, start_day, count, key, kind, night). ``night`` marks days whose holy
# night begins on the previous evening.
_FIXED = (
    (1, 1, 1, "new_year", OBSERVANCE, False),
    (1, 10, 1, "ashura", OBSERVANCE, False),
    (3, 12, 1, "mawlid", HOLY_NIGHT, True),
    (7, 1, 1, "three_months", OBSERVANCE, False),
    (7, 27, 1, "isra_miraj", HOLY_NIGHT, True),
    (8, 15, 1, "baraat", HOLY_NIGHT, True),
    (9, 1, 1, "ramadan_start", FAST, False),
    (9, 27, 1, "laylat_al_qadr", HOLY_NIGHT, True),
    (10, 1, 3, "eid_al_fitr", FEAST, False),
    (12, 9, 1, "arafah", OBSERVANCE, False),
    (12, 10, 4, "eid_al_adha", FEAST, False),
)


@dataclass(frozen=True)
class ReligiousDay:
    """A single religious day, with its Gregorian date and (for nights) eve."""

    key: str
    kind: str
    hijri: tuple[int, int, int]
    gregorian: date
    eve: date | None = None        # evening a holy night begins on (Gregorian)
    day_index: int | None = None   # 1-based index within a multi-day feast
    observed_hijri: tuple[int, int, int] | None = None  # Hijri date it is marked on

    @property
    def is_holy_night(self) -> bool:
        return self.kind == HOLY_NIGHT

    @property
    def observed(self) -> date:
        """The date this day is **published/observed** on.

        For a holy night that is its eve -- the evening the night begins -- which
        is exactly how Diyanet and other authorities print kandils (e.g. Mi'raj
        appears on 26 Rajab, the evening 27 Rajab starts). For everything else it
        is the day itself.
        """
        return self.eve if self.eve is not None else self.gregorian

    @property
    def observed_hijri_date(self) -> tuple[int, int, int]:
        """The **Hijri** date this day is marked on (mirror of :attr:`observed`)."""
        return self.observed_hijri or self.hijri

    def name(self, lang: str | None = None) -> str:
        """Localized name (adds the day number for multi-day feasts).

        Falls back to the English name when a locale predates a holiday key, so
        third-party locales keep working across upgrades.
        """
        loc = get_locale(lang)
        base = loc["holidays"].get(self.key)
        if base is None:
            from .locales import get_locale as _gl
            base = _gl("en")["holidays"].get(self.key, self.key)
        if self.day_index is not None:
            base += loc["day_suffix"].format(n=self.day_index)
        return base

    def describe(self, lang: str | None = None) -> str:
        s = f"{self.name(lang)}: {self.gregorian.isoformat()}"
        if self.eve is not None:
            s += f" (night begins the evening of {self.eve.isoformat()})"
        return s

    def __str__(self) -> str:
        return self.describe()


def holiday_key(month: int, day: int, observed: bool = True) -> str | None:
    """Return the holiday key for a fixed-date (month, day), or ``None``.

    With ``observed=True`` (the default) a **holy night matches its eve** -- the
    date printed on calendars, because the night starts that evening. So Mawlid
    is found on 11 Rabi al-awwal, the evening 12 Rabi al-awwal begins, which is
    exactly how Diyanet prints it. Pass ``observed=False`` to match instead the
    Hijri day the night belongs to (12 Rabi al-awwal).

    Raghaib is not fixed-date; it is produced by :func:`year_holidays` and
    detected by :meth:`HijriDate.holiday`.
    """
    for m, start, count, key, _kind, night in _FIXED:
        first = start - 1 if (night and observed) else start
        if m == month and first <= day < first + count:
            return key
    return None


def _greg(calendar, year: int, month: int, day: int) -> tuple[int, date]:
    jdn = calendar.to_jdn(year, month, day)
    y, m, d = jdn_to_gregorian(jdn)
    return jdn, date(y, m, d)


def raghaib(calendar, hijri_year: int) -> ReligiousDay:
    """Raghaib: the first Friday eve of Rajab (the night before its first Friday)."""
    jdn1 = calendar.to_jdn(hijri_year, 7, 1)
    forward = (4 - jdn_weekday(jdn1)) % 7  # 4 = Friday
    friday_jdn = jdn1 + forward
    fy, fm, fd = jdn_to_gregorian(friday_jdn)
    ey, em, ed = jdn_to_gregorian(friday_jdn - 1)
    return ReligiousDay(
        key="raghaib",
        kind=HOLY_NIGHT,
        hijri=(hijri_year, 7, forward + 1),
        gregorian=date(fy, fm, fd),
        eve=date(ey, em, ed),
        # The eve can fall in the previous month (e.g. 29 Jumada II 1445), so
        # ask the calendar rather than assuming "day - 1".
        observed_hijri=calendar.from_jdn(friday_jdn - 1),
    )


def year_holidays(hijri_year: int, calendar, *, lang: str | None = None) -> list[ReligiousDay]:
    """All religious days of a Hijri year, in chronological (Gregorian) order.

    ``calendar`` is any engine with ``to_jdn`` (arithmetic or astronomical).
    ``lang`` is accepted for symmetry but names are resolved lazily via
    :meth:`ReligiousDay.name`; it does not change the returned objects.
    """
    days: list[ReligiousDay] = []
    for m, start, count, key, kind, night in _FIXED:
        for i in range(count):
            day = start + i
            jdn, greg = _greg(calendar, hijri_year, m, day)
            eve = None
            if night:
                ey, em, ed = jdn_to_gregorian(jdn - 1)
                eve = date(ey, em, ed)
            days.append(
                ReligiousDay(
                    key=key,
                    kind=kind,
                    hijri=(hijri_year, m, day),
                    gregorian=greg,
                    eve=eve,
                    day_index=(i + 1) if count > 1 else None,
                    observed_hijri=((hijri_year, m, day - 1) if night
                                    else (hijri_year, m, day)),
                )
            )
    days.append(raghaib(calendar, hijri_year))

    # Eve of Eid al-Fitr: the last day of Ramadan, whose number depends on
    # whether that Ramadan runs 29 or 30 days.
    last = calendar.month_length(hijri_year, 9)
    jdn, greg = _greg(calendar, hijri_year, 9, last)
    days.append(
        ReligiousDay(
            key="eid_al_fitr_eve",
            kind=OBSERVANCE,
            hijri=(hijri_year, 9, last),
            gregorian=greg,
        )
    )

    days.sort(key=lambda r: r.gregorian)
    return days
