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

    def insert_id(self) -> int:
        debug_assert(self.valid())
        return cast(int, cast(sqlite3.Cursor, self.cursor).lastrowid)

class SqlResult(NamedTuple):
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
    
    # NOTE: Do not use INSERT OR IGNORE for any of the inserts
    
    def insert_user(self, username: str, email: str, pw_hash: str) -> SqlResult:
        sql = 'INSERT INTO "user" (username, email, password_hash) VALUES (?, ?, ?)'
        cursor = self.execute_sql_params(sql, [username, email, pw_hash])
        if cursor.valid():
            return SqlResult(True, cursor.insert_id())
        return SqlResult(False, cursor.error_message())

    def insert_exercise_template(self, user_id: int, name: str, target_sets: int, target_reps: int) -> SqlResult:
        sql = """
        INSERT INTO exercise_template (creator_id, name, category, target_sets, target_reps) VALUES (?, ?, ?, ?, ?)
        """ 
        cursor = self.execute_sql_params(sql, [user_id, name, target_sets, target_reps])
        if cursor.valid():
            return SqlResult(True, cursor.insert_id())
        return SqlResult(False, cursor.error_message())
    
    def insert_user_exercise_template(self, user_id: int, template_id: int) -> SqlResult:
        sql = """
        INSERT INTO user_exercise_template (user_id, exercise_template_id) VALUES (?, ?);
        """
        cursor = self.execute_sql_params(sql, [user_id, template_id])
        if cursor.valid():
            return SqlResult(True, cursor.insert_id())
        return SqlResult(False, cursor.error_message())

    def insert_workout_exercise_template(self, workout_template_id: int, exercise_template_id: int, order_index: int) -> SqlResult:
        sql = """
        INSERT INTO workout_exercise_template (workout_template_id, exercise_template_id, order_index) VALUES (?, ?, ?)
        """
        cursor = self.execute_sql_params(sql, [workout_template_id, exercise_template_id, order_index])
        if cursor.valid():
            return SqlResult(True, cursor.insert_id())
        return SqlResult(False, cursor.error_message())

    def get_user_by_username(self, username: str) -> SqlResult:
        sql = 'SELECT id, username, password_hash FROM "user" WHERE username = ?'
        cursor = self.execute_sql_params(sql, [username])
        if cursor.valid():
            return SqlResult(True, cursor.one())
        return SqlResult(False, cursor.error_message())
    
    # Exercises

    def get_exercise_templates(self, user_id: int) -> SqlResult:
        sql = """
        SELECT 
            e.id AS id,
            e.creator_id AS creator_id,
            e.name AS name,
            e.category AS category,
            e.target_sets AS sets,
            e.target_reps AS reps,
            u.username AS creator_name
        FROM exercise_template e
        JOIN "user" u ON e.creator_id = u.id
        WHERE e.creator_id = ?
        ORDER BY e.name ASC;
        """
        cursor = self.execute_sql_params(sql, [user_id])
        if cursor.valid():
            return SqlResult(True, cursor.all())
        return SqlResult(False, cursor.error_message())

    def get_adopted_exercise_templates(self, user_id: int) -> SqlResult:
        sql = """
        SELECT 
            e.id AS id,
            e.name AS name,
            e.category AS category,
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
            return SqlResult(True, cursor.all())
        return SqlResult(False, cursor.error_message()) 

    def get_exercise_logs(self, user_id: int) -> SqlResult:
        sql = """
        SELECT DISTINCT
            COALESCE(e.exercise_template_id, e.id) AS id,
            e.name AS name,
            et.category AS category,
            w.user_id AS creator_id,
            u.username AS creator_name,
            e.notes AS notes
        FROM exercise_log e
        JOIN workout_log w 
            ON e.workout_id = w.id
        JOIN "user" u 
            ON w.user_id = u.id
        LEFT JOIN exercise_template et 
            ON e.exercise_template_id = et.id
        WHERE w.user_id = ?
        ORDER BY e.name ASC;
        """
        cursor = self.execute_sql_params(sql, [user_id])
        if cursor.valid():
            return SqlResult(True, cursor.all())
        return SqlResult(False, cursor.error_message())

    def get_exercise_templates_by_name(self, name: str, user_id: int) -> SqlResult:
        sql = """
        SELECT 
            e.id AS id,
            e.name AS name,
            e.category AS category,
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
            return SqlResult(True, cursor.all())
        return SqlResult(False, cursor.error_message()) 

    # Workouts
    
    def get_workout_logs(self, user_id: int) -> SqlResult:
        sql = """
        SELECT 
            w.id AS id,
            w.name AS name,
            w.notes AS notes,
            w.started_at AS started_at,
            w.ended_at AS ended_at,
            w.user_id AS creator_id,
            u.username AS creator_name
        FROM workout_log w
        JOIN "user" u 
            ON w.user_id = u.id
        LEFT JOIN exercise_log e 
            ON e.workout_id = w.id
        WHERE w.user_id = ?
        GROUP BY w.id, w.name, w.notes, w.started_at, w.ended_at, w.user_id, u.username
        ORDER BY w.started_at DESC;
        """
        cursor = self.execute_sql_params(sql, [user_id])
        if cursor.valid():
            return SqlResult(True, cursor.all())
        return SqlResult(False, cursor.error_message()) 

sql_handler = SqlQueryHandler("database/xfit_dev.db")
