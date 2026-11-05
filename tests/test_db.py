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