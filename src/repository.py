import sqlite3
from typing import Any, NamedTuple
from contextlib import AbstractContextManager
from pathlib import Path
from flask import g
from .config import DATABASE_FILEPATH
from .utils import debug_assert, debug_output

CONNECTION_KEY = "sqlite_connection"

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

class SqlCursor:
    def __init__(self, cursor: sqlite3.Cursor | None, error: Exception | None = None):
        self.error = error
        self.cursor = cursor

    def valid(self) -> bool:
        return self.error is None

    def error_message(self) -> str:
        return str(self.error) if not self.error else ""

    def next_row(self) -> Any:
        return self.cursor.fetchone() if self.cursor else None

    def all_rows(self) -> list:
        return self.cursor.fetchall() if self.cursor else []

    def insert_id(self) -> int:
        result = self.cursor.lastrowid if self.cursor else -1
        if result is None:
            result = -1
        return result

    def row_count(self) -> int:
        return self.cursor.rowcount if self.cursor else 0

class SqlResult(NamedTuple):
    success: bool
    data: Any

class SqlTransaction(AbstractContextManager):
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection: Any = None
        self.error: Exception | None = None

    def __enter__(self) -> Any:
        self.connection = get_sql_connection(self.db_path)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if not(exc_type is None):
            self.connection.rollback()
            self.error = exc_value
            self.connection.close()
            return True
        try:
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            self.error = e
        finally:
            self.connection.close()
        return True

    def success(self) -> bool:
        return self.error is None

    def error_message(self) -> str:
        return str(self.error) if not self.error else ""

    def execute_sql(self, sql: str, params: list = []) -> sqlite3.Cursor:
        return self.connection.execute(sql, params)
 
