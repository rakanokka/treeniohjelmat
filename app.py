import re
import secrets
import config
import utils
import users
import exercises
import workouts
from typing import Any, NamedTuple
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

BAD_REQUEST = 400
UNAUTHORIZED = 401
FORBIDDEN = 403
PAGE_NOT_FOUND = 404
INTERNAL_SERVER_ERROR = 500

MAX_INPUT_LENGTH = 100
MAX_COMMENT_LENGTH = 1000
MAX_TAG_LENGTH = 50
MAX_SETS = 100
MAX_REPS = 100
MAX_WEIGHT = 1000.0

EMAIL_REGEX = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"

# Common util functions

def is_valid_email(email: str) -> bool:
    if not email:
        return False
    return bool(re.match(EMAIL_REGEX, email.strip()))

def get_auth_user() -> int:
    if "user_id" in session:
        return session["user_id"]
    abort(UNAUTHORIZED)

def has_hidden_input_set_true(name: str) -> bool:
    return request.form.get(name) == "true"

def push_error_messages(messages: list[str]):
    for message in messages:
        flash(f"[VIRHE] {message}")

def get_hidden_input(name: str) -> str:
    return request.form[name]

def get_hidden_input_as_int(name: str) -> int:
    return int(get_hidden_input(name))

def check_csrf():
    if not("csrf_token" in request.form):
        print("CSRF token not in session")
        abort(FORBIDDEN)
    if request.form["csrf_token"] != session["csrf_token"]:
        print("CSRF token not in request")
        abort(FORBIDDEN)

# Public routes

@app.route("/")
def get_home() -> str:
    username = session.get("username")
    user_id = session.get("user_id")
    usr_lst = []
    authenticated = not(user_id is None)
    if authenticated:
        usr_lst = users.get_other_users(int(user_id))
    return render_template("home.html",
                           authenticated = authenticated,
                           users = usr_lst,
                           username = username,
                           user_id = user_id)

@app.route("/register")
def get_register() -> str:
    return render_template("register.html",
                           username = "",
                           email = "",
                           password1 = "",
                           password2 = "")

@app.route("/register", methods = ["POST"])
def post_register() -> str | Any:
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password1 = request.form.get("password1", "").strip()
    password2 = request.form.get("password2", "").strip()
    error_messages: list[str] = []
    
    if password1 != password2:
        error_messages.append("Salasanat eivät täsmää")
    
    if not is_valid_email(email):
        error_messages.append("Sähköpostiosoite on virheellinen")
    
    if error_messages:
        push_error_messages(error_messages)
        return render_template("register.html",
                               username = username,
                               email = email,
                               password1 = password1,
                               password2 = password2)
    
    if not users.add_user(username, email, password1):
        flash("[VIRHE] Käyttäjätunnus tai sähköpostiosoite on varattu")
        return render_template("register.html",
                               username = username,
                               email = email,
                               password1 = password1,
                               password2 = password2)
    
    return redirect(url_for("get_home"))

@app.route("/login")
def get_login() -> str: 
    return render_template("login.html")

@app.route("/login", methods = ["POST"])
def post_login() -> Any:
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    user_id = users.get_auth_user_id(username, password) 
    if user_id: 
        session["user_id"] = user_id
        session["username"] = username 
        session["csrf_token"] = secrets.token_hex(16) 
        return redirect(url_for("get_home"))
    
    flash("[VIRHE] Käyttäjätunnus tai salasana on virheellinen")
    return redirect(url_for("get_login"))

# Auth routes

@app.route("/logout", methods = ["POST"])
def post_logout() -> Any: 
    session.clear()
    return redirect(url_for("get_home"))

@app.route("/profile/<int:user_id>")
def get_profile(user_id: int) -> str:
    get_auth_user()
    profile_info = users.get_user_profile_info(user_id)
    if not profile_info:
        abort(PAGE_NOT_FOUND)
    workout_templates = users.get_workout_templates_usage_count(user_id)
    recent_workouts = users.get_recent_workouts(user_id)
    favourites = users.get_favourite_exercise_categories(user_id)
    return render_template("profile.html", 
                           profile_info = profile_info,
                           workout_templates = workout_templates,
                           workouts = recent_workouts,
                           favourites = favourites) 

