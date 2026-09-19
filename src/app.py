import sqlite3
from flask import Flask
from pathlib import Path
from .config import DEBUG_MODE, DATABASE_FILEPATH, APP_SECRET_KEY
from .utils import set_log_filters, RemoveStaticLogs, RemoveChromeDevtoolLogs, debug_assert
from .repository import close_sql_connection

app = Flask(__name__)
app.teardown_appcontext(close_sql_connection)
app.secret_key = APP_SECRET_KEY

if DEBUG_MODE:
    set_log_filters("werkzeug", [
        RemoveStaticLogs(),
        RemoveChromeDevtoolLogs()
    ])

DB_PATH = Path(DATABASE_FILEPATH)
DB_DNE_MESSAGE = f"Database file does not exist. Create: <project-root>/{DB_PATH}"
debug_assert(DB_PATH.exists(), DB_DNE_MESSAGE)

def cli_execute_sql(sql: str):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(sql)
        connection.commit()

def cli_execute_sql_file(filepath: str, db_path = DB_PATH):
    with sqlite3.connect(db_path) as connection:
        with open(Path(filepath), mode="r", encoding="utf-8") as file:
            connection.executescript(file.read())

def cli_run_file(filepath: str):
    cli_execute_sql_file(filepath)
    print(f"File {filepath} execution complete")

@app.cli.command("db-init-schema")
def db_init_schema_cli():
    print("--- db-init-schema ---")
    if DB_PATH.exists():
        cli_run_file("src/db/schema.sql")
    else:
        print(DB_DNE_MESSAGE)

@app.cli.command("db-seed-users")
def db_seed_users_cli():
    print("--- db-seed-users ---")
    if DB_PATH.exists():
        cli_run_file("src/db/seed_users.sql")
    else:
        print(DB_DNE_MESSAGE)

@app.cli.command("db-seed-workouts")
def db_seed_workouts_cli():
    print("--- db-seed-workouts ---")
    if DB_PATH.exists():
        cli_run_file("src/db/seed_workouts.sql")
    else:
        print(DB_DNE_MESSAGE)
