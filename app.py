import sqlite3
import secrets
import config
import utils
import users as users_repo
import exercises as exercises_repo
import workouts as workouts_repo
from typing import Any, cast
from flask import Flask, abort, flash, render_template, request, redirect, url_for, session
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

UNAUTHORIZED = 401
FORBIDDEN = 403
URL_NOT_FOUND = 404

def check_csrf():
    if not("csrf_token" in request.form):
        abort(FORBIDDEN)
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(FORBIDDEN)

### These routse are public for all users ###

@app.route("/")
def home() -> str:
    username = session.get("username")
    user_id = session.get("user_id")
    users = []
    authenticated = not(username is None)
    if authenticated:
        users = users_repo.get_other_users(cast(int, user_id))
    return render_template("home.html",
                           authenticated = authenticated,
                           users = users,
                           username = username,
                           user_id = user_id)

@app.route("/register", methods = ["GET", "POST"])
def register() -> str | Any:
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password1 = request.form.get("password1", "").strip()
        password2 = request.form.get("password2", "").strip()
        if password1 != password2:
            flash("[VIRHE] salasanat eivät täsmää")
            return redirect(url_for("register"))
        if not users_repo.add_user(username, email, password1):
            flash("[VIRHE] käyttäjätunnus tai salasana on varattu")
            return redirect(url_for("register"))
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/login", methods = ["GET", "POST"])
def login() -> str | Any:
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user_id = users_repo.get_auth_user_id(username, password) 
        if user_id != -1: 
            session["user_id"] = user_id
            session["username"] = username 
            session["csrf_token"] = secrets.token_hex(16) 
            return redirect(url_for("home"))
        flash("[VIRHE] käyttäjätunnus tai salasana on virheellinen")
        return redirect(url_for("login"))
    return render_template("login.html")

### All routes below are auth-protected ###

@app.route("/logout", methods = ["POST"])
def logout() -> Any: 
    if "user_id" in session:
        del session["user_id"]
        del session["username"]
    return redirect(url_for("home"))

@app.route("/profile/<int:user_id>")
def profile(user_id: int) -> str | Any:
    get_auth_user()
    profile_info = users_repo.get_user_profile_info(user_id)
    if not profile_info:
        abort(URL_NOT_FOUND)
    workout_templates = users_repo.get_workout_templates_usage_count(user_id)
    workouts = users_repo.get_recent_workouts(user_id)
    favourites = users_repo.get_favourite_exercise_categories(user_id)
    return render_template("profile.html", 
                           profile_info = profile_info,
                           workout_templates = workout_templates,
                           workouts = workouts,
                           favourites = favourites) 

def get_auth_user() -> int:
    if "user_id" in session:
        return session["user_id"]
    abort(UNAUTHORIZED)

# Exercises

@app.route("/exercises", methods = ["GET", "POST"])
def exercises() -> str:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        exercise_id = cast(int, request.form.get("exercise_id"))
        exercises_repo.delete_exercise_log(user_id, exercise_id)
    e = exercises_repo.get_exercise_logs(user_id)
    return render_template("exercises.html", exercises = e)

@app.route("/exercises/<int:exercise_id>", methods = ["GET"])
def view_exercise(exercise_id: int) -> str | Any:
    user_id = get_auth_user()
    e = exercises_repo.get_exercise_log(exercise_id)
    if not e:
        abort(URL_NOT_FOUND)
    workout_id = e["workout_id"]
    owner_id = workouts_repo.get_workout_log_user_id(workout_id)
    if user_id != owner_id:
        # For now, users have no access to the exercise logs of other users. 
        # Exercise logs are for personal use only
        abort(FORBIDDEN)
    return render_template("exercise.html", exercise = e)

