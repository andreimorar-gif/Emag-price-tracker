import pytest

from tracker import notifier
from tracker.exceptions import NotificationException
from tracker.notifier import *

URL = "https://www.emag.ro/test/pd/xyz/"

def test_alert_for_price_drop():
    subject,body=format_alert("Laptop",URL,500,400,"RON")
    assert subject == "Price drop: Laptop is now 400.00 RON"
    assert "New price: 400.00 RON (-20%)" in body
    assert "Previous price: 500.00 RON" in body
    assert URL in body

def test_alert_for_price_increase():
    subject, body = format_alert("Laptop", URL, 400, 500, "RON")
    assert subject == "Price increase: Laptop is now 500.00 RON"
    assert "New price: 500.00 RON (+25%)" in body
    assert "Previous price: 400.00 RON" in body
    assert URL in body

def test_alert_without_previous_price():
    subject, body = format_alert("Laptop", URL, None, 400, "RON")
    assert subject == "Price drop: Laptop is now 400.00 RON"
    assert "New price: 400.00 RON" in body
    assert "Previous price" not in body
    assert URL in body

def test_alert_with_missing_name_and_currency():
    subject, body = format_alert(None, URL, 500, 400, None)
    assert subject == "Price drop: Your product is now 400.00 RON"