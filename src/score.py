"""
Score each fetched program page against RUBRIC.md.

Five criteria, 1 to 3 each, maximum 15. The reference date is fixed rather than
read from the clock so the scores are reproducible: rerunning this in six months
against the same HTML must produce the same numbers.

Design note on C1. The rubric scores freshness from the "Updated" stamp because
that is the only recency signal a farmer can see. The audit's main finding is that
this signal is not load-bearing: pages stamped within the last five weeks display
deadlines from earlier years. C1 and C2 are deliberately scored independently so
that divergence is visible in the data rather than averaged away.
"""

import csv
import datetime
import os
import re

REFERENCE_DATE = datetime.date(2026, 8, 6)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def parse_updated(s):
    if not s or s == "ABSENT":
        return None
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def score_c1_freshness(updated):
    if updated is None:
        return 1
    age_days = (REFERENCE_DATE - updated).days
    if age_days <= 365:
        return 3
    if age_days <= 730:
        return 2
    return 1


def deadline_year(text):
    years = [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", text or "")]
    return max(years) if years else None


def score_c2_deadline(deadline_raw, contradicts_body):
    """
    1 if the status is incoherent: a Closed date in the future, a Due date in the
    past, a month-and-day with no year, or a header that contradicts the body.
    2 if no deadline is shown and the program is genuinely rolling.
    3 if the status is coherent and currently true.
    """
    if contradicts_body:
        return 1
    if not deadline_raw or deadline_raw == "ABSENT":
        return 2
    if not re.search(r"\b(19|20)\d{2}\b", deadline_raw):
        return 1  # month and day with no year: the reader cannot tell which cycle
    year = deadline_year(deadline_raw)
    m = re.match(r"(Closed|Due)\s+([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", deadline_raw)
    if m:
        kind, month, day, yr = m.groups()
        try:
            d = datetime.datetime.strptime(f"{month} {day} {yr}", "%B %d %Y").date()
        except ValueError:
            return 2
        if kind == "Closed" and d > REFERENCE_DATE:
            return 1  # advertised as closed on a date that has not happened
        if kind == "Due" and d < REFERENCE_DATE:
            return 1  # advertised as open past its own deadline
    return 3


C3 = {"SPECIFIC": 3, "GENERIC": 2, "NONE": 1}
C5 = {"EXPLICIT": 3, "PROSE": 2, "ABSENT": 1}


def score_c4_amount(amount):
    if not amount or amount == "ABSENT":
        return 1
    if re.search(r"\$[\d,]+", amount):
        return 3
    if re.search(r"\d+\s*(percent|%)", amount, re.I):
        return 2  # a percentage with no cap is not actionable on its own
    return 2


def main():
    rows = list(csv.DictReader(open(os.path.join(DATA, "scored_programs.csv"))))
    for r in rows:
        if r["status"] != "OK":
            continue
        contradicts = bool(re.search(r"contradict|conflict", r["note"], re.I))
        r["C1"] = score_c1_freshness(parse_updated(r["last_updated"]))
        r["C2"] = score_c2_deadline(r["deadline_raw"], contradicts)
        r["C3"] = C3.get(r["source_quality"], 1)
        r["C4"] = score_c4_amount(r["amount"])
        r["C5"] = C5.get(r["eligibility"], 1)
        r["total"] = sum(int(r[c]) for c in ("C1", "C2", "C3", "C4", "C5"))
    with open(os.path.join(DATA, "scored_programs.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
