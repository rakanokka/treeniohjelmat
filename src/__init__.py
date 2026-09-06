import os
from pathlib import Path
from flask import Flask, render_template, g, current_app
import sqlite3
from werkzeug.security import generate_password_hash
#import db
from typing import Any

app = Flask(__name__)

def get_database(db_path: Path) -> Any:
    if not ("db" in g):
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_database(e = None):
    db = g.pop("db", None)
    if not (db is None):
        db.close()

def run_sql(sql_filename: str, db_path: Path):
    connection = get_database(db_path)
    with current_app.open_resource(sql_filename) as file:
        connection.executescript(file.read().decode("utf8"))

app.teardown_appcontext(close_database)

# TODO: Sanity checks to ensure the paths/files exist
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT_DIR.joinpath("database")
DB_PATH = DATABASE_DIR.joinpath("xfit.db")

@app.cli.command("db-migrate")
def migrate_database():
    # For development only!
    # A real app would use versioning in migration. 
    # Not sure if Flask supports that. Anyway, in a toy app 
    # removing the old db and replacing it with the updated one 
    # will do just fine
    close_database()
    if DB_PATH.exists():
        # Remove the existing database
        DB_PATH.unlink()
        print(f"[INFO] Database {DB_PATH.name} removed")
    # Create a new database from the existing schema 
    run_sql("db/schema.sql", DB_PATH)
    # Fill the database with dummy data for testing
    run_sql("db/seed.sql", DB_PATH)
    print(f"[INFO] Database {DB_PATH.name} created and filled with seed data")

@app.route("/")
def home():
    return render_template(
        "home.html"
    )

@app.route("/login")
def login():
    return render_template(
        "login.html"
    )
