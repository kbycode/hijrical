"""English locale."""

LOCALE = {
    "code": "en",
    "name": "English",
    "era": "AH",
    "day_suffix": " (Day {n})",
    "months": (
        "Muharram", "Safar", "Rabi al-awwal", "Rabi al-thani",
        "Jumada al-awwal", "Jumada al-thani", "Rajab", "Sha'ban",
        "Ramadan", "Shawwal", "Dhu al-Qi'dah", "Dhu al-Hijjah",
    ),
    # Monday-first, to match jdn_weekday / date.weekday().
    "weekdays": (
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ),
    "holidays": {
        "new_year": "Islamic New Year",
        "ashura": "Day of Ashura",
        "mawlid": "Mawlid al-Nabi",
        "raghaib": "Laylat al-Raghaib",
        "isra_miraj": "Isra and Mi'raj",
        "baraat": "Mid-Sha'ban (Bara'ah)",
        "ramadan_start": "First day of Ramadan",
        "laylat_al_qadr": "Laylat al-Qadr",
        "eid_al_fitr": "Eid al-Fitr",
        "arafah": "Day of Arafah",
        "eid_al_adha": "Eid al-Adha",
    },
}