# Exercise valdation utils

class ExerciseTemplateFormData(NamedTuple):
    error_messages: list[str]
    name: str
    category: str
    sets: int
    reps: int

def validate_exercise_template_form() -> ExerciseTemplateFormData:
    error_messages: list[str] = []
    name = request.form.get("name", "").strip()
    if not name:
        error_messages.append("Harjoituksella on oltava nimi")
    elif len(name) > MAX_INPUT_LENGTH:
        error_messages.append(f"Harjoituksen nimen pituus saa olla enintään {MAX_INPUT_LENGTH} merkkiä")
    
    category = request.form.get("category", "").strip() 
    if len(category) > MAX_INPUT_LENGTH:
        error_messages.append(f"Ryhmän pituus saa olla enintään {MAX_INPUT_LENGTH} merkkiä")

    sv = utils.IntValidator(request.form["target_sets"], MAX_SETS)
    rv = utils.IntValidator(request.form["target_reps"], MAX_REPS)
    if not sv.validate():
        error_messages.append(f"Sarjojen määrän on oltava kokonaisluku välillä 0 < sarjat < {MAX_SETS + 1}")
    if not rv.validate():
        error_messages.append(f"Toistojen määrän on oltava kokonaisluku välillä 0 < toistot < {MAX_REPS + 1}")
    return ExerciseTemplateFormData(error_messages, name, category, sv.get(), rv.get())

# Routes /exercises

@app.route("/exercises")
def get_exercises() -> str:
    user_id = get_auth_user()
    exercise_logs = exercises.get_exercise_logs(user_id)
    return render_template("exercises.html", exercises = exercise_logs)

@app.route("/exercises", methods = ["POST"])
def post_exercises() -> str:
    user_id = get_auth_user()
    check_csrf()
    exercise_id = int(str(request.form.get("exercise_id")))
    exercises.delete_exercise_log(user_id, exercise_id)
    exercise_logs = exercises.get_exercise_logs(user_id)
    return render_template("exercises.html", exercises = exercise_logs)

# Routes /exercises/<id>

@app.route("/exercises/<int:exercise_id>")
def get_exercise(exercise_id: int) -> str:
    user_id = get_auth_user()
    exercise_log = exercises.get_exercise_log(exercise_id)
    if not exercise_log:
        abort(PAGE_NOT_FOUND)
    workout_id = exercise_log["workout_id"]
    owner_id = workouts.get_workout_log_user_id(workout_id)
    if user_id != owner_id:
        abort(FORBIDDEN)
    return render_template("exercise.html", exercise = exercise_log)

# Routes /exercises/templates

@app.route("/exercises/templates")
def get_exercise_templates() -> str | Any:
    user_id = get_auth_user()
    my_exercises = exercises.get_exercise_templates(user_id)
    adopted_exercises = exercises.get_adopted_exercise_templates(user_id)
    return render_template("exercise-templates.html", 
                           my_templates = my_exercises,
                           adopted_templates = adopted_exercises)

