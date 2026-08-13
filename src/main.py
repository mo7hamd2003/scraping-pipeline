import requests
from urllib.parse import urljoin
import urllib.robotparser as robotparser

domain_root = "https://books.toscrape.com/"


def robots_exit(domain_root: str) -> bool:
    robots_url = urljoin(domain_root, "/robots.txt")
    resp = requests.get(robots_url)
    return resp.status_code == 200


if robots_exit(domain_root):
    print("robots.txt exist")
else:
    print("no robots file found")


