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

def test_console_notifier_prints_alert(capsys):
    ConsoleNotifier().send("a@gmail.com","Price drop","New price: 400.00 RON")
    captured = capsys.readouterr().out
    assert "a@gmail.com" in captured
    assert "Price drop" in captured
    assert "New price: 400.00 RON" in captured

class FakeSesClient:
    def __init__(self,should_fail=False):
        self.should_fail = should_fail
        self.calls=[]

    def send_email(self,**kwargs):
        if self.should_fail:
            raise RuntimeError("Email address not verified")
        self.calls.append(kwargs)

def test_email_notifier_sends_alert():
    client = FakeSesClient()
    email_notifier = EmailNotifier("me@gmail.com","eu-central-1",client)
    email_notifier.send("a@gmail.com","Price drop","New price: 400.00 RON")

    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["Source"] == "me@gmail.com"
    assert call["Destination"] == {"ToAddresses": ["a@gmail.com"]}
    assert call["Message"]["Subject"]["Data"]=="Price drop"
    assert call["Message"]["Body"]["Text"]["Data"]=="New price: 400.00 RON"

def test_email_failure_raises_exception():
    client = FakeSesClient(should_fail=True)
    email_notifier=EmailNotifier("me@gmail.com","eu-central-1",client)
    with pytest.raises(NotificationException) as e:
        email_notifier.send("a@gmail.com","Price drop","New price: 400.00 RON")
    assert "a@gmail.com" in str(e.value)

def test_without_ses_sender_alerts_printed(monkeypatch):
    monkeypatch.delenv("SES_SENDER", raising=False)
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    assert isinstance(get_notifier(), ConsoleNotifier)

def test_empty_ses_sender_results_not_set(monkeypatch):
    monkeypatch.setenv("SES_SENDER", "")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    assert isinstance(get_notifier(), ConsoleNotifier)

def test_with_ses_email_are_sent(monkeypatch):
    monkeypatch.setenv("SES_SENDER", "me@gmail.com")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")

    result = get_notifier()
    assert isinstance(result, EmailNotifier)
    assert result.sender == "me@gmail.com"
    assert result.client.meta.region_name == "eu-central-1"