@app.route("/exercises/templates", methods = ["POST"])
def post_exercise_templates() -> str | Any:
    user_id = get_auth_user()
    check_csrf()
    if has_hidden_input_set_true("et_delete_owner"):
        # Delete owner template
        et_id = int(request.form["template_id"])
        exercises.delete_my_exercise_template(user_id, et_id)
        return redirect(url_for("get_exercise_templates"))
    
    if has_hidden_input_set_true("et_pop_owner"):
        # Delete last owner template
        et_id = int(request.form["template_id"])
        exercises.delete_my_exercise_template_latest_version(user_id, et_id)
        return redirect(url_for("get_exercise_templates"))
    
    if has_hidden_input_set_true("et_delete_adopted"):
        # Delete adopted template
        et_id = int(request.form["template_id"])
        exercises.delete_adopted_exercise_template(user_id, et_id)
        return redirect(url_for("get_exercise_templates"))
    
    if has_hidden_input_set_true("et_pop_adopted"):
        # Delete last adopted template (go back to previous version)
        et_id = int(request.form["template_id"])
        prev_version_id = exercises.get_exercise_template_previous_version_id(et_id)
        if not prev_version_id:
            abort(BAD_REQUEST)
        exercises.update_adopted_exercise_template(user_id, et_id, prev_version_id)
        return redirect(url_for("get_exercise_templates"))
    
    if has_hidden_input_set_true("et_next_adopted"):
        # Adopt next adopted template (next updated version)
        et_id = int(request.form["template_id"])
        next_version_id = exercises.get_exercise_template_next_version_id(et_id)
        if not next_version_id:
            abort(BAD_REQUEST)
        exercises.update_adopted_exercise_template(user_id, et_id, next_version_id)
        return redirect(url_for("get_exercise_templates"))
    
    # Add exercise
    data = validate_exercise_template_form()
    if data.error_messages:
        push_error_messages(data.error_messages)
    else:
        exercises.add_my_exercise_template(user_id, data.name, data.category, data.sets, data.reps)
    return redirect(url_for("get_exercise_templates"))

# Routes /exercises/templates/<id>

@app.route("/exercises/templates/<int:template_id>")
def get_exercise_template(template_id: int) -> str:
    get_auth_user() 
    template = exercises.get_exercise_template(template_id)
    if not template:
        abort(PAGE_NOT_FOUND)
    comments = exercises.get_excercise_template_comments(template_id)
    return render_template("exercise-template.html",
                           template = template,
                           comments = comments)

@app.route("/exercises/templates/<int:template_id>", methods = ["POST"])
def post_exercise_template(template_id: int) -> Any:
    user_id = get_auth_user()
    check_csrf()
    content = request.form.get("content", "").strip()
    if len(content) > MAX_COMMENT_LENGTH:
        flash(f"[VIRHE] Kommentin pituus saa olla enintään {MAX_COMMENT_LENGTH} merkkiä")
    else:
        exercises.add_excercise_template_comment(user_id, template_id, content)
    return redirect(url_for("get_exercise_template", template_id = template_id))

# Routes /exercises/templates/edit/<id>

@app.route("/exercises/templates/edit/<int:template_id>")
def get_edit_exercise_template(template_id: int) -> str:
    user_id = get_auth_user()
    creator_id = exercises.get_exercise_template_creator_id(template_id)
    if user_id != creator_id:
        abort(FORBIDDEN)
    template = exercises.get_exercise_template(template_id)
    return render_template("edit-exercise-template.html", template = template)

@app.route("/exercises/templates/edit/<int:template_id>", methods = ["POST"])
def post_edit_exercise_template(template_id: int) -> Any:
    user_id = get_auth_user()
    creator_id = exercises.get_exercise_template_creator_id(template_id)
    if user_id != creator_id:
        abort(FORBIDDEN)
    data = validate_exercise_template_form()
    if data.error_messages:
        push_error_messages(data.error_messages)
    else:
        exercises.update_exercise_template(user_id, template_id, data.name, data.category, data.sets, data.reps)
    redirect(url_for("get_edit_exercise_template", template_id = template_id)) 
    
# Routes /exercises/templates/search

def find_exercise_templates_by(user_id: int, search_type: str, search_query: str) -> str:
    templates = []
    if search_type == "category":
        templates = exercises.find_exercise_templates_by_category(search_query)
    else:
        templates = exercises.find_exercise_templates_by_name(search_query)
    
    user_et_ids = exercises.get_all_exercise_template_ids(user_id)
    return render_template("search-exercises.html",
                           search_type = search_type,
                           search_query = search_query,
                           no_search_results = len(templates) == 0,
                           templates = templates,
                           user_et_ids = set(user_et_ids))

@app.route("/exercises/search")
def get_exercises_search() -> str | Any:
    user_id = get_auth_user()
    search_type = request.args.get("type", "name")
    search_query = request.args.get("query", "").strip() 
    if search_query:
        return find_exercise_templates_by(user_id, search_type, search_query)
    
    return render_template("search-exercises.html",
                           search_type = "name",
                           search_query = "",
                           no_search_results = False,
                           templates = [],
                           user_et_ids = {})

