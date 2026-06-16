"""
Localization registry (i18n).

Month names, weekday names and religious-day names are looked up per language.
Three languages ship by default -- English (``en``), Turkish (``tr``) and Arabic
(``ar``) -- and adding another is just a dictionary away via
:func:`register_locale`.

A locale is a plain ``dict`` with these keys::

    code        str          short language code, e.g. "fr"
    name        str          autonym, e.g. "Français"
    era         str          era suffix, e.g. "AH"
    day_suffix  str          template with {n}, e.g. " (Day {n})"
    months      tuple[str]   12 month names, Muharram-first
    weekdays    tuple[str]   7 weekday names, Monday-first
    holidays    dict[str,str] holiday-key -> localized name
"""

from __future__ import annotations

from . import ar, en, tr

DEFAULT_LANGUAGE = "en"

_REQUIRED_KEYS = {"code", "name", "era", "day_suffix", "months", "weekdays", "holidays"}

_LOCALES: dict[str, dict] = {}


def register_locale(locale: dict) -> None:
    """Register (or override) a language pack. See module docstring for the schema."""
    missing = _REQUIRED_KEYS - set(locale)
    if missing:
        raise ValueError(f"Locale is missing keys: {', '.join(sorted(missing))}.")
    if len(locale["months"]) != 12:
        raise ValueError("Locale 'months' must have exactly 12 entries.")
    if len(locale["weekdays"]) != 7:
        raise ValueError("Locale 'weekdays' must have exactly 7 entries.")
    _LOCALES[locale["code"]] = locale


for _pack in (en.LOCALE, tr.LOCALE, ar.LOCALE):
    register_locale(_pack)


def available_languages() -> list[str]:
    """Registered language codes."""
    return sorted(_LOCALES)


def get_locale(lang: str | None = None) -> dict:
    """Return the locale dict for ``lang`` (default language if ``None``)."""
    code = lang or DEFAULT_LANGUAGE
    try:
        return _LOCALES[code]
    except KeyError:
        opts = ", ".join(available_languages())
        raise ValueError(
            f"Unsupported language: {lang!r}. Available: {opts}. "
            "Add your own with hijrical.register_locale()."
        ) from None


def month_name(month: int, lang: str | None = None) -> str:
    """Localized name of Hijri month ``month`` (1-12)."""
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be 1-12, got {month}.")
    return get_locale(lang)["months"][month - 1]


def weekday_name(index: int, lang: str | None = None) -> str:
    """Localized weekday name for ``index`` (0=Monday ... 6=Sunday)."""
    if not 0 <= index <= 6:
        raise ValueError(f"Weekday index must be 0-6, got {index}.")
    return get_locale(lang)["weekdays"][index]
