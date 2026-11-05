import os

import pytest
from dotenv import load_dotenv

from tracker import db

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