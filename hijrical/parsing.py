"""
Forgiving date-string parsing.

Turns human-friendly strings into ``(year, month, day)`` fields. It understands

* ISO / separated numerics -- ``"1447-09-01"``, ``"1447/9/1"``, ``"1447.09.01"``,
* day + month-name + year -- ``"1 Ramadan 1447"``, ``"15 Ramazan 1447"``,
  ``"12 Rabi al-awwal 1447"``, ``"١ رمضان ١٤٤٧"``,
* month-name + day + year -- ``"Ramadan 1, 1447"``.

Month names are recognized in **every registered language**, so the parser
grows automatically when you add a locale. The actual range validation is left
to the calendar engine, which gives precise, localized error messages.
"""

from __future__ import annotations

import re
import unicodedata

from .exceptions import ParseError
from .locales import _LOCALES

_SPLIT = re.compile(r"[\s,\-/.،]+")  # incl. Arabic comma U+060C

# Map Arabic-Indic and Persian digits to ASCII.
_DIGIT_MAP = {ord(c): str(i % 10) for i, c in enumerate(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹"
)}


def _ascii_digits(text: str) -> str:
    return text.translate(_DIGIT_MAP)


def _normalize(token: str) -> str:
    """Fold a month token for matching: lowercase, drop marks, strip separators."""
    t = unicodedata.normalize("NFKD", token).lower()
    t = "".join(c for c in t if not unicodedata.combining(c))
    # Turkish-specific folds that NFKD does not cover.
    for a, b in (("ı", "i"), ("ş", "s"), ("ç", "c"), ("ö", "o"),
                 ("ü", "u"), ("ğ", "g"), ("'", ""), ("`", ""), ("-", "")):
        t = t.replace(a, b)
    return re.sub(r"\s+", "", t)


def _month_lookup() -> dict[str, int]:
    """Normalized month-name -> month number, gathered from all locales."""
    table: dict[str, int] = {}
    for loc in _LOCALES.values():
        for idx, name in enumerate(loc["months"], start=1):
            table[_normalize(name)] = idx
    return table


def month_from_name(name: str) -> int | None:
    """Resolve a month name (any registered language) to its number, or ``None``."""
    return _month_lookup().get(_normalize(name))


def parse_fields(text: str) -> tuple[int, int, int]:
    """Parse a Hijri date string into ``(year, month, day)`` integer fields.

    Validation of the values against a calendar is performed by the caller.
    """
    if not text or not text.strip():
        raise ParseError("Empty date string.")
    raw = _ascii_digits(text.strip())
    tokens = [t for t in _SPLIT.split(raw) if t]

    numeric = [t for t in tokens if t.isdigit()]
    words = [t for t in tokens if not t.isdigit()]

    if words:
        month = month_from_name("".join(words))
        if month is None:
            raise ParseError(
                f"Unrecognized month name in {text!r}. "
                "Use an English, Turkish or Arabic month name, or a number."
            )
        if len(numeric) != 2:
            raise ParseError(
                f"Expected a day and a year alongside the month in {text!r}."
            )
        a, b = int(numeric[0]), int(numeric[1])
        # The 3-4 digit value (or the one > 31) is the year.
        if a > 31 or len(numeric[0]) >= 3:
            year, day = a, b
        else:
            day, year = a, b
        return year, month, day

    if len(numeric) != 3:
        raise ParseError(
            f"Could not parse {text!r}. Try 'YYYY-MM-DD' or '1 Ramadan 1447'."
        )
    n = [int(x) for x in numeric]
    if len(numeric[0]) >= 3:          # year-first (ISO)
        return n[0], n[1], n[2]
    if len(numeric[2]) >= 3:          # day-month-year
        return n[2], n[1], n[0]
    return n[0], n[1], n[2]           # default: year-first
