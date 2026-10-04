import sqlite3
import config
from flask import g

def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(config.DATABASE_FILENAME)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection

def query_with(connection: sqlite3.Connection, sql: str, params = []) -> list[dict]:
    result = connection.execute(sql, params).fetchall()
    return result

def query(sql: str, params = []) -> list[dict]:
    connection = get_connection()
    result = connection.execute(sql, params).fetchall()
    connection.close()
    return result

def execute_with(connection: sqlite3.Connection, sql: str, params = []) -> int:
    c = connection.execute(sql, params)
    connection.commit()
    return c.lastrowid or -1

def execute(sql: str, params = []):
    connection = get_connection()
    c = connection.execute(sql, params)
    connection.commit()
    g.insert_id = c.lastrowid
    g.row_count = c.rowcount
    connection.close()

def insert_id() -> int:
    return g.insert_id or -1

def row_count() -> int:
    return g.row_count
