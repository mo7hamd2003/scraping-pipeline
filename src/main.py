from urllib.parse import urljoin, urlparse
from pathlib import Path
from pydantic import BaseModel, ValidationError
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import json
import re

DOMAIN_ROOT = "https://books.toscrape.com/"
CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("output")
BOOKS_FILE = OUTPUT_DIR / "books.json"
ERRORS_FILE = OUTPUT_DIR / "errors.json"
MAX_PAGES = 3

HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0"
}


class Schema(BaseModel):
    product_url: str
    title: str | None
    price: str | None
    price_gbp: float | None
    availability: str | None
    rating: str | None
    description: str | None
    source_page: str
    fetched_at: datetime


def robots_exists(domain_root: str) -> bool:
    """Check whether robots.txt exists at the domain root."""
    robots_url = urljoin(domain_root, "/robots.txt")
    resp = requests.get(robots_url, headers=HEADERS, timeout=10)
    return resp.status_code == 200


def cache_path_for(url: str) -> Path:
    """Turn a URL into a deterministic filename under CACHE_DIR."""
    parsed = urlparse(url)
    name = parsed.path.strip("/").replace("/", "_") or "index"
    if not name.endswith(".html"):
        name += ".html"
    return CACHE_DIR / name


def crawl_catalogue(start_url: str, max_pages: int) -> set | None:
    """Crawl the catalogue starting from the given URL, up to max_pages."""
    url = start_url
    page_count = 0
    discovered_count = 0
    unique_links = set()

    try:
        while url and page_count < max_pages:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()

            path = cache_path_for(url)
            path.write_text(resp.text, encoding="utf-8")
            print(f"CACHED page {page_count + 1}: {url}")

            soup = BeautifulSoup(resp.text, "html.parser")

            for book in soup.select("article.product_pod"):
                book_link = book.h3.a["href"]
                page_url = urljoin(url, book_link)
                discovered_count += 1
                unique_links.add(page_url)

            page_count += 1
            next_tag = soup.select_one("li.next a")
            url = urljoin(url, next_tag["href"]) if next_tag else None

        print(f"Catalogue_pages={page_count}, Discovered={discovered_count}, unique_url={len(unique_links)}")
        return unique_links

    except requests.exceptions.HTTPError as err:
        if resp.status_code == 404:
            print(f"page not found: {url}")
        elif 500 <= resp.status_code < 600:
            print(f"server error: {err}")
        else:
            print(err)
        return None

    except requests.exceptions.RequestException as err:
        print(f"request failed: {err}")
        return None


def fetch_product(url: str) -> dict | None:
    """Fetch and parse a single product detail page."""
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        print(f"page not found: {url}")
        return None

    path = cache_path_for(url)
    path.write_text(resp.text, encoding="utf-8")

    soup = BeautifulSoup(resp.text, "html.parser")

    title = soup.select_one("div.product_main h1").get_text(strip=True)
    price = soup.select_one("p.price_color").get_text(strip=True)
    numeric_price = float(re.sub(r"[^0-9.]", "", price))
    availability = soup.select_one("p.availability").get_text(strip=True)
    rating_tag = soup.select_one("p.star-rating")
    rating = rating_tag.get("class", [])[-1] if rating_tag else ""

    desc_tag = soup.select_one("#product_description ~ p")
    description = desc_tag.get_text(strip=True) if desc_tag else ""

    source_page = url
    fetched_at = datetime.now()

    table_rows = soup.select("table.table.table-striped tr")
    extra_info = {row.th.get_text(strip=True): row.td.get_text(strip=True) for row in table_rows}

    return {
        "product_url": url,
        "title": title,
        "price": price,
        "price_gbp": numeric_price,
        "availability": availability,
        "rating": rating,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
        **extra_info,
    }


def load_existing_urls(path: Path) -> set:
    """Read product_url values already stored in books.json, so reruns
    skip books we already have instead of re-fetching and re-appending them."""
    if not path.exists():
        return set()

    urls = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                urls.add(record["product_url"])
            except (json.JSONDecodeError, KeyError):
                continue
    return urls


def compare_and_store(info: dict) -> None:
    """Validate against the schema and append to books.json (or errors.json)."""
    try:
        validated = Schema.model_validate(info)

        with open(BOOKS_FILE, "a", encoding="utf-8") as f:
            json.dump(validated.model_dump(mode="json"), f, ensure_ascii=False)
            f.write("\n")

        print(f"VALID: {validated.title}")

    except ValidationError as e:
        error_record = {
            "data": info,
            "error": e.errors(),
        }

        with open(ERRORS_FILE, "a", encoding="utf-8") as f:
            json.dump(error_record, f, ensure_ascii=False, default=str)
            f.write("\n")

        print(f"INVALID: {info.get('product_url')}")
        print(e)


def main() -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    if robots_exists(DOMAIN_ROOT):
        print("robots.txt exists")
    else:
        print("no robots file found")

    start_url = urljoin(DOMAIN_ROOT, "catalogue/page-1.html")
    product_links = crawl_catalogue(start_url, MAX_PAGES)

    if product_links is None:
        print("Crawl failed — nothing to fetch. Stopping.")
        return

    existing_urls = load_existing_urls(BOOKS_FILE)
    print(f"{len(existing_urls)} book(s) already stored from previous runs")

    new_count = 0
    skipped_count = 0

    for link in product_links:
        if link in existing_urls:
            skipped_count += 1
            continue

        result = fetch_product(link)
        if result is not None:
            compare_and_store(result)
            existing_urls.add(link)
            new_count += 1

    print(f"\nNew: {new_count}, Skipped (already stored): {skipped_count}, Total known: {len(existing_urls)}")


if __name__ == "__main__":
    main()