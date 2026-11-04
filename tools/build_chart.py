#!/usr/bin/env python3
"""
Rebuild the home-page chart (Russian theatre, monthly enrolments and desertions, 1914–1920).

Counts come from ``data/final/persons/legionnaires_clean.parquet`` in the thesis repository,
with the definitions of ``notebooks/03_visualisation.ipynb`` cell 8: ``theater == "Russia"``,
dates precise to the day or month only, deserters flagged by ``deserted``. Only the 84
monthly aggregates reach the page.

Rewrites, in place: the four series paths, both axes' tick labels, the peak figures in the
chart's <desc> and comment, the readout totals, and the data literal of the hover script.

Usage::

    python tools/build_chart.py [path/to/Legions]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

SITE = Path(__file__).resolve().parents[1]
LEGIONS = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    SITE.parents[1] / "!!!CERGE" / ".Thesis" / "Legions"

X0, X1, Y0, Y1 = 76, 958, 52, 296
MON = ["January", "February", "March", "April", "May", "June", "July",
       "August", "September", "October", "November", "December"]


def series() -> tuple[list[int], list[int]]:
    df = pd.read_parquet(LEGIONS / "data/final/persons/legionnaires_clean.parquet")
    for c in ("enroll_date", "exit_date"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    russia = df[df["theater"] == "Russia"]
    months = pd.date_range("1914-01-01", "1920-12-01", freq="MS")

    def monthly(sub, col):
        sub = sub[sub[f"{col}_precision"].isin(["day", "month"])]
        s = sub[col].dropna()
        s = s[s.between("1914-01-01", "1920-12-31")]
        return s.dt.to_period("M").dt.to_timestamp().value_counts().reindex(months, fill_value=0)

    e = monthly(russia, "enroll_date")
    d = monthly(russia[russia["deserted"].astype(bool)], "exit_date")
    return [int(v) for v in e], [int(v) for v in d]


def fmt(v: float) -> str:
    return f"{round(v, 1):g}"


def path(vals, vmax, close):
    pts = [f"{fmt(X0 + i * (X1 - X0) / 83)} {fmt(Y1 - v / vmax * (Y1 - Y0))}"
           for i, v in enumerate(vals)]
    return "M" + " L".join(pts) + (f" L{X1} {Y1} L{X0} {Y1} Z" if close else "")


def month_name(i: int) -> str:
    return f"{MON[i % 12]} {1914 + i // 12}"


def sub1(pattern, repl, text):
    new, n = re.subn(pattern, repl, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"pattern not found in index.html: {pattern[:60]}")
    return new


def main() -> None:
    enrol, desert = series()
    emax, dmax = max(enrol), max(desert)
    idx = SITE / "index.html"
    s = idx.open(encoding="utf-8", newline="").read()

    for cls, vals, vmax, close in [("fill-a", enrol, emax, True), ("fill-b", desert, dmax, True),
                                   ("series-a", enrol, emax, False), ("series-b", desert, dmax, False)]:
        d = path(vals, vmax, close)
        s = sub1(r'(<path class="' + cls + r'" d=")[^"]+(")', lambda m: m.group(1) + d + m.group(2), s)

    ys = [296, 235, 174, 113, 52]
    left = "".join(f'<text x="67" y="{y}">{t}</text>' for y, t in
                   zip(ys, ["0"] + [f"{emax * k / 4 / 1000:.1f}k" for k in (1, 2, 3, 4)]))
    right = "".join(f'<text x="967" y="{y}">{t}</text>' for y, t in
                    zip(ys, ["0"] + [str(int(dmax * k / 4 + 0.5)) for k in (1, 2, 3, 4)]))
    s = sub1(r'(<g class="tick tick--l">).*?(</g>)', lambda m: m.group(1) + left + m.group(2), s)
    s = sub1(r'(<g class="tick tick--r">).*?(</g>)', lambda m: m.group(1) + right + m.group(2), s)

    ie, idd = enrol.index(emax), desert.index(dmax)
    s = sub1(r'Enrolments rise through 1916 and peak at\s+[\d,]+ in [A-Za-z]+ \d{4}',
             f"Enrolments rise through 1916 and peak at\n                  {emax:,} in {month_name(ie)}", s)
    s = sub1(r'peak at [\d,]+ in\s+[A-Za-z]+ \d{4}, after the Bolshevik coup',
             f"peak at {dmax:,} in\n                  {month_name(idd)}, after the Bolshevik coup", s)
    s = sub1(r'enrolments peak at [\d,]+ in a\s+month against [\d,]+ desertions',
             f"enrolments peak at {emax:,} in a\n               month against {dmax} desertions", s)
    s = sub1(r'(Enrolments&nbsp;<b>)[\d,]+(</b>\s*<span class="swatch swatch--b"></span>Desertions&nbsp;<b>)[\d,]+(</b>)',
             lambda m: f"{m.group(1)}{sum(enrol):,}{m.group(2)}{sum(desert):,}{m.group(3)}", s)
    lit = json.dumps({"n": 84, "x0": X0, "x1": X1, "y0": Y0, "y1": Y1, "emax": emax,
                      "dmax": dmax, "enrol": enrol, "desert": desert}, separators=(",", ":"))
    s = sub1(r'var d = \{"n":84.*?\};', lambda m: "var d = " + lit + ";", s)

    idx.open("w", encoding="utf-8", newline="").write(s)
    print(f"enrolments {sum(enrol):,} (peak {emax:,}, {month_name(ie)}), "
          f"desertions {sum(desert):,} (peak {dmax}, {month_name(idd)})")


if __name__ == "__main__":
    main()