class SqlHandler:
    def __init__(self, filepath: str):
        self.db_path = Path(filepath)
        if not self.db_path.exists():
            # Do something in non-debug build. Create the filepath or kill the app...
            pass

    # These are for isolated queries/writes that do not need transaction handling
    
    def execute_sql(self, sql: str, params: list = []) -> SqlCursor:
        try:
            connection = get_sql_connection(self.db_path)
            cursor = connection.execute(sql, params)
            connection.commit()
            return SqlCursor(cursor)
        except Exception as e:
            return SqlCursor(None, e)

    def execute_sql_file(self, filepath: str):
        connection = get_sql_connection(self.db_path)
        with open(Path(filepath), mode="r", encoding="utf-8") as file:
            connection.executescript(file.read())

    ### INSERT queries ###
    # NOTE: Do not use INSERT OR IGNORE for any of the inserts
    
    def insert_user(self, username: str, email: str, pw_hash: str) -> SqlResult:
        sql = 'INSERT INTO "user" (username, email, password_hash) VALUES (?, ?, ?)'
        cursor = self.execute_sql(sql, [username.strip(), email.strip(), pw_hash])
        if cursor.valid():
            return SqlResult(True, cursor.insert_id())
        return SqlResult(False, cursor.error_message())

    def insert_exercise_template(self, 
        user_id: int,
        name: str,
        category: str,
        target_sets: int,
        target_reps: int
    ) -> SqlResult:
        category_or_null = (category.strip() or None) if category else None 
        sql = """
        INSERT INTO exercise_template (creator_id, name, category, target_sets, target_reps) VALUES (?, ?, ?, ?, ?)
        """ 
        cursor = self.execute_sql(sql, [
            user_id, 
            name.strip(), 
            category_or_null, 
            target_sets, 
            target_reps
        ])
        if cursor.valid():
            return SqlResult(True, cursor.insert_id())
        return SqlResult(False, cursor.error_message())
    
    def insert_user_exercise_template(self, user_id: int, template_id: int) -> SqlResult:
        sql = """
        INSERT INTO user_exercise_template (user_id, exercise_template_id) VALUES (?, ?);
        """
        cursor = self.execute_sql(sql, [user_id, template_id])
        if cursor.valid():
            return SqlResult(True, cursor.insert_id())
        return SqlResult(False, cursor.error_message())

    def insert_workout_exercise_template(self, workout_template_id: int, exercise_template_id: int, order_index: int) -> SqlResult:
        sql = """
        INSERT INTO workout_exercise_template (workout_template_id, exercise_template_id, order_index) VALUES (?, ?, ?)
        """
        cursor = self.execute_sql(sql, [workout_template_id, exercise_template_id, order_index])
        if cursor.valid():
            return SqlResult(True, cursor.insert_id())
        return SqlResult(False, cursor.error_message())

    ### SELECT queries ###
    
    def get_user_by_username(self, username: str) -> SqlResult:
        sql = 'SELECT id, username, password_hash FROM "user" WHERE username = ?'
        cursor = self.execute_sql(sql, [username.strip()])
        if cursor.valid():
            return SqlResult(True, cursor.next_row())
        return SqlResult(False, cursor.error_message())
    
    # Exercises

    def get_exercise_template_creator_id(self, template_id: int) -> SqlResult:
        sql = "SELECT creator_id FROM exercise_template WHERE id = ?"
        cursor = self.execute_sql(sql, [template_id])
        if not cursor.valid():
            return SqlResult(False, cursor.error_message())
        template = cursor.next_row()
        if not template:
            return SqlResult(False, "No such template exists")
        return SqlResult(True, template["creator_id"])

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
        ORDER BY e.name ASC
        """
        cursor = self.execute_sql(sql, [user_id])
        if cursor.valid():
            return SqlResult(True, cursor.all_rows())
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
        ORDER BY e.name ASC
        """
        cursor = self.execute_sql(sql, [user_id])
        if cursor.valid():
            return SqlResult(True, cursor.all_rows())
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
        ORDER BY e.name ASC
        """
        cursor = self.execute_sql(sql, [user_id])
        if cursor.valid():
            return SqlResult(True, cursor.all_rows())
        return SqlResult(False, cursor.error_message())

    def get_exercise_template_by_id(self, template_id: int) -> SqlResult:
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
        WHERE e.id = ? 
        """ 
        cursor = self.execute_sql(sql, [template_id])
        if cursor.valid():
            return SqlResult(True, cursor.next_row())
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
        ORDER BY e.name ASC
        """ 
        cursor = self.execute_sql(sql, [user_id, user_id, f"%{name.strip()}%"])
        if cursor.valid():
            return SqlResult(True, cursor.all_rows())
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
        ORDER BY w.started_at DESC
        """
        cursor = self.execute_sql(sql, [user_id])
        if cursor.valid():
            return SqlResult(True, cursor.all_rows())
        return SqlResult(False, cursor.error_message())

    ### UPDATE queries ###
    
    def update_exercise_template(self, 
        user_id: int,
        template_id: int,
        name: str,
        category: str,
        target_sets: int,
        target_reps: int
    ) -> SqlResult:
        category_or_null = (category.strip() or None) if category else None 
        sql = """
        UPDATE exercise_template 
        SET name = ?, category = ?, target_sets = ?, target_reps = ?
        WHERE id = ? AND creator_id = ?
        """
        cursor = self.execute_sql(sql, [
            name.strip(),
            category_or_null,
            target_sets,
            target_reps,
            template_id,
            user_id
        ])
        if cursor.valid():
            if cursor.row_count() > 0:
                return SqlResult(True, "TODO: Do we return something???")
            return SqlResult(False, "No such template exists")
        return SqlResult(False, cursor.error_message())
        
    ### DELETE queries ###
 
    def delete_exercise_template(self, user_id: int, template_id: int) -> SqlResult:
        get_creator = self.get_exercise_template_creator_id(template_id)
        if not get_creator.success:
            return SqlResult(False, get_creator.data)
        creator_id = get_creator.data
        user_is_creator = creator_id == user_id
        if user_is_creator:
            with SqlTransaction(self.db_path) as transaction:
                sql = "DELETE FROM user_exercise_template WHERE exercise_template_id = ?"
                transaction.execute_sql(sql, [template_id])
                sql = "DELETE FROM exercise_template WHERE id = ? AND creator_id = ?"
                transaction.execute_sql(sql, [template_id, user_id])
            if transaction.success():
                return SqlResult(True, "TODO: Do we return something???")
            return SqlResult(False, transaction.error_message())
        
        sql = "DELETE FROM user_exercise_template WHERE user_id = ? AND exercise_template_id = ?"
        cursor = self.execute_sql(sql, [user_id, template_id])
        if cursor.valid():
            return SqlResult(True, "TODO: Do we return something???")
        return SqlResult(False, cursor.error_message())

sql_handler = SqlHandler(DATABASE_FILEPATH)
