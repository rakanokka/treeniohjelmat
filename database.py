import sqlite3
import config
from flask import g

def get_connection() -> sqlite3.Connection | None:
    try:
        connection = sqlite3.connect(config.DATABASE_FILENAME)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sqlite3.Row
        return connection
    except Exception as e:
        print(str(e)) 
    return None

def query_with(connection: sqlite3.Connection, sql: str, params = []) -> list[dict]:
    try:
        return connection.execute(sql, params).fetchall()
    except Exception as e:
        print(str(e)) 
    return []

def query(sql: str, params = []) -> list[dict]:
    connection = get_connection()
    result = []
    if connection:
        try:
            result = connection.execute(sql, params).fetchall()
        except Exception as e:
            print(str(e)) 
        finally:
            connection.close()
    return result

def execute_insert_with(connection: sqlite3.Connection, sql: str, params = []) -> int:
    result = -1
    try:
        c = connection.execute(sql, params)
        connection.commit()
        result = c.lastrowid
    except Exception as e:
        print(str(e))
    return result or -2

def execute_updel_with(connection: sqlite3.Connection, sql: str, params = []) -> int:
    result = -1
    try:
        c = connection.execute(sql, params)
        connection.commit()
        result = c.rowcount
    except Exception as e:
        print(str(e))
    return result

def execute(sql: str, params = []) -> bool:
    connection = get_connection()
    if connection:
        try:
            c = connection.execute(sql, params)
            connection.commit()
            g.insert_id = c.lastrowid
            g.row_count = c.rowcount
            return True
        except Exception as e:
            print(str(e))
        finally:
            connection.close()
    return False

def row_count() -> int:
    return g.row_count

