# scraper

A small scraping exercise against a site built for exactly this purpose.

## Target classification

- **Site:** `books.toscrape.com`
- **Why this site:** Its parent site, `toscrape.com`, states directly that Books to Scrape is a fictional bookstore built to be scraped a sandbox for people learning or testing scraping tools. There's no real business, no real inventory, no real customer behind it.
- **Scope:** The first 3 catalogue pages only (`/catalogue/a-light-in-the-attic_1000/index.html` through `soumission_998/index.html`), roughly 60 books out of the 1000 on the site.
- **Data collected:** Title, price, star rating, and stock availability for each book on those 3 pages.
- **Why this is appropriate:** The site exists specifically to absorb scraping traffic. Limiting the run to 3 pages is a self-imposed cap there's no rate limit or ban risk here, but practicing "take only what you need" as a default habit matters more than the target does.

## robots.txt

Requested `https://books.toscrape.com/robots.txt` once.

**Result: 404  no robots file found.**

A missing `robots.txt` is not a green light. It just means the site hasn't published crawl rules silence, not permission. The actual permission for this exercise comes from the site's own description of itself as a scraping sandbox (see above), not from the absence of a robots file.

## Checkpoint

Target: `books.toscrape.com`. Scope: first 3 catalogue pages. Robots result: no robots file found (404).

I will not reuse this code on another site without checking its rules and terms first.