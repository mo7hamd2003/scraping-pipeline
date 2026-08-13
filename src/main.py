from urllib.parse import urljoin, urlparse
from pathlib import Path
from bs4 import BeautifulSoup
import requests

DOMAIN_ROOT = "https://books.toscrape.com/"
CACHE_DIR = Path("cache")
MAX_PAGES = 3

HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0"
}


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


def crawl_catalogue(start_url: str, max_pages: int) -> None:
    url = start_url
    page_count = 0
    discovered_count = 0
    unique_links = set()

    while url and page_count < max_pages:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"page not found: {url}")
            break

        path = cache_path_for(url)
        path.write_text(resp.text, encoding="utf-8")
        print(f"CACHED page {page_count + 1}: {url}")

        soup = BeautifulSoup(resp.text, "html.parser")

        for book in soup.select("article.product_pod"):
            book_link = book.h3.a["href"]
            page_url = urljoin(url, book_link)
            discovered_count += 1
            unique_links.add(page_url)
            print(f"{discovered_count}. {page_url}")

        page_count += 1
        next_tag = soup.select_one("li.next a")
        url = urljoin(url, next_tag["href"]) if next_tag else None
    print(f"Catalogue_pages= {page_count}, Discovered= {discovered_count}, unique_url= {len(unique_links)}")


def main() -> None:
    CACHE_DIR.mkdir(exist_ok=True)

    if robots_exists(DOMAIN_ROOT):
        print("robots.txt exists")
    else:
        print("no robots file found")

    start_url = urljoin(DOMAIN_ROOT, "catalogue/page-1.html")
    crawl_catalogue(start_url, MAX_PAGES)


if __name__ == "__main__":
    main()