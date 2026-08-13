# Ambrook Funding Library: data-quality audit

**Jonah Rahn · 2026-08-06 · 395 programs scored across 377 organization pages**

Rubric, dataset, and crawler: github.com/Jonahrahn/ambrook-funding-audit

---

## The number

**81 program pages tell a farmer they were updated in the last five weeks, then show a deadline from a previous year.**

That is 22% of the 367 pages carrying an `Updated` date on or after July 1, 2026. The most extreme case is stamped `Updated July 23, 2026` above a deadline reading `Closed June 15, 2022`.

The library is not in bad shape overall: mean score 13.4 out of 15, and 122 programs score a perfect 15. The failures are concentrated, not systemic, which is why they are worth naming individually.

---

## 1. The `Updated` stamp is not a freshness signal

Four verified examples, each fetched twice:

| Program | Stamp | Deadline shown |
|---|---|---|
| Low Carbon Beef | Updated July 23, 2026 | Closed June 15, 2022 |
| California Urban Agriculture Grant | Updated July 23, 2026 | Closed October 23, 2023 |
| NC-SARE Farmer Rancher | Updated July 23, 2026 | Closed December 1, 2023 |
| Farm Labor Stabilization Pilot | Updated July 23, 2026 | Closed January 3, 2024 |

The stamp is not defined anywhere on the site or in the Help Center, so it is not a broken promise. But a farmer sees a recent date above program information and draws the obvious conclusion. For 81 programs that conclusion is wrong, and nothing on the page distinguishes them.

**Sharpest single case:** the Massachusetts Agricultural Energy Efficiency Program page was updated **three days ago**, shows a header status of `Closed May 7, 2026`, and its body still reads *"Check back in early 2022 to learn how to apply."*

## 2. Currency fields rendering as dates

Two pages run a dollar amount through a date parser:

- **Organic Certification Cost Share (OCCSP)** displays `Maximum Award Amount: January 1, 750`. The real cap is $750 per certification scope.
- **FACT Conference Scholarships** displays `January 1, 400`. The real award is up to $400.

A type-coercion bug, not a content problem, which makes it the cheapest thing here to fix and the easiest to detect: any value in that field not matching a currency pattern should fail a check.

## 3. One program, two records, two different maximum awards

Montana's Growth Through Agriculture program exists at two live URLs, each with its own canonical tag, neither redirecting:

- `/funding/montana-gta` → Maximum Award Amount **$150,000**
- `/funding/montana-growth-through-agriculture-program` → Maximum Award Amount **$100,000**

The $100,000 page contradicts itself: its own body reads *"a maximum total amount of $150,000 in the form of grant funding up to $50,000 and loan funding up to $100,000."* The loan sub-cap was promoted into the headline field. That is a diagnosable extraction error, not a typo, which means it will recur wherever a program has tiered instruments.

The same duplication exists for the AMS dairy donation program at `/funding/dairy-donation-program` and `/funding/milk-donation-reimbursement-program`.

## 4. Twenty-eight pages contradict themselves

Either the header status disagrees with the body text, or the page states two different maximum awards. Three verified money cases:

| Program | `Maximum Award Amount` field | Body text |
|---|---|---|
| Food Supply Chain Guaranteed Loans (FPEP) | $100,000,000 | "the maximum award amount is $150 million" |
| Frontera Farmer Foundation | $12,000 | "grants for capital improvements of up to $15,000" |
| W-SARE Professional + Producer | $85,000 | "cannot exceed $75,000 over the entire project period" |

The direction of the error is inconsistent, so this is not a rounding or truncation bug. Two overstate, one understates.

Header-versus-body contradictions include Utah Grazing Improvement (`Closed December 31, 2025` over a body listing a window that closed June 17, 2022) and Ohio Agriculture Growing Tomorrow (`Closed July 31, 2026` over *"Check back in early 2024"*).

## 5. Seventy deadlines with no year

18% of programs display a deadline as a month and day only: `Closed Aug 15`, `Due Sep 25`, `Aug 21`. The reader cannot tell which application cycle it refers to, and on August 6, a bare `Closed Aug 15` is ambiguous between nine days ago and nine days from now.

The North Dakota Soil Health Cover Crop page shows four year-less dates that conflict with each other: a September 15 deadline, a December 1 deadline, an August 31 planting date, and an October 1 application date.

## 6. Broken and misfiled entries

