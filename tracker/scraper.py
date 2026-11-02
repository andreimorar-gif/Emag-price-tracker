import json
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from tracker.exceptions import InvalidProductUrlException, PageFetchException

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    )
}

@dataclass
class PriceInfo:
    name: str | None = None
    price: float | None = None
    currency: str | None = None
    seller: str | None = None
    in_stock: bool = True
    source: str = "none"

def clean_product_url(url: str) -> str:
    url=url.strip()
    parts=urlparse(url)
    if parts.scheme not in ["http", "https"] or parts.netloc == "":
        raise InvalidProductUrlException(f"Invalid product url: {url}")
    domain = parts.netloc.lower()
    if domain not in ["www.emag.ro", "emag.ro"]:
        raise InvalidProductUrlException(f"Invalid product url: {url}")
    return f"https://www.emag.ro{parts.path}"

def parse_price(text:str):
    if text is None:
        return None
    try:
        return float(text)
    except (TypeError,ValueError):
        return None

def find_product_in_json(data):
    products=[]
    if isinstance(data, list):
        for item in data:
            products.extend(find_product_in_json(item))
    elif isinstance(data, dict):
        data_type=data.get("@type")
        if data_type == "Product" or (isinstance(data_type,list) and "Product" in data_type):
            products.append(data)
        #this is not needed for eMAG because they don't use this graph,
        #but is good to have, other sites use it
        if "@graph" in data:
            products.extend(find_product_in_json(data["@graph"]))
    return products

def extract_price(html):
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data=json.loads(script.string or "")
        except json.decoder.JSONDecodeError:
            continue
        for product in find_product_in_json(data):
            offers=product.get("offers") or {}
            price=parse_price(offers.get("price"))
            if price is None:
                continue
            seller=offers.get("seller") or {}
            availability=offers.get("availability") or ""

            return PriceInfo(
                name=product.get("name"),
                price=price,
                currency=offers.get("priceCurrency"),
                seller=seller.get("name"),
                in_stock="OutOfStock" not in availability,
                source="json-ld"
            )
    return PriceInfo(in_stock=False)

def download_page(url,timeout=20):
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
    except requests.RequestException as e:
        raise PageFetchException(f"Network problem ({type(e).__name__}): {url}") from e

    if response.status_code in (403,429):
        raise PageFetchException(f"Request blocked (HTTP {response.status_code}): {url}")
    if response.status_code == 404:
        raise PageFetchException(f"Page not found (HTTP 404): {url}")
    if response.status_code >= 400:
        raise PageFetchException(f"Page error (HTTP {response.status_code}): {url}")
    return response.text

def get_price(url):
    html = download_page(url)
    return extract_price(html)