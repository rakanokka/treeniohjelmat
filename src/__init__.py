import logging
import sqlite3
from typing import Any
from pathlib import Path
from flask import Flask, redirect, render_template, g, current_app, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

# TODO: Sanity checks to ensure the paths/files exist
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT_DIR.joinpath("database")
DB_PATH = DATABASE_DIR.joinpath("xfit.db")

# TODO: Create SqlQueryHandler class for the result
def get_database(db_path: Path) -> Any:
    print("[DEBUG] Trying to connect to database...")
    if not ("db" in g):
        print("[DEBUG] Connecting to database...")
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_database(e = None):
    print("[DEBUG] Trying to close database...")
    db = g.pop("db", None)
    if not (db is None):
        print("[DEBUG] Closing database...")
        db.close()

def run_sql(sql: str, params: list[str], db_path: Path) -> Any:
    connection = get_database(db_path)
    result = connection.execute(sql, params)
    connection.commit()
    return result

def run_sql_file(sql_filename: str, db_path: Path):
    connection = get_database(db_path)
    with current_app.open_resource(sql_filename) as file:
        connection.executescript(file.read().decode("utf8"))

class RemoveStaticLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not ("GET /static/" in record.getMessage()) 

logging.getLogger("werkzeug").addFilter(RemoveStaticLogs())
#def create_app():
#    app = Flask(__name__)
#    with app.app_context():
#        init_db()
#    return app

app = Flask(__name__)
app.teardown_appcontext(close_database)

@app.cli.command("db-migrate")
def migrate_database():
    # For development only!
    # A real app would use versioning in migration. Not sure if Flask supports that. 
    # Anyway, in a toy app simply removing the old db and replacing it with the updated one 
    # will do
    close_database()
    if DB_PATH.exists():
        # Remove the existing database
        DB_PATH.unlink()
        print(f"[DEBUG] Old database {DB_PATH.name} removed")
    # Create a new database from the existing schema 
    run_sql_file("db/schema.sql", DB_PATH)
    # Fill the database with dummy data for testing
    run_sql_file("db/seed.sql", DB_PATH)
    print(f"[DEBUG] New database {DB_PATH.name} created and filled with data from seed.sql")

@app.route("/")
def home() -> str:
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register() -> str | Any:
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return render_template(
                    "register.html",
                    error = "Passwords do not match. Please try again.")
        pw_hash = generate_password_hash(password1)
        try:
            sql = 'INSERT INTO "user" (username, email, password_hash) VALUES (?, ?, ?)'
            run_sql(sql, [username, email, pw_hash], DB_PATH)
        except sqlite3.IntegrityError:
            return render_template(
                    "register.html",
                    error = "Username or email is already taken.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login() -> str | Any:
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        sql = 'SELECT id, password_hash FROM "user" WHERE username = ?'
        user = run_sql(sql, [username], DB_PATH).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        return render_template(
                    "login.html",
                    error = "Invalid username or password.")
    return render_template("login.html")
