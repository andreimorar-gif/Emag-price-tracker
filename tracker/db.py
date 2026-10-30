import os
from decimal import Decimal
import pyodbc

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
        old_price DECIMAL(10,2),
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