@app.route("/exercises/search", methods = ["POST"])
def post_exercises_search() -> Any:
    user_id = get_auth_user()
    check_csrf()
    template_id = int(str(request.form.get("template_id")))
    exercises.add_adopted_exercise_template(user_id, template_id)
    return redirect(url_for("get_exercise_templates"))

# Workout valdation utils 

class WorkoutLogExercisesData(NamedTuple):
    error_messages: list[str]
    sets: int
    reps: list[int]
    weights: list[float]

def validate_workout_exercise() -> WorkoutLogExercisesData:
    error_messages: list[str] = []
    sv = utils.IntValidator(request.form["sets"], MAX_SETS)
    if not sv.validate():
        error_messages.append(f"Sarjojen määrän on oltava kokonaisluku 0 < sarjat < {MAX_SETS}")
    rv = utils.IntListValidator(request.form["reps"], MAX_REPS)
    if not rv.validate():
        error_messages.append(f"Toistojen on oltava lista kokonaislukuja välillä 0 < toisto < {MAX_REPS + 1}")
    # Negative weights are supported. They may indicate machine assisted weights
    wv = utils.FloatListValidator(request.form["weights"], MAX_WEIGHT, False)
    if not wv.validate():
        error_messages.append(f"Painojen on oltava lista lukuja välillä -{MAX_WEIGHT} < paino < {MAX_WEIGHT}")
    sets = sv.get()
    reps_lst = rv.get()
    weight_lst = wv.get()
    if len(reps_lst) != sets:
        error_messages.append("Toistolistan pituuden on täsmättävä sarjojen määrän kanssa")
    if len(weight_lst) != sets:
        error_messages.append("Painolistan pituuden on täsmättävä sarjojen määrän kanssa")
    
    return WorkoutLogExercisesData(error_messages, sets, reps_lst, weight_lst)

class WorkoutTemplateData(NamedTuple):
    error_messages: list[str]
    name: str
    description: str 
    tags: list[str]

def validate_workout_template_data(name: str, description: str, tags: list[str]) -> WorkoutTemplateData:
    error_messages: list[str] = []
    if not name:
        error_messages.append("Treenillä on oltava nimi")
    elif len(name) > MAX_INPUT_LENGTH:
        error_messages.append(f"Treenin nimen pituus saa olla enintään {MAX_INPUT_LENGTH} merkkiä")

    tag_count = len(tags)
    tags = [t.strip() for t in tags if t.strip()]
    tag_set = set(tags)
    if len(tags) != tag_count:
        error_messages.append("Virheellinen treenin luokitusmuoto. Syötä luokat pilkulla erotettuna listana.")
    if len(tag_set) != tag_count:
        error_messages.append("Virheellinen treenin luokitus. Luokkien on oltava uniikkeja.")

    return WorkoutTemplateData(error_messages, name, description, tags)

def validate_workout_template_form_data() -> WorkoutTemplateData:
    name = request.form.get("name", "").strip() 
    desc = request.form.get("description", "").strip()
    tags_input = request.form.get("tags", "").strip()
    tags = tags_input.split(",") if tags_input else []
    return validate_workout_template_data(name, desc, tags) 

def validate_workout_template_session_data(session_name: str) -> WorkoutTemplateData:
    name = session[session_name]["name"] 
    desc = session[session_name]["description"] 
    tags = session[session_name]["tags"] 
    return validate_workout_template_data(name, desc, tags)

# Routes /workouts

@app.route("/workouts")
def get_workouts() -> str:
    user_id = get_auth_user()
    workout_logs = workouts.get_workout_logs(user_id)
    return render_template("workouts.html", workouts = workout_logs)

@app.route("/workouts", methods = ["POST"])
def post_workouts() -> str:
    user_id = get_auth_user()
    check_csrf()
    workout_id = get_hidden_input_as_int("workout_id")
    workouts.delete_workout_log(user_id, workout_id) 
    workout_logs = workouts.get_workout_logs(user_id)
    return render_template("workouts.html", workouts = workout_logs)

