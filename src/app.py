import sqlite3
from flask import Flask
from pathlib import Path
from .utils import set_log_filters, RemoveStaticLogs, debug_output, debug_assert
from .repository import close_sql_connection

#def create_app():
#    app = Flask(__name__)
#    with app.app_context():
#        init_db()
#    return app
app = Flask(__name__)
app.teardown_appcontext(close_sql_connection)

set_log_filters("werkzeug", [
    RemoveStaticLogs()
])

DB_FILENAME_DEV = "xfit_dev.db"
DB_FILEPATH_DEV = f"database/{DB_FILENAME_DEV}"
DB_PATH_DEV = Path(DB_FILEPATH_DEV)
debug_assert(DB_PATH_DEV.exists(), f"Create: {DB_FILEPATH_DEV}")

def debug_execute_sql(sql: str):
    with sqlite3.connect(DB_PATH_DEV) as connection:
        connection.execute(sql)
        connection.commit()

def debug_execute_sql_file(filepath: str):
    with sqlite3.connect(DB_PATH_DEV) as connection:
        with open(Path(filepath), mode="r", encoding="utf-8") as file:
            connection.executescript(file.read())

def debug_batch_commit(filepaths: list[str]):
    # Major hack! It appears executescript() writes a COMMIT before and after each invokation,
    # making transaction is unusable since we couldn't rollback in case of a failure
    combined_sql = ""
    for filepath in filepaths:    
        with open(Path(filepath), mode="r", encoding="utf-8") as file:
            combined_sql += f"{file.read()}\n"
    with sqlite3.connect(DB_PATH_DEV) as connection:
        connection.executescript(combined_sql)

def debug_delete_users():
    debug_execute_sql('DELETE FROM "user"') 
    debug_output(f"User data from {DB_FILENAME_DEV} deleted")

def debug_delete_all_data():
    debug_execute_sql_file("src/db/flush.sql") 
    debug_output(f"All data from {DB_FILENAME_DEV} deleted")

def debug_reset_database():
    debug_batch_commit(["src/db/flush.sql", "src/db/schema.sql"])
    debug_output(f"Database {DB_FILENAME_DEV} reset")

def debug_seed_database():
    debug_execute_sql_file("src/db/seed.sql")
    debug_output(f"Database {DB_FILENAME_DEV} seed complete")

@app.cli.command("db-delete-users")
def db_delete_users_cli():
    debug_output("--- db-delete-users ---")
    debug_delete_users()

@app.cli.command("db-delete-all-data")
def db_delete_all_data_cli():
    debug_output("--- db-delete-all-data ---")
    debug_delete_all_data()

@app.cli.command("db-reset")
def db_reset_cli():
    debug_output("--- db-reset ---")
    debug_reset_database()

@app.cli.command("db-seed")
def db_seed_cli():
    debug_output("--- db-seed ---")
    debug_seed_database()

@app.cli.command("db-migrate")
def migrate_database():
    # For development only! A real app would use versioning in migration. 
    debug_output("--- db-migrate ---")
    debug_batch_commit([
        "src/db/flush.sql", 
        "src/db/schema.sql",
        "src/db/seed.sql"
    ])
    debug_output(f"Database {DB_FILENAME_DEV} migration complete")
