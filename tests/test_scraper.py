import pytest
import requests

from tracker import scraper
from tracker.exceptions import InvalidProductUrlException, PageFetchException
from tracker.scraper import parse_price, clean_product_url, extract_price


def test_parse_price():
    assert parse_price("12.99")==12.99
    assert parse_price("12")==12.0
    assert parse_price(12.99)==12.99
    assert parse_price("") is None
    assert parse_price(None) is None
    assert parse_price("abc") is None
    assert parse_price({"value":5}) is None

def test_clean_url_removes_last_part():
    url="https://www.emag.ro/test/pd/xyz/?ref=other_customers_viewed_go_3_4&provider="
    assert clean_product_url(url)=="https://www.emag.ro/test/pd/xyz/"

def test_clean_url_rejects_bad_links():
    with pytest.raises(InvalidProductUrlException):
        clean_product_url("www.emag.ro/test/pd/xyz/")
    with pytest.raises(InvalidProductUrlException):
        clean_product_url("abcdefg")
    with pytest.raises(InvalidProductUrlException):
        clean_product_url("")

def test_clean_url_rejects_other_shops():
    with pytest.raises(InvalidProductUrlException):
        clean_product_url("https://www.altex.ro/test/pd/xyz/")

def test_clean_url_one_form():
    expected = "https://www.emag.ro/test/pd/xyz/"
    assert clean_product_url("http://emag.ro/test/pd/xyz/")==expected
    assert clean_product_url("https://WWW.EMAG.RO/test/pd/xyz/")==expected

PAGE_IN_STOCK="""
<html><head>
<script type="application/ld+json"> 
{
"@context": "http://schema.org",
"@type": "Product",
"name": "Telefon mobil Samsung Galaxy S26 Ultra",
"offers": {
        "@type": "Offer",
        "url": "https://www.emag.ro/telefon-mobil-samsung-galaxy-s26-ultra-dual-sim-12gb-ram-256gb-5g-black-sm-s948bzkdeue/pd/DRWGTB2BM/",
        "availability": "http://schema.org/InStock",
        "price": "5619.94",
        "priceCurrency": "RON",
        "seller": {
            "@type": "Organization",
            "name": "eMAG"
        }
    }
}
</script>
</head><body></body></html>
"""

PAGE_OUT_OF_STOCK="""
<html><head>
<script type="application/ld+json"> 
{
"@context": "http://schema.org",
"@type": "Product",
"name": "Telefon mobil Samsung Galaxy S25 Ultra",
"offers": {
        "@type": "Offer",
        "url": "https://www.emag.ro/telefon-mobil-samsung-galaxy-s25-ultra-dual-sim-12gb-ram-256gb-5g-black-sm-s948bzkdeue/pd/DRWGTB2BM/",
        "availability": "http://schema.org/OutOfStock",
        "price": "4619.94",
        "priceCurrency": "RON",
        "seller": {
            "@type": "Organization",
            "name": "eMAG"
        }
    }
}
</script>
</head><body></body></html>
"""

PAGE_WITHOUT_JSON="""
<html><body><h1>Padge</h1></body></html>
"""

PAGE_WITH_BROKEN_JSON="""
<html><head>
<script type="application/ld+json"> 
{ DAUKDYGGAUYDA
</script>
</head><body></body></html>
"""

def test_page_in_stock():
    info = extract_price(PAGE_IN_STOCK)
    assert info.name == "Telefon mobil Samsung Galaxy S26 Ultra"
    assert info.price == 5619.94
    assert info.priceCurrency == "RON"
    assert info.seller == "eMAG"
    assert info.in_stock == True
    assert info.source == "json-ld"

def test_page_out_of_stock():
    info = extract_price(PAGE_OUT_OF_STOCK)
    assert info.price == 4619.94
    assert info.in_stock == False

def test_page_with_broken_json():
    info = extract_price(PAGE_WITH_BROKEN_JSON)
    assert info.price is None

def test_page_without_json():
    info = extract_price(PAGE_WITHOUT_JSON)
    assert info.price is None
    assert info.in_stock == False
    assert info.source == "none"

class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text

def test_download_returns_the_page(monkeypatch):
    monkeypatch.setattr(scraper.requests, "get", lambda url, **kwargs: FakeResponse(200, "<html>ok</html>"))
    assert scraper.download_page("https://www.emag.ro/test/pd/xyz/") == "<html>ok</html>"

@pytest.mark.parametrize("status_code", [403,429])
def test_download_blocked_raises_exception(monkeypatch,status_code):
    monkeypatch.setattr(scraper.requests, "get", lambda url, **kwargs: FakeResponse(status_code))
    with pytest.raises(PageFetchException) as e:
        scraper.download_page("https://www.emag.ro/test/pd/xyz/")
    assert f"Request blocked (HTTP {status_code})" in str(e.value)

def test_download_missing_page_raises_exception(monkeypatch):
    monkeypatch.setattr(scraper.requests, "get", lambda url, **kwargs: FakeResponse(404))
    with pytest.raises(PageFetchException) as e:
        scraper.download_page("https://www.emag.ro/test/pd/xyz/")
    assert "Page not found (HTTP 404)" in str(e.value)

@pytest.mark.parametrize("status_code", [400,401,500,502,503])
def test_download_page_error(monkeypatch, status_code):
    monkeypatch.setattr(scraper.requests, "get", lambda url, **kwargs: FakeResponse(status_code))
    with pytest.raises(PageFetchException) as e:
        scraper.download_page("https://www.emag.ro/test/pd/xyz/")
    assert f"Page error (HTTP {status_code})" in str(e.value)

def test_download_without_internet_raises_exception(monkeypatch):
    def no_internet(url, **kwargs):
        raise requests.ConnectionError()
    monkeypatch.setattr(scraper.requests, "get", no_internet)
    with pytest.raises(PageFetchException) as e:
        scraper.download_page("https://www.emag.ro/test/pd/xyz/")

def test_get_price(monkeypatch):
    monkeypatch.setattr(scraper.requests, "get", lambda url, **kwargs: FakeResponse(200,PAGE_IN_STOCK))
    info = scraper.get_price("https://www.emag.ro/test/pd/xyz/")
    assert info.price == 5619.94