def check_workout_owner(user_id, workout_id):
    owner_id = workouts.get_workout_log_user_id(workout_id)
    if user_id != owner_id:
        abort(FORBIDDEN)

# Routes /workouts/<id>

@app.route("/workouts/<int:workout_id>")
def get_workout(workout_id: int) -> str:
    user_id = get_auth_user()
    workout = workouts.get_workout_log(workout_id)
    if not workout:
        abort(PAGE_NOT_FOUND)
    check_workout_owner(user_id, workout_id) 
    workout_exercises = workouts.get_workout_exercises(workout_id)
    wt_id = workout["workout_template_id"]
    workout_exercise_templates = exercises.get_exercise_templates_in_workout(wt_id)
    return render_template("workout.html",
                           workout = workout,
                           workout_exercises = workout_exercises,
                           workout_exercise_templates = workout_exercise_templates)

@app.route("/workouts/<int:workout_id>", methods = ["POST"])
def post_workout(workout_id: int) -> Any:
    user_id = get_auth_user()
    check_workout_owner(user_id, workout_id) 
    check_csrf()
    if has_hidden_input_set_true("wl_delete_exercise"):
        exercise_id = get_hidden_input_as_int("exercise_id")
        workouts.remove_exercise_from_workout_log(workout_id, exercise_id) 
        return redirect(url_for("get_workout", workout_id = workout_id))
       
    data = validate_workout_exercise() 
    if data.error_messages:
        push_error_messages(data.error_messages) 
    else:
        # Add exercise to workout
        name = request.form["wet_name"]
        wet_id = int(request.form["wet_id"])
        workouts.add_exercise_to_workout_log(workout_id, wet_id, name, data.reps, data.weights)
    
    return redirect(url_for("get_workout", workout_id = workout_id))

# Routes /workouts/templates

@app.route("/workouts/templates")
def get_workout_templates() -> str:
    user_id = get_auth_user()
    my_templates = workouts.get_workout_templates(user_id)
    adopted_templates = workouts.get_adopted_workout_templates(user_id)
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

@app.route("/workouts/templates", methods = ["POST"])
def post_workout_templates() -> Any:
    user_id = get_auth_user()
    check_csrf()
    
    if has_hidden_input_set_true("wt_commit"):
        # Do workout button press
        wt_id = get_hidden_input_as_int("wt_id")
        name = get_hidden_input("wt_name")
        desc = get_hidden_input("wt_desc")
        workouts.add_workout_log(user_id, wt_id, name, desc) 
        return redirect(url_for("get_workouts"))
     
    if has_hidden_input_set_true("wt_delete_owner"):
        # Delete owner template
        wt_id = get_hidden_input_as_int("wt_id")
        workouts.delete_my_workout_template(user_id, wt_id)
    
    if has_hidden_input_set_true("wt_pop_owner"):
        # Delete last owner template
        wt_id = get_hidden_input_as_int("wt_id")
        workouts.delete_my_workout_template_latest_version(user_id, wt_id)
    
    if has_hidden_input_set_true("wt_delete_adopted"):
        # Delete adopted template
        wt_id = get_hidden_input_as_int("wt_id")
        workouts.delete_adopted_workout_template(user_id, wt_id)
    
    if has_hidden_input_set_true("wt_next_adopted"):
        # Adopt next adopted template (next updated version)
        wt_id = get_hidden_input_as_int("wt_id")
        next_version_id = workouts.get_workout_template_next_version_id(wt_id)
        if not next_version_id:
            abort(BAD_REQUEST)
        workouts.update_adopted_workout_template(user_id, wt_id, next_version_id)

    if has_hidden_input_set_true("wt_pop_adopted"):
        # Delete last adopted template (go back to previous version)
        wt_id = get_hidden_input_as_int("wt_id")
        prev_version_id = workouts.get_workout_template_previous_version_id(wt_id)
        if not prev_version_id:
            abort(BAD_REQUEST)
        workouts.update_adopted_workout_template(user_id, wt_id, prev_version_id)

    return redirect(url_for("get_workout_templates"))

