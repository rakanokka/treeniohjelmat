import sqlite3
import config
from flask import g

def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(config.DATABASE_FILENAME)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection

def query(sql: str, params = []) -> list[dict]:
    connection = get_connection()
    rows = connection.execute(sql, params).fetchall()
    connection.close()
    return rows

def execute_insert(sql: str, params = []) -> int | None:
    connection = get_connection()
    c = connection.execute(sql, params)
    connection.commit()
    insert_id = c.lastrowid
    connection.close()
    return insert_id

def execute_updel(sql: str, params = []) -> int:
    connection = get_connection()
    c = connection.execute(sql, params)
    connection.commit()
    row_count = c.rowcount
    connection.close()
    return row_count

