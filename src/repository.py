import sqlite3
from typing import Any, cast
from pathlib import Path
from flask import g, current_app
from .utils import debug_output, get_filepath, debug_assert

class SqlHandler:
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    def connect(self) -> sqlite3.Connection:
        debug_output("Trying to connect to database...")
        if not ("db" in g):
            debug_output("Connecting to database...")
            g.db = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            g.db.row_factory = sqlite3.Row 
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db

    def close_connection(self):
        debug_output("Trying to close database...")
        db = g.pop("db", None)
        if not (db is None):
            debug_output("Closing database...")
            db.close()

    # TODO: SqlQueryResult type
    def execute_sql(self, sql: str, params: list[str]) -> Any:
        connection = self.connect()
        result = connection.execute(sql, params)
        connection.commit()
        return result   

    def execute_file(self, sql_filename: str):
        connection = self.connect()
        with current_app.open_resource(sql_filename) as file:
            connection.executescript(file.read().decode("utf8"))

    def insert_user(self, username: str, email: str, pw_hash: str):
        sql = 'INSERT INTO "user" (username, email, password_hash) VALUES (?, ?, ?)'
        self.execute_sql(sql, [username, email, pw_hash])

    def get_user_by_username(self, username: str) -> Any:
        sql = 'SELECT id, password_hash FROM "user" WHERE username = ?'
        result = self.execute_sql(sql, [username]).fetchone()
        return result

path_result = get_filepath("database/xfit.db")
debug_assert(path_result.valid, path_result.error)
sql_handler = SqlHandler(cast(Path, path_result.path))


