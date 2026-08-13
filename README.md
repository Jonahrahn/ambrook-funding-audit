# Ambrook Funding Library: a data-quality audit

An unsolicited coverage and accuracy audit of the public [Ambrook Funding Library](https://ambrook.com/funding), run on 2026-08-06 against every program reachable from an organization page.

Nobody asked for this. I built it because I am applying for the Product Operations role, the Funding Library is the largest public data surface Ambrook owns, and reading a job description is a worse way to understand a product than auditing it.

**Findings summary: [FINDINGS.md](FINDINGS.md)**

## What was measured

397 programs across 377 organization pages. Each program page scored 1 to 3 on five criteria, maximum 15. The rubric is in [RUBRIC.md](RUBRIC.md) and was written before any page was scored.

| | |
|---|---|
| Programs scored | 395 |
| Mean score | 13.4 / 15 |
| Scoring a perfect 15 | 122 (31%) |
| Scoring 11 or below | 46 (12%) |

The library is in good shape overall. That is the point of publishing the distribution rather than a single number: the failures are concentrated, which means they are fixable without a rewrite.

## Headline finding

**The `Updated` stamp does not imply the deadline below it was checked.**

367 of 395 pages carry an `Updated` date on or after 2026-07-01. Of those, **81 display an application deadline from 2025 or earlier**. The most extreme is [Low Carbon Beef](https://ambrook.com/funding/low-carbon-beef-usda-pilot-program), stamped `Updated July 23, 2026` above a deadline reading `Closed June 15, 2022`.

A farmer reading a five-week-old timestamp reasonably concludes the program information under it is current. For 81 programs it is not, and there is no way to tell which 81 from the page.

## Method

```
python src/crawl.py discover   # walk 377 org pages, harvest program hrefs
python src/crawl.py fetch      # fetch each program page
python src/score.py            # apply RUBRIC.md, write data/scored_programs.csv
```

> **On the crawler, plainly.** The published dataset was collected through a different HTTP client than the one in `src/crawl.py`, because the environment the crawl ran in blocked direct outbound requests. `crawl.py` is a faithful reimplementation of the same two-stage method and emits the same schema, but **it has not been executed end to end against the live site.** Treat it as documentation of the method that happens to be runnable, not as the thing that produced the numbers.
>
> What did produce the numbers: `data/scored_programs.csv` is the record of what was observed on 2026-08-06, one row per program, and every claim in `FINDINGS.md` was re-verified by opening the live page a second time. The findings do not depend on the crawler being correct. The population count does, which is why the coverage caveat below is stated rather than glossed.

Three decisions worth stating, because they determine whether the numbers hold up:

**The population is defined by the organization walk, not the sitemap.** `ambrook.com/sitemap.xml` carries no `<lastmod>` data, mixes case variants of the same slug, and lists `/funding/` URLs that 404 (`/funding/EQIP` returns 404 while `/funding/eqip` resolves). The organization pages render server-side and their hrefs are the links a farmer can actually click. So the denominator here is "programs reachable by navigation," which is both reproducible and the number that matters to a user.

**Slugs are harvested from hrefs, never constructed.** Ambrook's slug conventions are not uniform: most are kebab-case, some are bare uppercase acronyms (`NAQI`, `UFSG`, `WLEI`), and at least one contains literal spaces (`/funding/Forest%20Legacy%20Program`). Constructing slugs from program names produces false 404s. My own first pass made exactly this mistake and reported Forest Legacy Program as a dead link before I caught it. It is excluded from the scored set and noted in the data as a slug-convention finding instead.

**The reference date is pinned to 2026-08-06 in code**, not read from the clock, so re-running this later against the same HTML reproduces the same scores.

## Files

| Path | What it is |
|---|---|
| `FINDINGS.md` | The two-page report |
| `RUBRIC.md` | Five criteria with explicit 1-3 definitions |
| `data/program_index.csv` | 397 programs: name, slug, agency, listing status |
| `data/scored_programs.csv` | Full scored dataset, one row per program, with the per-criterion scores and a defect note |
| `src/crawl.py` | Organization walk and program fetch |
| `src/score.py` | Rubric application |

## Scope and limits

- Scores measure **what the page displays**, not whether it agrees with the administering agency. C3 asks whether the page points at the authority, not whether it matches. A full primary-source reconciliation against fsa.usda.gov and nrcs.usda.gov is the obvious next pass and is not done here.
- The organization walk is near-complete but not provably exhaustive. Spot-checking against independently observed URLs suggested roughly a 2% residual miss rate, so expect a handful of programs beyond these 397.
- Every specific claim in `FINDINGS.md` was re-verified against the live page by a second pass before publication. One claim from the first pass was withdrawn as a result. Findings I could not reproduce twice were cut rather than softened.

## The disclaimer, quoted up front

Every program page carries this:

> "This information was gathered from public sources. Ambrook is not responsible for or able to affect the results of any financial programs listed, nor are they responsible for any incorrect information that is listed or is on the hyperlinked external sites. All information is subject to change."

That covers stale third-party source data, and it should. It does not cover a currency field rendering as `January 1, 750`, one Montana program stored as two records with different maximum awards, or an organization page linking to a URL that 404s. Those are internal data-integrity defects, and they are what this audit is about.

---

Jonah Rahn · jonah.rahn@gmail.com · [github.com/Jonahrahn](https://github.com/Jonahrahn)