# Routes /workouts/templates/<id>

@app.route("/workouts/templates/<int:template_id>")
def get_workout_template(template_id: int) -> str:
    get_auth_user()
    template = workouts.get_workout_template(template_id)
    if not template:
        abort(PAGE_NOT_FOUND)
    tags = template["tags"].split(",") if template["tags"] else []
    workout_exercises = workouts.get_workout_template_exercises(template_id)
    comments = workouts.get_workout_template_comments(template_id)
    return render_template("workout-template.html",
                           template = template,
                           tags = tags,
                           exercises = workout_exercises,
                           comments = comments)

@app.route("/workouts/templates/<int:template_id>", methods = ["POST"])
def post_workout_template(template_id: int) -> Any:
    user_id = get_auth_user()
    check_csrf()
    content = request.form.get("content", "").strip()
    if len(content) > MAX_COMMENT_LENGTH:
        flash(f"[VIRHE] Kommentin pituus saa olla enintään {MAX_COMMENT_LENGTH} merkkiä")
    else:
        workouts.add_workout_template_comment(user_id, template_id, content)
    return redirect(url_for("get_workout_template", template_id = template_id))

# Common util functions for create/edit workout template 

def workout_template_info(session_name: str, page_prefix: str) -> str:
    data = validate_workout_template_form_data()
    if data.error_messages:
        push_error_messages(data.error_messages)
    
    session[session_name]["name"] = data.name
    session[session_name]["description"] = data.description
    session[session_name]["tags"] = data.tags
    session.modified = True
    
    return render_template(f"{page_prefix}-workout-template.html")

def add_workout_template_exercise(session_name: str, page_prefix: str) -> str:       
    exercise_id = int(request.form["et_id"])
    exercise = workouts.get_exercise_template(exercise_id)
    if not exercise:
        abort(BAD_REQUEST)
    session[session_name]["exercises"].append(dict(exercise))
    session[session_name]["valid"] = True
    session.modified = True 
    return render_template(f"{page_prefix}-workout-template.html")
    
def remove_workout_template_exercise(session_name: str, page_prefix: str) -> str:
    et_index = int(request.form["et_index"])
    del session[session_name]["exercises"][et_index]
    session.modified = True
    return render_template(f"{page_prefix}-workout-template.html")

# Routes /workouts/templates/create

@app.route("/workouts/templates/create")
def get_create_workout_template() -> str:
    user_id = get_auth_user()
    my_exercise_templates = exercises.get_exercise_templates(user_id)
    session["wtc"] = {
        "valid": False,
        "name": "",
        "description": "",
        "tags": [],
        "exercises": [],
        "my_templates": [dict(et) for et in my_exercise_templates]
    }
    return render_template("create-workout-template.html")

def submit_create_workout_template(user_id: int) -> str | Any:                          
    data = validate_workout_template_session_data("wtc")
    if data.error_messages:
        push_error_messages(data.error_messages)
        return render_template("create-workout-template.html")
    
    exercise_ids = [int(e["exercise_template_id"]) for e in session["wtc"]["exercises"]]
    workouts.add_my_workout_template(user_id, data.name, data.description, data.tags, exercise_ids)
    del session["wtc"]
    return redirect(url_for("get_workout_templates"))

@app.route("/workouts/templates/create", methods = ["POST"])
def post_create_workout_template() -> str | Any:
    user_id = get_auth_user()
    check_csrf()
    session_name = "wtc"
    page_prefix = "create"
    if has_hidden_input_set_true("wt_create_info"):
        return workout_template_info(session_name, page_prefix)
    if has_hidden_input_set_true("et_add"):
        return add_workout_template_exercise(session_name, page_prefix)
    if has_hidden_input_set_true("et_remove"):
        return remove_workout_template_exercise(session_name, page_prefix)
    return submit_create_workout_template(user_id)

# Routes /workouts/templates/edit

