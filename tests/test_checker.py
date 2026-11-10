from tracker import db
from tracker.checker import should_notify, check_product
from tracker.exceptions import NotificationException

URL = "https://www.emag.ro/test/pd/xyz/"

def test_price_drop_alerts():
    assert should_notify(100,90,None,None) is True

def test_price_increase_alerts():
    assert should_notify(90,100,None,None) is True

def test_same_price_does_not_alert():
    assert should_notify(100,100,None,None) is False

def test_first_check_without_target_does_not_alert():
    assert should_notify(None,100,None,None) is False

def test_no_price_does_not_alert():
    assert should_notify(100,None,None,None) is False

def test_drop_when_above_target_does_not_alert():
    assert should_notify(100,90,80,None) is False

def test_reaching_target_alerts():
    assert should_notify(100,90,90,None) is True

def test_price_increase_with_target_does_not_alert():
    assert should_notify(90,100,80,None) is False

def test_same_target_alert_is_not_sent_twice():
    assert should_notify(100,80,90,80) is False

def test_lower_price_below_target_alerts_again():
    assert should_notify(80,70,90,80) is True

def follow(conn,email,url,target_price=None):
    user_id = db.get_or_create_user(conn,email)
    product_id = db.get_or_create_product(conn,url)
    db.track(conn,user_id,product_id,target_price)
    for product in db.products_to_check(conn):
        if product["id"]==product_id:
            return product

def check_prices(conn,product,shop,notifier,prices):
    for price in prices:
        shop.prices[product["url"]] = price
        check_product(conn,product,notifier,shop.get_price)

class NotifierFailingFor:
    def __init__(self,bad_address):
        self.bad_address = bad_address
        self.sent=[]

    def send(self,to,subject,body):
        if to==self.bad_address:
            raise NotificationException(f"{to} is not verified")
        self.sent.append((to,subject,body))

def test_one_change_sends_one_alert(conn,fake_shop,fake_notifier):
    product = follow(conn,"a@gmail.com",URL)
    check_prices(conn,product,fake_shop,fake_notifier,[100,100,90,90])
    assert len(fake_notifier.sent)==1
    to,subject,body = fake_notifier.sent[0]
    assert to=="a@gmail.com"
    assert subject.startswith("Price drop")
    assert "90" in subject

def test_every_change_alerts(conn,fake_shop,fake_notifier):
    product = follow(conn, "a@gmail.com", URL)
    check_prices(conn, product, fake_shop, fake_notifier, [100, 90, 100, 90])
    assert len(fake_notifier.sent) == 3
    subjects=[subject for to,subject,body in fake_notifier.sent]
    assert subjects[0].startswith("Price drop")
    assert subjects[1].startswith("Price increase")
    assert subjects[2].startswith("Price drop")

def test_target_price(conn,fake_shop,fake_notifier):
    product = follow(conn, "a@gmail.com", URL, target_price=100)
    check_prices(conn, product, fake_shop, fake_notifier, [110, 105, 115, 90])
    assert len(fake_notifier.sent) == 1
    assert "90" in fake_notifier.sent[0][1]

def test_every_follower_gets_alerts(conn,fake_shop,fake_notifier):
    follow(conn,"a@gmail.com",URL)
    product = follow(conn, "b@gmail.com", URL)
    check_prices(conn, product, fake_shop, fake_notifier, [100, 90])
    notifications=sorted(to for to,subject,body in fake_notifier.sent)
    assert notifications == ["a@gmail.com","b@gmail.com"]

def test_every_check_is_saved(conn,fake_shop,fake_notifier):
    product = follow(conn, "a@gmail.com", URL)
    check_prices(conn, product, fake_shop, fake_notifier, [100, 90, 90])
    assert len(db.history(conn,product["id"])) == 3

def test_product_name_saved(conn,fake_shop,fake_notifier):
    product = follow(conn, "a@gmail.com", URL)
    check_prices(conn, product, fake_shop, fake_notifier, [100])
    assert db.list_tracked(conn)[0]["name"]=="Test product"

def test_failed_email_does_not_stop_other_alerts(conn,fake_shop):
    follow(conn,"bad@gmail.com",URL)
    product = follow(conn, "good@gmail.com", URL)
    notifier = NotifierFailingFor("bad@gmail.com")
    check_prices(conn, product, fake_shop, notifier, [100, 90])
    assert len(notifier.sent) == 1
    assert notifier.sent[0][0] == "good@gmail.com"