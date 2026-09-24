import sqlite3
import config
from flask import g

def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(config.DATABASE_FILENAME)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection

def query(sql: str, params = []) -> list:
    connection = get_connection()
    result = connection.execute(sql, params).fetchall()
    connection.close()
    return result

def execute(sql: str, params = []):
    connection = get_connection()
    c = connection.execute(sql, params)
    connection.commit()
    g.insert_id = c.lastrowid
    connection.close()

def insert_id() -> int:
    return int(g.insert_id) if g.insert_id else -1
