import sqlite3
import config
import utils
import users as U
import exercises as E
import workouts as W
from typing import Any
from flask import Flask, abort, flash, render_template, request, redirect, url_for, session
from utils import IntValidator
from pathlib import Path

app = Flask(__name__)
app.secret_key = config.APP_SECRET_KEY

if config.DEBUG_MODE:
    utils.set_log_filters("werkzeug", [
        utils.RemoveStaticLogs(),
        utils.RemoveChromeDevtoolLogs()
    ])

DB_PATH = Path(config.DATABASE_FILENAME)
if not DB_PATH.exists():
    assert False, f"Create database file at {DB_PATH}"

### These routse are public for all users ###

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
            flash("VIRHE: salasanat eivät täsmää")
            return redirect(url_for("register"))
        try:
            users.add_user(username, email, password1)
            return redirect(url_for("home"))
        except sqlite3.IntegrityError:
            flash("VIRHE: käyttäjätunnus tai salasana on varattu")
            return redirect(url_for("register"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login() -> str | Any:
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_id = U.has_user(username, password) 
        if user_id != -1: 
            session["user_id"] = user_id
            session["username"] = username
            return redirect(url_for("home"))
        flash("VIRHE: käyttäjätunnus tai salasana on virheellinen")
        return redirect(url_for("login"))
    return render_template("login.html")

def error_page(message: str) -> str:
    return render_template("error.html", message = message)

### All routes below are auth-protected ###

@app.route("/logout", methods=["POST"])
def logout() -> Any: 
    if "user_id" in session:
        del session["user_id"]
        del session["username"]
    return redirect(url_for("home"))

# Exercises

def get_auth_user() -> int:
    if "user_id" in session:
        return session["user_id"]
    abort(403)

@app.route("/exercises", methods=["GET"])
def exercises() -> str:
    user_id = get_auth_user()
    exr_lst = E.get_exercise_logs(user_id)
    return render_template("exercises.html", exercises = exr_lst)

@app.route("/exercises/templates", methods=["GET", "POST"])
def exercise_templates() -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("VIRHE: Harjoituksella on oltava nimi")
            return redirect(url_for("exercise_templates"))
        category = request.form.get("category", "").strip() 
        sv = IntValidator(request.form["target_sets"])
        rv = IntValidator(request.form["target_reps"])
        if not(sv.validate() and rv.validate()):
            flash("VIRHE: Sarjat ja toistot on oltava kokonaislukuja")
            return redirect(url_for("exercise_templates"))
        target_sets = sv.get()
        target_reps = rv.get()
        if not(target_sets > 0 and target_reps > 0):
            flash("VIRHE: Sarjat ja toistot on oltava positiivisia kokonaislukuja")
            return redirect(url_for("exercise_templates"))
        E.add_my_exercise_template(user_id, name, category, target_sets, target_reps)
     
    my_exercises = E.get_exercise_templates(user_id)
    adopted_exercises = E.get_adopted_exercise_templates(user_id)
    return render_template("exercise-templates.html", 
                           my_templates = my_exercises,
                           adopted_templates = adopted_exercises)

@app.route("/exercises/templates/<int:template_id>", methods=["GET", "POST"])
def exercise_template(template_id: int) -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        if request.form.get("is_delete") == "true":
            E.delete_exercise_template(user_id, template_id)
            return redirect(url_for("exercise_templates"))
        
        name = request.form.get("name", "").strip() 
        if not name:
            flash("VIRHE: Harjoituksella on oltava nimi")
            return redirect(url_for("exercise_template"))
        category = request.form.get("category", "").strip()
        sv = IntValidator(request.form["target_sets"])
        rv = IntValidator(request.form["target_reps"])
        if not(sv.validate() and rv.validate()):
            flash("VIRHE: Sarjat ja toistot on oltava kokonaislukuja")
            return redirect(url_for("exercise_template"))
        target_sets = sv.get()
        target_reps = rv.get()
        if not(target_sets > 0 and target_reps > 0):
            flash("VIRHE: Sarjat ja toistot on oltava positiivisia kokonaislukuja")
            return redirect(url_for("exercise_template"))
        E.update_exercise_template(user_id, template_id, name, category, target_sets, target_reps)

    template = E.get_exercise_template(template_id)
    if not template:
        abort(404)
    creator_id = E.get_exercise_template_creator_id(template_id)
    return render_template("exercise-template.html",
                           template = template,
                           has_edit_permission = creator_id == user_id)

@app.route("/exercises/search", methods=["GET"])
def exercises_search() -> str:
    user_id = get_auth_user()
    search_query = request.args.get("query", "").strip() 
    if search_query:
        templates = E.find_exercise_templates(search_query, user_id)
        return render_template("search-exercises.html",
                               search_query = search_query,
                               templates = templates)
    
    return render_template("search-exercises.html", 
                           search_query = "",
                           templates = [])

@app.route("/exercises/add-template", methods=["POST"])
def exercises_add_template() -> Any:
    user_id = get_auth_user()
    tv = IntValidator(request.form.get("template_id", "").strip())
    if not tv.validate():
        abort(500) 
    E.add_adopted_exercise_template(user_id, tv.get())
    return redirect(url_for("exercises_search"))

# Workouts

@app.route("/workouts", methods=["GET"])
def workouts() -> str:
    user_id = get_auth_user()
    wrk_lst = W.get_workout_logs(user_id)
    return render_template("workouts.html", 
                           workouts = wrk_lst)

@app.route("/workouts/templates", methods=["GET", "POST"])
def workout_templates() -> str | Any:
    user_id = get_auth_user()
    flash("VIRHE: Not implemented")
    return redirect(url_for("workouts"))

@app.route("/workouts/search", methods=["GET"])
def workouts_search() -> str | Any:
    user_id = get_auth_user()
    flash("VIRHE: Not implemented")
    return redirect(url_for("workouts"))

@app.route("/workouts/add-template", methods=["POST"])
def workouts_add_template() -> Any:
    user_id = get_auth_user()
    flash("VIRHE: Not implemented")
    return redirect(url_for("workouts"))

### CLI ###

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

@app.cli.command("db-seed-users")
def db_seed_users_cli():
    print("--- db-seed-users ---")
    if DB_PATH.exists():
        cli_run_file("src/db/seed_users.sql")

@app.cli.command("db-seed-workouts")
def db_seed_workouts_cli():
    print("--- db-seed-workouts ---")
    if DB_PATH.exists():
        cli_run_file("src/db/seed_workouts.sql")
