import sqlite3
from typing import Any, NamedTuple
from flask import render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from .utils import debug_assert, debug_output
from .repository import sql_handler
from .app import app

# These routse are public for all users

@app.route("/")
def home() -> str:
    #debug_output(session)
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
            sql_handler.insert_user(username, email, pw_hash)
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
        r = sql_handler.get_user_by_username(username) 
        if r.success and check_password_hash(r.data["password_hash"], password): 
            session["user_id"] = r.data["id"]
            session["username"] = r.data["username"]
            return redirect(url_for("home"))
        return render_template(
                    "login.html",
                    error = "Invalid username or password.")
    return render_template("login.html")

# These routes are auth-protected

def error_page(message: str) -> str:
    return render_template("error.html", message = message)

@app.route("/logout", methods=["POST"])
def logout() -> Any: 
    session.clear()
    return redirect(url_for("home"))

@app.route("/exercises", methods=["GET"])
def exercises() -> str:
    if not("user_id" in session):
        #TODO: Is it okay to stay at /exercises while displaying an error page???
        # Or do we create a common route for error pages, like /error ??
        # Check the standard to see what is the "conventional" way
        return error_page("Unauthorized access")
    user_id = session["user_id"]
    query_result = sql_handler.get_exercise_logs(user_id)
    if query_result.success:
        return render_template("exercises.html", 
                               exercises = query_result.data,
                               error = None)
    return render_template("exercises.html", 
                           exercises = [],
                           error = query_result.data)

@app.route("/exercises/create", methods=["GET", "POST"])
def exercises_create() -> str | Any:
    if not("user_id" in session):
        return error_page("Unauthorized access")
    user_id = session["user_id"]
    if request.method == "POST":
        name = request.form.get("name", "").strip() 
        target_sets = int(request.form["target_sets"])
        target_reps = int(request.form["target_reps"])
        sql_handler.insert_exercise_template(user_id, name, target_sets, target_reps)
    query_result = sql_handler.get_exercise_templates(user_id)
    if query_result.success:
        return render_template("create-exercise.html", 
                               templates = query_result.data,
                               error = None)
    return render_template("create-exercise.html", 
                           templates = [],
                           error = query_result.data)

class SearchModel(NamedTuple):
    query: str 
    mine: bool

@app.route("/exercises/search", methods=["GET"])
def exercises_search() -> str:
    if not("user_id" in session):
        return error_page("Unauthorized access")
    search_query = request.args.get("query", "").strip() 
    if search_query:
        user_id = session["user_id"]
        search_result = sql_handler.get_exercise_templates_by_name(search_query, user_id)
        templates = [] 
        error: str | None = None
        if search_result.success:
            templates = search_result.data
        else:    
            error = str(search_result.data)
        return render_template("search-exercises.html",
                               search_query = search_query,
                               templates = templates,
                               error = error)
    return render_template("search-exercises.html", 
                           search_query = "",
                           templates = [],
                           error = None)

