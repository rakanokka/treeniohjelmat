import sqlite3
from typing import Any
from pathlib import Path
from flask import g
from .utils import debug_output

CONNECTION_KEY = "sqlite_connection"

def get_sql_connection(path: Path) -> sqlite3.Connection:
    if not(CONNECTION_KEY in g):
        debug_output("Connecting to database...")
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        setattr(g, CONNECTION_KEY, connection)
    return getattr(g, CONNECTION_KEY)

def close_sql_connection(e = None):
    connection = g.pop(CONNECTION_KEY, None)
    if not(connection is None):
        debug_output("Closing database...")
        connection.close()


class SqlQueryHandler:

    def __init__(self, filepath: str):
        self.db_path = Path(filepath)

    # TODO: SqlQueryResult type
    def execute_sql(self, sql: str) -> Any:
        connection = get_sql_connection(self.db_path)
        result = connection.execute(sql)
        connection.commit()
        return result

    def execute_sql_params(self, sql: str, params: list[str]) -> Any:
        connection = get_sql_connection(self.db_path)
        result = connection.execute(sql, params)
        connection.commit()
        return result   

    def execute_sql_file(self, filepath: str):
        connection = get_sql_connection(self.db_path)
        with open(Path(filepath), mode="r", encoding="utf-8") as file:
            connection.executescript(file.read())

    def insert_user(self, username: str, email: str, pw_hash: str):
        sql = 'INSERT INTO "user" (username, email, password_hash) VALUES (?, ?, ?)'
        self.execute_sql_params(sql, [username, email, pw_hash])

    def get_user_by_username(self, username: str) -> Any:
        sql = 'SELECT id, password_hash FROM "user" WHERE username = ?'
        rows = self.execute_sql_params(sql, [username])
        # TODO: Sanity check
        return rows.fetchone()

sql_handler = SqlQueryHandler("database/xfit_dev.db")