@app.route("/workouts/templates/edit")
def get_edit_workout_template() -> str:
    user_id = get_auth_user()
    template_id = request.args.get("wt_id")
    wt_id = int(str(template_id))
    wt = workouts.get_workout_template(wt_id) 
    if not wt:
        abort(BAD_REQUEST)
    name = wt["name"]
    description = wt["description"] or ""
    tags = wt["tags"].split(",") if wt["tags"] else []
    wet = workouts.get_user_workout_template_exercises(user_id, wt_id)
    my_exercise_templates = exercises.get_exercise_templates(user_id)
    session["wte"] = {
        "template_id": template_id,
        "name": name,
        "description": description,
        "tags": tags,
        "exercises": [dict(et) for et in wet],
        "my_templates": [dict(et) for et in my_exercise_templates]
    }
    return render_template("edit-workout-template.html")

def submit_edit_workout_template(user_id: int) -> str | Any:                          
    data = validate_workout_template_session_data("wte")
    if data.error_messages:
        push_error_messages(data.error_messages)
        return render_template("edit-workout-template.html")
    
    template_id = session["wte"]["template_id"]
    exercise_ids = [int(e["exercise_template_id"]) for e in session["wte"]["exercises"]]
    name = session["wte"]["name"]
    description = session["wte"]["description"]
    tags = session["wte"]["tags"]
    workouts.update_my_workout_template(user_id, template_id, name, description, tags, exercise_ids)
    del session["wte"]
    return redirect(url_for("get_workout_templates"))

@app.route("/workouts/templates/edit", methods = ["POST"])
def post_workout_template_edit() -> str | Any:
    user_id = get_auth_user()
    check_csrf()
    session_name = "wte"
    page_prefix = "edit"
    if has_hidden_input_set_true("wt_edit_info"):
        return workout_template_info(session_name, page_prefix)
    if has_hidden_input_set_true("et_add"):
        return add_workout_template_exercise(session_name, page_prefix)
    if has_hidden_input_set_true("et_remove"):
        return remove_workout_template_exercise(session_name, page_prefix)
    return submit_edit_workout_template(user_id)

# Routes /workouts/search

def find_workout_templates_by(user_id: int, search_type: str, search_query: str) -> str:
    print("search_type", search_type)
    templates = []
    if search_type == "tag":
        templates = workouts.find_workout_templates_by_tag(search_query)
    elif search_type == "category":
        templates = workouts.find_workout_templates_by_category(search_query)
    else:
        templates = workouts.find_workout_templates_by_name(search_query)
    
    user_wt_ids = workouts.get_all_workout_template_ids(user_id)
    categories_map: dict[int, list] = {}
    tags_map: dict[int, list] = {}
    for template in templates:
        tid = template["id"]
        categories_map[tid] = template["categories"].split(",") if template["categories"] else []
        tags_map[tid] = template["tags"].split(",") if template["tags"] else []
    
    return render_template("search-workouts.html",
                           search_type = search_type,
                           search_query = search_query,
                           no_search_results = len(templates) == 0,
                           templates = templates,
                           user_wt_ids = set(user_wt_ids),
                           categories = categories_map,
                           tags = tags_map)

@app.route("/workouts/search")
def get_workouts_search() -> str:
    user_id = get_auth_user()
    tag = request.args.get("tag")
    if tag:
        # Search via link
        return find_workout_templates_by(user_id, "tag", tag)
    
    search_type = request.args.get("type", "name")
    search_query = request.args.get("query", "").strip() 
    if search_query:
        # Search via form
        return find_workout_templates_by(user_id, search_type, search_query)
    
    return render_template("search-workouts.html",
                           search_type = "name",
                           search_query = "",
                           no_search_results = False,
                           templates = [],
                           user_wt_ids = set(),
                           categories = {},
                           tags = {})

@app.route("/workouts/search", methods=["POST"])
def post_workouts_search() -> str | Any:
    # Adopt template
    user_id = get_auth_user()
    check_csrf()
    template_id = int(request.form["template_id"])
    workouts.add_adopted_workout_template(user_id, template_id)
    return redirect(url_for("get_workout_templates"))
