import sqlite3
from typing import Any, NamedTuple, cast
from pathlib import Path
from flask import g
from .utils import debug_assert, debug_output

CONNECTION_KEY = "sqlite_connection"

# These calls may fail for all sorts of reasons.
# In a real app we would resolve the error but in this implementation 
# we just kill the app if the request to the db server fails. 
def get_sql_connection(path: Path) -> sqlite3.Connection:
    if not(CONNECTION_KEY in g):
        debug_assert(path.exists(), f"Invalid database path: {path}")
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

class SqlQueryCursor:
    def __init__(self, cursor: sqlite3.Cursor | None, error = None):
        self.error = error
        self.cursor = cursor

    def valid(self) -> bool:
        return self.error is None

    def error_message(self) -> str:
        debug_assert(not self.valid())
        return str(self.error)

    def one(self) -> Any:
        debug_assert(self.valid())
        return cast(sqlite3.Cursor, self.cursor).fetchone()

    def all(self) -> Any:
        debug_assert(self.valid())
        return cast(sqlite3.Cursor, self.cursor).fetchall()

class SqlQueryResult(NamedTuple):
    success: bool
    data: Any

class SqlQueryHandler:

    def __init__(self, filepath: str):
        self.db_path = Path(filepath)

    def execute_sql(self, sql: str) -> SqlQueryCursor:
        try:
            connection = get_sql_connection(self.db_path)
            cursor = connection.execute(sql)
            connection.commit()
            return SqlQueryCursor(cursor)
        except Exception as e:
            return SqlQueryCursor(None, e)

    def execute_sql_params(self, sql: str, params: list) -> SqlQueryCursor:
        try:
            connection = get_sql_connection(self.db_path)
            cursor = connection.execute(sql, params)
            connection.commit()
            return SqlQueryCursor(cursor)
        except Exception as e:
            return SqlQueryCursor(None, e)

    def execute_sql_file(self, filepath: str):
        connection = get_sql_connection(self.db_path)
        with open(Path(filepath), mode="r", encoding="utf-8") as file:
            connection.executescript(file.read())
    
    # TODO: All exposed functions must return a result so that the UI can handle the possible error
    def insert_user(self, username: str, email: str, pw_hash: str):
        sql = 'INSERT INTO "user" (username, email, password_hash) VALUES (?, ?, ?)'
        self.execute_sql_params(sql, [username, email, pw_hash])

    def insert_exercise_template(self, user_id: int, name: str, target_sets: int, target_reps: int):
        sql = "INSERT INTO exercise_template (creator_id, workout_template_id, name, target_sets, target_reps, order_index) VALUES (?, NULL, ?, ?, ?, 0)"
        self.execute_sql_params(sql, [user_id, name, target_sets, target_reps])

    def insert_user_exercise_template(self, user_id: int, template_id: int):
        sql = """
        INSERT OR IGNORE INTO user_exercise_template (user_id, exercise_template_id) VALUES (?, ?);
        """
        self.execute_sql_params(sql, [user_id, template_id])

    def get_user_by_username(self, username: str) -> SqlQueryResult:
        sql = 'SELECT id, username, password_hash FROM "user" WHERE username = ?'
        cursor = self.execute_sql_params(sql, [username])
        if cursor.valid():
            return SqlQueryResult(True, cursor.one())
        return SqlQueryResult(False, cursor.error_message())
    
    # Exercises

    def get_exercise_templates(self, user_id: int) -> SqlQueryResult:
        sql = """
        SELECT 
            e.id AS id,
            e.name AS name,
            e.target_sets AS sets,
            e.target_reps AS reps,
            e.creator_id AS creator_id,
            u.username AS creator_name
        FROM exercise_template e
        JOIN "user" u ON e.creator_id = u.id
        WHERE e.creator_id = ?
        ORDER BY e.name ASC;
        """
        cursor = self.execute_sql_params(sql, [user_id])
        if cursor.valid():
            return SqlQueryResult(True, cursor.all())
        return SqlQueryResult(False, cursor.error_message())

    def get_adopted_exercise_templates(self, user_id: int) -> SqlQueryResult:
        sql = """
        SELECT 
            e.id AS id,
            e.name AS name,
            e.target_sets AS sets,
            e.target_reps AS reps,
            e.creator_id AS creator_id,
            u.username AS creator_name
        FROM user_exercise_template uet
        JOIN exercise_template e 
            ON uet.exercise_template_id = e.id
        JOIN "user" u 
            ON e.creator_id = u.id
        WHERE uet.user_id = ?
        ORDER BY e.name ASC;
        """
        cursor = self.execute_sql_params(sql, [user_id])
        if cursor.valid():
            return SqlQueryResult(True, cursor.all())
        return SqlQueryResult(False, cursor.error_message()) 

    def get_exercise_logs(self, user_id: int) -> SqlQueryResult:
        sql = """
        SELECT DISTINCT
            COALESCE(e.exercise_template_id, e.id) AS id,
            e.name AS name,
            w.user_id AS creator_id,
            u.username AS creator_name,
            e.notes AS notes
        FROM exercise_log e
        JOIN workout_log w 
            ON e.workout_id = w.id
        JOIN "user" u 
            ON w.user_id = u.id
        WHERE w.user_id = ?
        ORDER BY e.name ASC;
        """
        cursor = self.execute_sql_params(sql, [user_id])
        if cursor.valid():
            return SqlQueryResult(True, cursor.all())
        return SqlQueryResult(False, cursor.error_message())

    def get_exercise_templates_by_name(self, name: str, user_id: int) -> SqlQueryResult:
        sql = """
        SELECT 
            e.id AS id,
            e.name AS name,
            e.target_sets AS sets,
            e.target_reps AS reps,
            e.creator_id AS creator_id,
            u.username AS creator_name
        FROM exercise_template e
        JOIN "user" u 
            ON e.creator_id = u.id
        LEFT JOIN user_exercise_template ue 
            ON e.id = ue.exercise_template_id AND ue.user_id = ?
        WHERE e.creator_id != ? 
            AND ue.exercise_template_id IS NULL 
            AND LOWER(e.name) LIKE LOWER(?)
        ORDER BY e.name ASC;
        """ 
        cursor = self.execute_sql_params(sql, [user_id, user_id, f"%{name.strip()}%"])
        if cursor.valid():
            return SqlQueryResult(True, cursor.all())
        return SqlQueryResult(False, cursor.error_message()) 

    # Workouts
    
    def get_workout_logs(self, user_id: int) -> SqlQueryResult:
        # TODO: We want notes! Add it into SELECT when we have updated 
        # the schema and added a default value for it which we forgot to do
        sql = """
        SELECT 
            w.id AS id,
            w.date AS timestamp,
            w.description AS description,
            w.user_id AS creator_id,
            u.username AS creator_name
            -- COUNT(DISTINCT e.id) AS exercise_count,
            -- COALESCE(SUM(e.sets), 0) AS total_sets
        FROM workout_log w
        JOIN "user" u 
            ON w.user_id = u.id
        LEFT JOIN exercise_log e 
            ON e.workout_id = w.id
        WHERE w.user_id = ?
        GROUP BY w.id, w.date, w.description, w.user_id, u.username
        ORDER BY w.date DESC;
        """
        cursor = self.execute_sql_params(sql, [user_id])
        if cursor.valid():
            return SqlQueryResult(True, cursor.all())
        return SqlQueryResult(False, cursor.error_message())

sql_handler = SqlQueryHandler("database/xfit_dev.db")
