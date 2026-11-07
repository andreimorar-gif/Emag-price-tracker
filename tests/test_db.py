import pytest

from tracker import db
from tracker.exceptions import DatabaseConnectionException
from tracker.scraper import PriceInfo

URL = "https://www.emag.ro/test/pd/xyz/"

def test_connect_returns_the_connection(monkeypatch):
    monkeypatch.setattr(db.pyodbc, 'connect', lambda s: "fake connection")
    assert db.connect("anything")=="fake connection"

def test_connect_errors_raises_an_exception(monkeypatch):
    def failing_connect(s):
        raise db.pyodbc.Error("server not found")
    monkeypatch.setattr(db.pyodbc, 'connect', failing_connect)
    with pytest.raises(DatabaseConnectionException) as e:
        db.connect("anything")
    assert "Could not connect to SQL Server" in str(e.value)
    assert isinstance(e.value.__cause__, db.pyodbc.Error)

def test_connect_raises_an_exception(monkeypatch):
    with pytest.raises(DatabaseConnectionException):
        db.connect("DRIVER={doesn't exist};SERVER=no")

def test_same_email_gives_same_user(conn):
    first_id = db.get_or_create_user(conn,"abc@gmail.com")
    second_id = db.get_or_create_user(conn,"abc@gmail.com")
    assert first_id == second_id

def test_different_email_gives_different_user(conn):
    first_id = db.get_or_create_user(conn,"abc@gmail.com")
    second_id = db.get_or_create_user(conn,"xyz@gmail.com")
    assert first_id != second_id

def test_same_url_gives_same_product(conn):
    first_id = db.get_or_create_product(conn,URL)
    second_id = db.get_or_create_product(conn,URL)
    assert first_id == second_id

def test_different_url_gives_different_product(conn):
    first_id = db.get_or_create_product(conn,URL)
    second_id = db.get_or_create_product(conn,"https://www.emag.ro/test/pd/abc/")
    assert first_id != second_id

def test_long_product_names_are_cut_off(conn):
    product_id = db.get_or_create_product(conn,URL)
    db.update_product_name(conn,product_id,"x"*300)
    row = db.run_select_one(conn,"SELECT name FROM products WHERE id = ?",[product_id])
    assert len(row["name"])==255

def test_tracking_twice_updates(conn):
    user_id = db.get_or_create_user(conn,"a@gmail.com")
    product_id = db.get_or_create_product(conn,URL)
    db.track(conn,user_id,product_id,999)
    db.track(conn,user_id,product_id,800)
    rows = db.run_select(conn, "SELECT target_price FROM tracked_products")
    assert len(rows)==1
    assert rows[0]["target_price"]==800

def test_untrack_removes_product(conn):
    user_id = db.get_or_create_user(conn, "a@gmail.com")
    product_id = db.get_or_create_product(conn,URL)
    db.track(conn,user_id,product_id)
    db.untrack(conn,"a@gmail.com",product_id)
    assert db.run_select(conn,"SELECT * FROM tracked_products") == []

def test_untrack_unkown_user_does_nothing(conn):
    db.untrack(conn,"random@gmail.com",1)

def test_only_tracked_products_are_checked(conn):
    user_id = db.get_or_create_user(conn,"a@gmail.com")
    product_id = db.get_or_create_product(conn,URL)
    db.get_or_create_product(conn,"https://www.emag.ro/test/pd/abc/")
    db.track(conn,user_id,product_id)
    products=db.products_to_check(conn)
    assert len(products)==1
    assert products[0]["id"]==product_id

def test_latest_price_is_none_before_check(conn):
    product_id = db.get_or_create_product(conn,URL)
    assert db.latest_price(conn,product_id) is None

def test_latest_price_skips_checks_without_price(conn):
    product_id = db.get_or_create_product(conn,URL)
    db.record_price(conn,product_id,PriceInfo(price=800.0,priceCurrency="RON"))
    db.record_price(conn,product_id,PriceInfo(price=None,in_stock=False))
    assert db.latest_price(conn,product_id) == 800.0

def test_record_price_saves_every_column(conn):
    product_id = db.get_or_create_product(conn,URL)
    db.record_price(conn,product_id,PriceInfo(price=800.0,priceCurrency="RON",seller="eMAG",in_stock=True))
    row=db.run_select_one(conn,
                        """
                            SELECT price,currency,seller,in_stock
                            FROM price_history
                            WHERE product_id = ?
                            """,
                    [product_id]
    )
    assert row["price"]==800.0
    assert row["currency"]=="RON"
    assert row["seller"]=="eMAG"
    assert row["in_stock"] is True

def test_watchers_lists(conn):
    product_id = db.get_or_create_product(conn,URL)
    for email in ["a@gmail.com","b@gmail.com"]:
        db.track(conn,db.get_or_create_user(conn,email),product_id,1000)
    emails = sorted(row["email"] for row in db.watchers(conn,product_id))
    assert emails==["a@gmail.com","b@gmail.com"]