@app.route("/exercises/templates", methods = ["GET", "POST"])
def exercise_templates() -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        if request.form.get("is_delete_owner_template") == "true":
            et_id = cast(int, request.form["template_id"])
            exercises_repo.delete_my_exercise_template(user_id, et_id)
            return redirect(url_for("exercise_templates"))
        if request.form.get("is_delete_adopted_template") == "true":
            et_id = cast(int, request.form["template_id"])
            exercises_repo.delete_adopted_exercise_template(user_id, et_id)
            return redirect(url_for("exercise_templates"))
        
        # Add template
        name = request.form.get("name", "").strip()
        if not name:
            flash("[VIRHE] Harjoituksella on oltava nimi")
            return redirect(url_for("exercise_templates"))
        category = request.form.get("category", "").strip() 
        sv = utils.IntValidator(request.form["target_sets"])
        rv = utils.IntValidator(request.form["target_reps"])
        if not(sv.validate() and rv.validate()):
            flash("[VIRHE] Sarjat ja toistot on oltava kokonaislukuja")
            return redirect(url_for("exercise_templates"))
        target_sets = sv.get()
        target_reps = rv.get()
        if not(target_sets > 0 and target_reps > 0):
            flash("[VIRHE] Sarjat ja toistot on oltava positiivisia kokonaislukuja")
            return redirect(url_for("exercise_templates"))
        exercises_repo.add_my_exercise_template(user_id, name, category, target_sets, target_reps)
     
    my_exercises = exercises_repo.get_exercise_templates(user_id)
    adopted_exercises = exercises_repo.get_adopted_exercise_templates(user_id)
    return render_template("exercise-templates.html", 
                           my_templates = my_exercises,
                           adopted_templates = adopted_exercises)

@app.route("/exercises/templates/<int:template_id>", methods = ["GET", "POST"])
def view_exercise_template(template_id: int) -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        if request.form.get("is_comment") == "true":
            content = request.form.get("content", "").strip()
            exercises_repo.add_excercise_template_comment(user_id, template_id, content)
        else:
            # Edit template 
            name = request.form.get("name", "").strip() 
            if not name:
                flash("[VIRHE] Harjoituksella on oltava nimi")
                return redirect(url_for("view_exercise_template", template_id = template_id))
            category = request.form.get("category", "").strip()
            sv = utils.IntValidator(request.form["target_sets"])
            rv = utils.IntValidator(request.form["target_reps"])
            if not(sv.validate() and rv.validate()):
                flash("[VIRHE] Sarjojen ja toistojen määrien on oltava positiivisia kokonaislukuja")
                return redirect(url_for("view_exercise_template", template_id = template_id))
            exercises_repo.update_exercise_template(user_id, template_id, name, category, sv.get(), rv.get())
    
    template = exercises_repo.get_exercise_template(template_id)
    if not template:
        abort(URL_NOT_FOUND)
    comments = exercises_repo.get_excercise_template_comments(template_id)
    creator_id = exercises_repo.get_exercise_template_creator_id(template_id)
    return render_template("exercise-template.html",
                           template = template,
                           comments = comments,
                           has_edit_permission = creator_id == user_id)

@app.route("/exercises/search", methods = ["GET", "POST"])
def exercises_search() -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        template_id = cast(int, request.form.get("template_id"))
        exercises_repo.add_adopted_exercise_template(user_id, template_id)
        return redirect(url_for("exercise_templates"))
    search_query = request.args.get("query", "").strip() 
    if search_query:
        templates = exercises_repo.find_exercise_templates(search_query, user_id)
        return render_template("search-exercises.html",
                               search_query = search_query,
                               templates = templates)
    
    return render_template("search-exercises.html", 
                           search_query = "",
                           templates = [])

# Workouts

@app.route("/workouts", methods = ["GET", "POST"])
def workouts() -> str:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        workout_id = cast(int, request.form.get("workout_id"))
        workouts_repo.delete_workout_log(user_id, workout_id) 
    w = workouts_repo.get_workout_logs(user_id)
    return render_template("workouts.html", workouts = w)

