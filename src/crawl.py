"""
Ambrook Funding Library crawler.

Two stages, matching how the audit was actually run:

  stage 1  discover  ->  every organization page, then every program link on it
  stage 2  fetch     ->  each program page, extracting the fields the rubric scores

Why the organization walk and not the sitemap: ambrook.com/sitemap.xml exists but
carries no <lastmod> data, mixes case variants of the same slug, and includes
/funding/ URLs that 404 (https://ambrook.com/funding/EQIP returns 404 while
https://ambrook.com/funding/eqip resolves). The organization pages render
server-side and their hrefs are the links a farmer can actually click, so the
org walk defines a population that is both reproducible and meaningful.

Slugs are harvested from hrefs, never constructed. Ambrook's slug conventions are
not uniform: most are kebab-case, some are bare uppercase acronyms (NAQI, UFSG,
WLEI), and at least one contains literal spaces
(/funding/Forest%20Legacy%20Program). Constructing slugs produces false 404s.

Usage:
    python src/crawl.py discover          # writes data/program_index.csv
    python src/crawl.py fetch             # writes data/raw/<slug>.html
"""

import csv
import os
import re
import sys
import time
from urllib.parse import unquote, urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://ambrook.com"
HTML_SITEMAP_ORGS = f"{BASE}/html-sitemap/organizations"
HEADERS = {"User-Agent": "funding-library-audit/1.0 (data quality review; contact in README)"}
SLEEP = 0.5  # be polite; this is someone else's marketing site

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")


def get(url, tries=3):
    for attempt in range(tries):
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        return r
    return r


def discover_organizations():
    """The undocumented HTML sitemap renders all organization links in one page."""
    soup = BeautifulSoup(get(HTML_SITEMAP_ORGS).text, "html.parser")
    slugs = set()
    for a in soup.select("a[href]"):
        m = re.match(r"^/funding/organization/(.+)$", a["href"])
        if m:
            slugs.add(m.group(1).strip("/"))
    return sorted(slugs)


def programs_on_org_page(org_slug):
    """Harvest program hrefs. Never construct a slug from a program name."""
    url = f"{BASE}/funding/organization/{org_slug}"
    r = get(url)
    if r.status_code != 200:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for a in soup.select("a[href]"):
        href = a["href"]
        # program URLs are single-segment under /funding/, excluding the
        # /organization/, /state/, /production/ and /tags/ facet paths
        m = re.match(r"^/funding/([^/]+)/?$", href)
        if not m:
            continue
        slug = m.group(1)
        if slug in ("organization", "state", "production", "tags"):
            continue
        out.append({
            "name": a.get_text(strip=True),
            "slug": unquote(slug),
            "href": urljoin(BASE, href),
            "agency_slug": org_slug,
        })
    return out


def discover():
    orgs = discover_organizations()
    print(f"organizations: {len(orgs)}")
    seen, rows = set(), []
    for i, org in enumerate(orgs, 1):
        for p in programs_on_org_page(org):
            if p["slug"] in seen:
                continue
            seen.add(p["slug"])
            rows.append(p)
        if i % 25 == 0:
            print(f"  {i}/{len(orgs)} orgs, {len(rows)} programs")
        time.sleep(SLEEP)
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "program_index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "slug", "href", "agency_slug"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} programs")


UPDATED_RE = re.compile(r"Updated\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})")


def extract(html):
    """Pull the fields the rubric scores. Absent means absent; never infer."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    m = UPDATED_RE.search(text)
    updated = m.group(1) if m else None

    # The status chip is the Due/Closed/Opens line near the program title.
    status = None
    for pat in (r"(Closed\s+[A-Z][a-z]+\s+\d{1,2},?\s*\d{0,4})",
                r"(Due\s+[A-Z][a-z]+\s+\d{1,2},?\s*\d{0,4})",
                r"(Opens\s+[A-Z][a-z]+\s+\d{1,2},?\s*\d{0,4})"):
        m = re.search(pat, text)
        if m:
            status = m.group(1).strip()
            break

    m = re.search(r"Maximum Award Amount:?\s*([^\n|]{1,80})", text)
    max_award = m.group(1).strip() if m else None

    external = sorted({
        a["href"] for a in soup.select("a[href^=http]")
        if "ambrook.com" not in a["href"]
    })

    return {
        "updated": updated,
        "status_chip": status,
        "max_award_field": max_award,
        "external_links": external,
    }


def fetch():
    os.makedirs(RAW, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(DATA, "program_index.csv"))))
    for i, r in enumerate(rows, 1):
        path = os.path.join(RAW, re.sub(r"[^A-Za-z0-9_.-]", "_", r["slug"]) + ".html")
        if os.path.exists(path):
            continue
        resp = get(r["href"])
        if resp.status_code != 200:
            print(f"  {resp.status_code}  {r['href']}")
            continue
        with open(path, "w") as f:
            f.write(resp.text)
        if i % 25 == 0:
            print(f"  {i}/{len(rows)}")
        time.sleep(SLEEP)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "discover"
    {"discover": discover, "fetch": fetch}[cmd]()
