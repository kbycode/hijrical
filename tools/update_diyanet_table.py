#!/usr/bin/env python
"""
Regenerate ``hijrical/diyanet.py``'s official table from Diyanet's own pages.

The embedded table is a **snapshot**: it cannot extend itself, because the data
simply does not exist until Diyanet publishes the next years. When they do, this
script turns their pages back into the Python table in one step.

Diyanet's site rejects scripted requests (a WAF sits in front of it), so fetch
the pages in a normal browser and save them, rather than trying to work around
that:

1. Open  https://vakithesaplama.diyanet.gov.tr/dini_gunler.php  and follow the
   "<year> Yılı Dini Günler" links for the years you want.
2. Save each page (Ctrl+S, "Web Page, HTML only") into one folder.
3. Run:

       python tools/update_diyanet_table.py path/to/folder

It prints the ``DIYANET_MONTH_STARTS`` tuple; paste it into ``hijrical/diyanet.py``
replacing the old one, then run ``python run_tests.py``. Extend the OFFICIAL rows
in ``tests/test_diyanet.py`` the same way to keep the verification honest.

The parser only trusts rows that give day ``1`` of a month, and it re-checks that
the result is contiguous and that every month is 29 or 30 days -- so a mangled
save is caught instead of silently corrupting the calendar.
"""

from __future__ import annotations

import glob
import os
import re
import sys
from html.parser import HTMLParser

MONTHS = {
    "MUHARREM": 1, "SAFER": 2, "R.EVVEL": 3, "R.VVEL": 3, "REBIULEVVEL": 3,
    "R.AHIR": 4, "R.AHİR": 4, "C.EVVEL": 5, "C.AHIR": 6, "C.AHİR": 6,
    "RECEB": 7, "RECEP": 7, "SABAN": 8, "ŞABAN": 8, "RAMAZAN": 9,
    "SEVVAL": 10, "ŞEVVAL": 10, "ZILKADE": 11, "ZİLKADE": 11,
    "ZILHICCE": 12, "ZİLHİCCE": 12,
}
GREG_MONTHS = {
    "OCAK": 1, "ŞUBAT": 2, "SUBAT": 2, "MART": 3, "NİSAN": 4, "NISAN": 4,
    "MAYIS": 5, "HAZİRAN": 6, "HAZIRAN": 6, "TEMMUZ": 7, "AĞUSTOS": 8,
    "AGUSTOS": 8, "EYLÜL": 9, "EYLUL": 9, "EKİM": 10, "EKIM": 10,
    "KASIM": 11, "ARALIK": 12,
}


class _Rows(HTMLParser):
    """Collect table rows as lists of cell texts."""

    def __init__(self):
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell)).strip()
            self._row.append(text)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def parse_file(path: str) -> dict[tuple[int, int], str]:
    with open(path, encoding="utf-8", errors="ignore") as fh:
        parser = _Rows()
        parser.feed(fh.read())

    starts: dict[tuple[int, int], str] = {}
    for row in parser.rows:
        if len(row) < 5:
            continue
        day, hmonth, hyear, gday, gmonthyear = (c.strip() for c in row[:5])
        if not day.isdigit() or int(day) != 1:
            continue  # only first-of-month rows pin a month start
        hm = MONTHS.get(hmonth.upper().replace(" ", ""))
        if hm is None or not hyear.isdigit() or not gday.isdigit():
            continue
        m = re.match(r"([^\d\-]+)\s*-?\s*(\d{4})", gmonthyear)
        if not m:
            continue
        gm = GREG_MONTHS.get(m.group(1).strip().upper())
        if gm is None:
            continue
        starts[(int(hyear), hm)] = f"{int(m.group(2)):04d}-{gm:02d}-{int(gday):02d}"
    return starts


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    target = argv[1]
    files = ([target] if os.path.isfile(target)
             else sorted(glob.glob(os.path.join(target, "*.htm*"))))
    if not files:
        print(f"No HTML files found in {target!r}.")
        return 1

    starts: dict[tuple[int, int], str] = {}
    for path in files:
        found = parse_file(path)
        print(f"# {os.path.basename(path)}: {len(found)} month starts", file=sys.stderr)
        starts.update(found)

    keys = sorted(starts)
    if not keys:
        print("Parsed no month starts -- are these the 'Dini Günler' pages?")
        return 1

    # Integrity: contiguous months, each 29 or 30 days long.
    from datetime import date

    problems = []
    for (y1, m1), (y2, m2) in zip(keys, keys[1:]):
        expected = (y1, m1 + 1) if m1 < 12 else (y1 + 1, 1)
        if (y2, m2) != expected:
            problems.append(f"gap: {y1}-{m1:02d} -> {y2}-{m2:02d}")
            continue
        d1 = date(*(int(p) for p in starts[(y1, m1)].split("-")))
        d2 = date(*(int(p) for p in starts[(y2, m2)].split("-")))
        if (d2 - d1).days not in (29, 30):
            problems.append(f"{y1}-{m1:02d} is {(d2 - d1).days} days long")
    if problems:
        print("Refusing to emit a table with problems:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 1

    print(f"# Verified: {len(keys)} contiguous months, "
          f"{keys[0][0]}-{keys[0][1]:02d} .. {keys[-1][0]}-{keys[-1][1]:02d}\n")
    print("DIYANET_MONTH_STARTS: tuple[tuple[int, int, str], ...] = (")
    line = "   "
    for key in keys:
        piece = f' ({key[0]}, {key[1]}, "{starts[key]}"),'
        if len(line) + len(piece) > 79:
            print(line)
            line = "   "
        line += piece
    if line.strip():
        print(line)
    print(")")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