@app.route("/workouts/<int:workout_id>", methods = ["GET", "POST"])
def view_workout(workout_id: int) -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        if request.form.get("is_delete_exercise") == "true":
            exercise_id = cast(int, request.form.get("exercise_id"))
            workouts_repo.remove_exercise_from_workout_log(workout_id, exercise_id) 
        else:
            # Add exercise
            sv = utils.IntValidator(request.form["sets"])
            if not sv.validate():
                flash("[VIRHE] Sarjojen määrän on oltava positiivinen kokonaisluku")
                return redirect(url_for("view_workout", workout_id = workout_id))
            rv = utils.IntListValidator(request.form["reps"])
            if not rv.validate():
                flash("[VIRHE] Toistojen on oltava lista positiivisia kokonaislukuja")
                return redirect(url_for("view_workout", workout_id = workout_id))
            wv = utils.FloatListValidator(request.form["weights"], False)
            if not wv.validate():
                flash("[VIRHE] Painojen on oltava lista lukuja")
                return redirect(url_for("view_workout", workout_id = workout_id))
            sets = sv.get()
            reps_lst = rv.get()
            weights_lst = wv.get()
            if not(len(reps_lst) == sets and len(weights_lst) == sets):
                flash("[VIRHE] Toistojen ja painojen määrien on täsmättävä sarjojen määrän kanssa")
                return redirect(url_for("view_workout", workout_id = workout_id))
            name = str(request.form.get("wet_name"))
            wet_id = cast(int, request.form.get("wet_id"))
            workouts_repo.add_exercise_to_workout_log(workout_id, wet_id, name, reps_lst, weights_lst)

    workout = workouts_repo.get_workout_log(workout_id)
    if not workout:
        abort(URL_NOT_FOUND)
    owner_id = workouts_repo.get_workout_log_user_id(workout_id)
    if user_id != owner_id:
        # For now, users have no access to the workout logs of other users. 
        # Workout logs are for personal use only
        abort(FORBIDDEN)
    workout_exercises = workouts_repo.get_workout_exercises(workout_id)
    wt_id = workout["workout_template_id"]
    workout_exercise_templates = exercises_repo.get_exercise_templates_in_workout(wt_id)
    return render_template("workout.html",
                           workout = workout,
                           workout_exercises = workout_exercises,
                           workout_exercise_templates = workout_exercise_templates)

@app.route("/workouts/templates", methods = ["GET", "POST"])
def workout_templates() -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        if request.form.get("is_do_workout") == "true":
            wt_id = cast(int, request.form["template_id"])
            wt_name = request.form["template_name"]
            wt_desc = request.form["template_desc"]
            workouts_repo.add_workout_log(user_id, wt_id, wt_name, wt_desc) 
            return redirect(url_for("workouts"))
        if request.form.get("is_delete_owner_template") == "true":
            wt_id = cast(int, request.form["template_id"])
            workouts_repo.delete_my_workout_template(user_id, wt_id)
            return redirect(url_for("workout_templates"))
        if request.form.get("is_delete_adopted_template") == "true":
            wt_id = cast(int, request.form["template_id"])
            workouts_repo.delete_adopted_workout_template(user_id, wt_id)
            return redirect(url_for("workout_templates"))
        
        # Add template
        name = request.form.get("name", "").strip()
        if not name:
            flash("[VIRHE] Treenipohjalla on oltava nimi")
            return redirect(url_for("workout_templates"))
        desc = request.form.get("desc", "").strip() 
        tags_input = request.form.get("tags", "").strip()
        tags = tags_input.split(",") if tags_input else [] 
        tag_count = len(tags)
        tags = [t.strip() for t in tags if t.strip()]
        if len(tags) != tag_count:
            flash("[VIRHE] Virheellinen luokitus")
            return redirect(url_for("workout_templates"))
        workouts_repo.add_my_workout_template(user_id, name, desc, tags)
     
    my_templates = workouts_repo.get_workout_templates(user_id)
    adopted_templates = workouts_repo.get_adopted_workout_templates(user_id)
    tags_map: dict[int, list] = {}
    categories_map: dict[int, list] = {}
    for template in my_templates:
        tid = template["id"]
        categories_map[tid] = template["categories"].split(",") if template["categories"] else []
        tags_map[tid] = template["tags"].split(",") if template["tags"] else []
    for template in adopted_templates:
        tid = template["id"]
        categories_map[tid] = template["categories"].split(",") if template["categories"] else []
        tags_map[tid] = template["tags"].split(",") if template["tags"] else []
    return render_template("workout-templates.html", 
                           my_templates = my_templates,
                           adopted_templates = adopted_templates,
                           categories = categories_map,
                           tags = tags_map)

