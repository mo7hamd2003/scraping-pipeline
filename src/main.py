from urllib.parse import urljoin, urlparse
from pathlib import Path

import requests
import urllib.robotparser as robotparser

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

domain_root = "https://books.toscrape.com/"
headers = {
    "User-Agent": "FlyRankInternshipA9/1.0"
}

def robots_exit(domain_root: str) -> bool:
    robots_url = urljoin(domain_root, "/robots.txt")
    resp = requests.get(robots_url)
    return resp.status_code == 200


def page_200(domain_root: str) -> bool:
    resp = requests.get(domain_root, headers=headers, timeout=10)
    return resp.status_code == 200

def save_to_cache(url: str):
    parse = urlparse(url)
    name = parse.path.strip("/").replace("/", "_") or "index"
    if not name.endswith(".html"):
        name += ".html"
    path = CACHE_DIR / name
    return path


def fetch_cache(url: str):
    path = save_to_cache(url)
    if path.exists():
        return path.read_text(encoding="utf-8")

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    path.write_text(resp.text, encoding='utf-8')
    return path
        
if robots_exit(domain_root):
    print("robots.txt exist")
else:
    print("no robots file found")

resp = urljoin(domain_root, "catalogue/tipping-the-velvet_999/index.html")
if page_200(resp):
    print("FETCH")
    fetch_cache(resp)
    print("CACHE HIT")
else:
    print("page not found")
