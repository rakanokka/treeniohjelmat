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

    def execute_sql_params(self, sql: str, params: list) -> Any:
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

    # TODO: Ensure that we won't dereference a null pointer with all these rows.fetch calls
    # TODO: These get-functions should return a proper type
    def get_user_by_username(self, username: str) -> Any:
        sql = 'SELECT id, username, password_hash FROM "user" WHERE username = ?'
        rows = self.execute_sql_params(sql, [username])
        return rows.fetchone()

    def get_user_exercises(self, user_id: int) -> Any:
        sql = """
        SELECT 
            et.id,
            et.name,
            et.target_sets,
            et.target_reps,
            et.creator_id,
            u.username AS creator_name,
            (et.creator_id = ?) AS is_mine
        FROM exercise_template et
        JOIN "user" u ON et.creator_id = u.id
        ORDER BY 
            CASE WHEN et.creator_id = ? THEN 0 ELSE 1 END,
            et.name ASC; 
        """
        rows = self.execute_sql_params(sql, [user_id, user_id])
        return rows.fetchall()

    def get_all_exercises(self, user_id: int) -> Any:
        sql = """
        SELECT 
            et.id AS template_id,
            et.name AS exercise_name,
            et.target_sets,
            et.target_reps,
            et.order_index,
            et.creator_id,
            u.username AS creator_name,
            wst.description AS workout_template_name
        FROM exercise_template et
        JOIN "user" u ON et.creator_id = u.id
        LEFT JOIN workout_session_template wst ON et.session_template_id = wst.id
        WHERE et.creator_id != ?
        ORDER BY et.name ASC;
        """
        rows = self.execute_sql_params(sql, [user_id])
        return rows.fetchall()

sql_handler = SqlQueryHandler("database/xfit_dev.db")
