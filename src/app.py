from flask import Flask

from src.utils import debug_assert
from .utils import set_log_filters, RemoveStaticLogs, get_filepath, debug_output, debug_assert
from .repository import sql_handler

#def create_app():
#    app = Flask(__name__)
#    with app.app_context():
#        init_db()
#    return app
app = Flask(__name__)
set_log_filters("werkzeug", [
    RemoveStaticLogs()
])

@app.teardown_appcontext
def close_database(e = None):
    sql_handler.close_connection()

DB_NAME = "xfit.db"

def remove_database():
    path_result = get_filepath(f"database/{DB_NAME}")
    if path_result.valid:
        close_database()
        path = path_result.path
        if path.exists():
            path.unlink()
            debug_output(f"Database {path.name} removed")
    else:
        debug_assert(False, path_result.error)

def empty_database():
    remove_database() 
    sql_handler.execute_file("db/schema.sql")
    debug_output(f"Empty database {DB_NAME} created")

def seed_database():
    sql_handler.execute_file("db/seed.sql")
    debug_output(f"Seed database {DB_NAME} complete")

@app.cli.command("db-remove")
def db_remove_cli():
    debug_output("--- db-remove ---")
    remove_database()

@app.cli.command("db-empty")
def db_empty_cli():
    debug_output("--- db-empty ---")
    empty_database()

@app.cli.command("db-seed")
def db_seed_cli():
    debug_output("--- db-seed ---")
    seed_database()

@app.cli.command("db-migrate")
def migrate_database():
    # For development only!
    # A real app would use versioning in migration. Not sure if Flask supports that. 
    # Anyway, in a toy app simply removing the old db and replacing it with the updated one 
    # will do
    debug_output("--- db-migrate ---")
    empty_database()
    seed_database()
