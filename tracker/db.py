import os
from decimal import Decimal
import pyodbc

from tracker.exceptions import DatabaseConnectionException

DEFAULT_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;DATABASE=EmagTracker;"
    "Trusted_Connection=yes;TrustServerCertificate=yes;"
)

SCHEMA = [
    """
    IF OBJECT_ID('users','U') IS NULL
    CREATE TABLE users (
        id INT PRIMARY KEY IDENTITY(1,1) ,
        email NVARCHAR(255) NOT NULL UNIQUE,
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    )
    """,
    """
    IF OBJECT_ID('products','U') IS NULL
    CREATE TABLE products (
        id INT PRIMARY KEY IDENTITY(1,1) ,
        url NVARCHAR(450) NOT NULL UNIQUE,
        name NVARCHAR(255), 
        created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    )
    """,
    """
    IF OBJECT_ID('tracked_products','U') IS NULL
    CREATE TABLE tracked_products (
        user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        target_price DECIMAL(10,2),
        last_notified_price DECIMAL(10,2),
        PRIMARY KEY(user_id,product_id)
    )
    """,
    """
    IF OBJECT_ID('price_history','U') IS NULL
    CREATE TABLE price_history (
        id INT PRIMARY KEY IDENTITY(1,1),
        product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        price DECIMAL(10,2),
        currency NVARCHAR(10),
        seller NVARCHAR(100),
        in_stock BIT NOT NULL,
        checked_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    )
    """,
    """
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_history_product_time')
    CREATE INDEX idx_history_product_time ON price_history (product_id, checked_at)
    """

]

def connect(connection_string=None):
    """
    :param connection_string:
    :return: either the ones past by the argument, from the .env.example file, or the default one from the top of the file
    """
    try:
        return pyodbc.connect(connection_string or os.getenv("DB_CONNECTION_STRING") or DEFAULT_CONNECTION_STRING)
    except pyodbc.Error as e:
        raise DatabaseConnectionException("Could not connect to SQL Server") from e


def init_db(conn):
    cursor = conn.cursor()
    for stmt in SCHEMA:
        cursor.execute(stmt)
    conn.commit()

def run_select(conn,sql,params=None):
    cursor = conn.cursor()
    if params is None:
        cursor.execute(sql)
    else:
        cursor.execute(sql, params)

    column_names=[]
    for column in cursor.description:
        column_names.append(column[0])

    result = []
    for row in cursor.fetchall():
        row_dict = {}
        for i in range(len(column_names)):
            value = row[i]
            if isinstance(value, Decimal):
                value = float(value)
            row_dict[column_names[i]] = value
        result.append(row_dict)
    return result

def run_select_one(conn,sql,params=None):
    rows = run_select(conn,sql,params)
    if len(rows) == 0:
        return None
    return rows[0]

def run_change(conn,sql,params=None):
    cursor = conn.cursor()
    if params is None:
        cursor.execute(sql)
    else:
        cursor.execute(sql, params)
    conn.commit()
    return cursor

def get_or_create_user(conn,email):
    existing = run_select_one(conn,"SELECT id FROM users WHERE email = ?",[email])
    if existing:
        return existing["id"]

    run_change(conn,"INSERT INTO users (email) VALUES (?)",[email])
    new_user = run_select_one(conn,"SELECT id FROM users WHERE email = ?",[email])
    return new_user["id"]

def get_or_create_product(conn,url):
    existing = run_select_one(conn,"SELECT id FROM products WHERE url = ?",[url])
    if existing:
        return existing["id"]

    run_change(conn,"INSERT INTO products (url) VALUES (?)",[url])
    new_product = run_select_one(conn,"SELECT id FROM products WHERE url = ?",[url])
    return new_product["id"]

def update_product_name(conn,product_id,name):
    run_change(conn,"UPDATE products SET name = ? WHERE id = ?",[name[:255],product_id])

def track(conn,user_id,product_id,target_price=None):
    existing = run_select_one(
        conn,
        "SELECT user_id FROM tracked_products WHERE user_id = ? AND product_id = ?",
        [user_id, product_id]
    )
    if existing:
        run_change(
            conn,
            "UPDATE tracked_products SET target_price = ? WHERE user_id = ? AND product_id = ?",
            [target_price, user_id, product_id]
        )
    else:
        run_change(
            conn,
            "INSERT INTO tracked_products (user_id, product_id,target_price) VALUES (?, ?, ?)",
            [user_id, product_id, target_price]
        )

def untrack(conn,email,product_id):
    user = run_select_one(conn,"SELECT id FROM users WHERE email = ?",[email])
    if not user:
        return
    run_change(
        conn,
        "DELETE FROM tracked_products WHERE user_id = ? AND product_id = ?",
        [user["id"], product_id]
    )

def products_to_check(conn):
    sql="""
        SELECT DISTINCT P.id, P.url, P.name
        FROM products P
        INNER JOIN tracked_products T ON P.id = T.product_id
        """
    return run_select(conn,sql)

def latest_price(conn,product_id):
    sql="""
    SELECT TOP 1 price
    FROM price_history
    WHERE product_id = ? AND price is not null
    ORDER BY checked_at DESC, id DESC
    """
    row=run_select_one(conn,sql,[product_id])
    if row is None:
        return None
    return row["price"]

def record_price(conn,product_id,info):
    sql="""
    INSERT INTO price_history (product_id, price, currency, seller, in_stock)
    VALUES (?, ?, ?, ?, ?)
    """
    if info.in_stock:
        in_stock = True
    else:
        in_stock = False
    run_change(conn,sql,[product_id,info.price,info.priceCurrency,info.seller,in_stock])