@app.route("/workouts/templates/<int:template_id>", methods = ["GET", "POST"])
def view_workout_template(template_id: int) -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST": 
        check_csrf()
        if request.form.get("is_remove_exercise") == "true":
            exercise_id = cast(int, request.form.get("exercise_template_id"))
            workouts_repo.remove_exercise_from_workout_template(user_id, template_id, exercise_id)
        elif request.form.get("is_comment") == "true":
            content = request.form.get("content", "").strip()
            workouts_repo.add_workout_template_comment(user_id, template_id, content)
        else:
            # Edit template
            name = request.form.get("name", "").strip() 
            if not name:
                flash("[VIRHE] Treenillä on oltava nimi")
                return redirect(url_for("view_workout_template", template_id = template_id))
            desc = request.form.get("desc", "").strip()
            tags_input = request.form.get("tags", "").strip()
            tags = tags_input.split(",") if tags_input else [] 
            tag_count = len(tags)
            tags = [t.strip() for t in tags if t.strip()]
            if len(tags) != tag_count:
                flash("[VIRHE] Virheellinen luokitus")
                return redirect(url_for("view_workout_template", template_id = template_id))
            workouts_repo.update_workout_template(user_id, template_id, name, desc, tags)
    
    template = workouts_repo.get_workout_template(template_id)
    if not template:
        abort(URL_NOT_FOUND)
    tags = template["tags"].split(",") if template["tags"] else []
    exercises = workouts_repo.get_workout_template_exercises(user_id, template_id)
    comments = workouts_repo.get_workout_template_comments(template_id)
    creator_id = workouts_repo.get_workout_template_creator_id(template_id)
    return render_template("workout-template.html",
                           template = template,
                           tags = tags,
                           exercises = exercises,
                           comments = comments,
                           has_permissions = user_id == creator_id)

@app.route("/workouts/templates/tag")
def workout_templates_tag() -> str:
    user_id = get_auth_user()
    tag_name = request.args.get("name", "").strip() 
    templates = workouts_repo.find_workout_templates_by_tag(tag_name, user_id)
    print(tag_name, len(templates))
    tags_map: dict[int, list] = {}
    for template in templates:
        tid = template["id"]
        tags_map[tid] = template["tags"].split(",") if template["tags"] else []
    return render_template("workout-templates-tag.html",
                           templates = templates,
                           tag_name = tag_name,
                           tags = tags_map)

@app.route("/workouts/search", methods=["GET", "POST"])
def workouts_search() -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        template_id = cast(int, request.form.get("template_id"))
        workouts_repo.add_adopted_workout_template(user_id, template_id)
        return redirect(url_for("workout_templates"))
    search_query = request.args.get("query", "").strip() 
    if search_query:
        templates = workouts_repo.find_workout_templates_by_name(search_query, user_id)
        tags_map: dict[int, list] = {}
        for template in templates:
            tid = template["id"]
            tags_map[tid] = template["tags"].split(",") if template["tags"] else []
        return render_template("search-workouts.html",
                               search_query = search_query,
                               templates = templates,
                               tags = tags_map)
    
    return render_template("search-workouts.html", 
                           search_query = "",
                           templates = [],
                           tags = {})

@app.route("/workouts/templates/add-exercises/<int:template_id>", methods = ["GET", "POST"])
def add_workout_exercises(template_id: int) -> str | Any:
    user_id = get_auth_user()
    creator_id = workouts_repo.get_workout_template_creator_id(template_id)
    if creator_id == -1:
        abort(URL_NOT_FOUND)
    if user_id != creator_id:
        abort(FORBIDDEN)
    if request.method == "POST":
        check_csrf()
        exercise_id = cast(int, request.form.get("exercise_template_id"))
        workouts_repo.add_exercise_to_workout(user_id, template_id, exercise_id)
        return redirect(url_for("view_workout_template", template_id = template_id))
    workout_template_name = workouts_repo.get_workout_template_name(template_id)
    templates = exercises_repo.get_exercise_templates(user_id)
    adopted_templates = exercises_repo.get_adopted_exercise_templates(user_id)
    for t in adopted_templates:
        templates.append(t)
    return render_template("workout-add-exercises.html",
                           name = workout_template_name,
                           templates = templates)

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
