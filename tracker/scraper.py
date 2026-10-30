import json
from dataclasses import dataclass
from urllib.parse import urlparse

from tracker.exceptions import InvalidProductUrlException


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
        if "@graph" in data:
            products.extend(find_product_in_json(data["@graph"]))
    return products