- The **NRCS organization page** links to `/funding/regen-pilot-program`, which returns **404**. A farmer browsing NRCS programs hits a dead end.
- **Slug conventions are not uniform.** Most programs are kebab-case, several are bare uppercase acronyms (`NAQI`, `UFSG`, `WLEI`), and Forest Legacy Program lives at `/funding/Forest%20Legacy%20Program` with literal spaces. Related: `/funding/EQIP` 404s while `/funding/eqip` resolves.
- **Two slugs are misfiled by state.** `de-scbgp` carries a Delaware prefix but is Rhode Island's Specialty Crop Block Grant. `mn-dpap` carries a Minnesota prefix but is a Montana program.
- **One slug does not match its page.** `low-carbon-beef-usda-pilot-program` renders a page titled "Low Carbon Technologies, Advancing Markets for Producers (AMP)."

## 7. Completeness gaps

| Gap | Count | Share |
|---|---|---|
| No funding amount shown | 68 | 17% |
| Links only to a form or third-party portal, not the agency's program page | 73 | 18% |
| No outbound source link at all | 22 | 6% |
| No eligibility information | 17 | 4% |

The 22 pages with no outbound link are the ones to fix first: a farmer who cannot reach the administering agency cannot verify anything or apply, and being the on-ramp is the Funding Library's whole job. By agency, NRCS is the weakest large publisher at 12.6 out of 15 across 27 programs, driven by missing funding figures and links resolving to office locators rather than program pages.

---

## What I would do about it

**Five checks, run weekly, catch all of it.** Every defect above is machine-detectable without a human reading a single page:

1. **Stamp-versus-deadline divergence.** Flag any page whose `Updated` date is more than 12 months later than the deadline it displays. Catches finding 1, **81 programs**. Nothing else on this list catches it, because those deadlines are internally coherent: June 15, 2022 really is in the past. The defect is the gap between the stamp and the content, which only shows up when you compare the two fields.
2. **Deadline coherence.** Flag any `Closed` date in the future, any `Due` date in the past, and any deadline string with no four-digit year. Catches finding 5 and the header-versus-body contradictions in finding 4, **93 programs** once the 6 that fail both tests are deduplicated.
3. **Field type validation.** Flag any `Maximum Award Amount` not matching a currency pattern. Catches finding 2 immediately, and would have caught it the day it shipped.
4. **Field-versus-body reconciliation.** Extract every dollar figure from the body, flag pages where the largest disagrees with the `Maximum Award Amount` field. Catches the money half of finding 4.
5. **Duplicate and link liveness.** Flag programs whose name normalizes to an existing record, and resolve every internal href and outbound source link. Catches findings 3 and 6.

**Then change what the stamp means.** The `Updated` date should reflect the last time the program's deadline and award data were verified against the source, not the last time the record was touched. If those are the same field today, splitting them costs one column and makes the number honest. If a re-verification pass is too expensive to run across 397 programs, showing nothing beats showing a date that means something other than what a farmer will read into it.

Checks 1 and 2 are worth more than the rest combined, because a wrong deadline is the only defect on this list that costs a farmer money.

---

## Method and limits

395 programs crawled from all 377 organization pages, each scored 1 to 3 on five criteria: freshness, deadline integrity, source traceability, funding specificity, eligibility completeness. Rubric written before scoring. Slugs harvested from live hrefs, never constructed, because Ambrook's conventions are not uniform enough to guess. Reference date pinned in code so scores reproduce. Full method, rubric, crawler, and the complete scored dataset are in the repo.

Every claim above was re-verified against the live page by an independent second pass. **One first-pass finding was withdrawn as a result:** I had reported Forest Legacy Program as a dead link when the page in fact resolves at a non-standard URL. Claims that did not reproduce twice were cut rather than softened.

**Not covered:** whether page content agrees with the administering agency. Criterion 3 asks whether the page points at the authority, not whether it matches. A primary-source reconciliation against fsa.usda.gov and nrcs.usda.gov is the obvious next pass and would find a different, probably larger class of error.

**On the disclaimer.** Every page carries: *"This information was gathered from public sources... All information is subject to change."* That covers stale third-party data, and it should. It does not cover a currency field rendering as `January 1, 750`, one program stored as two records with different maximums, or an organization page linking to a 404. Those are internal integrity defects, and they are what this report is about.

---

Jonah Rahn · jonah.rahn@gmail.com · 714-795-4872 · github.com/Jonahrahn
