import sqlite3
from flask import Flask
from pathlib import Path
from .utils import set_log_filters, RemoveStaticLogs, RemoveChromeDevtoolLogs, debug_output, debug_assert
from .repository import close_sql_connection

#def create_app():
#    app = Flask(__name__)
#    with app.app_context():
#        init_db()
#    return app
app = Flask(__name__)
# TODO: Read from env file
app.secret_key = "rDIP7NzAOQZZa61rfGpV1LnT9H5PzZor3FZth3Om6XA="
app.teardown_appcontext(close_sql_connection)

set_log_filters("werkzeug", [
    RemoveStaticLogs(),
    RemoveChromeDevtoolLogs()
])

DB_FILENAME_DEV = "xfit_dev.db"
DB_FILEPATH_DEV = f"database/{DB_FILENAME_DEV}"
DB_PATH_DEV = Path(DB_FILEPATH_DEV)
debug_assert(DB_PATH_DEV.exists(), f"Create: {DB_FILEPATH_DEV}")

def debug_execute_sql(sql: str):
    with sqlite3.connect(DB_PATH_DEV) as connection:
        connection.execute(sql)
        connection.commit()

def debug_execute_sql_file(filepath: str, db_path = DB_PATH_DEV):
    with sqlite3.connect(db_path) as connection:
        with open(Path(filepath), mode="r", encoding="utf-8") as file:
            connection.executescript(file.read())

def debug_run_file(filepath: str):
    debug_execute_sql_file(filepath)
    debug_output(f"Run file {filepath} complete")

@app.cli.command("db-run-schema")
def db_delete_all_data_cli():
    debug_output("--- db-run-schema ---")
    debug_run_file("src/db/schema.sql")

@app.cli.command("db-seed-users")
def db_seed_users_cli():
    debug_output("--- db-seed-users ---")
    debug_run_file("src/db/seed_users.sql")

@app.cli.command("db-seed-workouts")
def db_seed_workouts_cli():
    debug_output("--- db-seed-workouts ---")
    debug_run_file("src/db/seed_workouts.sql")
