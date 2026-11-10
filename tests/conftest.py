import os

import pytest
from dotenv import load_dotenv

from tracker import db
from tracker.exceptions import PageFetchException
from tracker.scraper import PriceInfo

load_dotenv()

@pytest.fixture
def conn():
    connection_string = os.getenv("TEST_DB_CONNECTION_STRING")
    if not connection_string:
        pytest.skip("No connection string provided")

    connection = db.connect(connection_string)
    db.init_db(connection)

    cursor = connection.cursor()
    cursor.execute("DELETE FROM price_history")
    cursor.execute("DELETE FROM tracked_products")
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM users")
    connection.commit()

    yield connection
    connection.close()

class FakeNotifier:
    def __init__(self):
        self.sent = []

    def send(self,to,subject,body):
        self.sent.append((to,subject,body))

class FakeShop:
    def __init__(self):
        self.prices = {}
        self.broken_urls = []

    def get_price(self,url):
        if url in self.broken_urls:
            raise PageFetchException(f"The shop is down: {url}")
        return PriceInfo(name="Test product",price=self.prices.get(url),priceCurrency="RON")

@pytest.fixture
def fake_notifier():
    return FakeNotifier()

@pytest.fixture
def fake_shop():
    return FakeShop()