import sqlite3
from typing import Any
from flask import render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from .utils import IntValidator, debug_assert, debug_output
from .repository import sql_handler
from .app import app

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

def error_page(message: str) -> str:
    return render_template("error.html", message = message)

### All routes below are auth-protected ###

@app.route("/logout", methods=["POST"])
def logout() -> Any: 
    session.clear()
    return redirect(url_for("home"))

# Exercises

@app.route("/exercises", methods=["GET"])
def exercises() -> str:
    if not("user_id" in session):
        return error_page("Unauthorized access")
    user_validator = IntValidator(session["user_id"])
    if not user_validator.validate():
        return error_page("Server error: invalid user id")
    user_id = user_validator.get()
    
    query_result = sql_handler.get_exercise_logs(user_id)
    if query_result.success:
        return render_template("exercises.html", 
                               exercises = query_result.data,
                               error = None)
    
    return render_template("exercises.html", 
                           exercises = [],
                           error = query_result.data)

@app.route("/exercises/templates", methods=["GET", "POST"])
def exercise_templates() -> str | Any:
    if not("user_id" in session):
        return error_page("Unauthorized access")
    user_validator = IntValidator(session["user_id"])
    if not user_validator.validate():
        return error_page("Server error: invalid user id")
    user_id = user_validator.get()
    
    if request.method == "POST":
        name = request.form.get("name", "").strip() 
        name = request.form.get("category", "").strip() 
        target_sets_validator = IntValidator(request.form["target_sets"])
        target_reps_validator = IntValidator(request.form["target_reps"])
        if not(target_sets_validator.validate() and target_reps_validator.validate()):
            # TODO: Bind the error with the form
            return error_page("Invalud user input: integer is required")
        target_sets = target_sets_validator.get()
        target_reps = target_reps_validator.get()
        sql_handler.insert_exercise_template(user_id, name, category, target_sets, target_reps)
     
    # TODO: Batch queries
    my_exercises = sql_handler.get_exercise_templates(user_id)
    adopted_exercises = sql_handler.get_adopted_exercise_templates(user_id)
    if my_exercises.success and adopted_exercises.success:
        return render_template("exercise-templates.html", 
                               my_templates = my_exercises.data,
                               adopted_templates = adopted_exercises.data,
                               error = None)
    
    if my_exercises.success:
        return render_template("exercise-templates.html", 
                               my_templates = my_exercises.data,
                               adopted_templates = [],
                               error = adopted_exercises.data)
    
    if adopted_exercises.success:
        return render_template("exercise-templates.html", 
                               my_templates = [],
                               adopted_templates = adopted_exercises.data,
                               error = my_exercises.data)
    
    error =  f"{my_exercises.data}\n{adopted_exercises.data}"
    return render_template("exercise-templates.html", 
                           my_templates = [],
                           adopted_templates = [],
                           error = error)

@app.route("/exercises/templates/<int:template_id>", methods=["GET", "POST"])
def exercise_template(template_id: int) -> str | Any:
    if not("user_id" in session):
        return error_page("Unauthorized access")
    user_validator = IntValidator(session["user_id"])
    if not user_validator.validate():
        return error_page("Server error: invalid user id")
    user_id = user_validator.get()
    
    update_notification: str | None = None
    if request.method == "POST":
        if request.form.get("is_delete") == "true":
            sql_handler.delete_exercise_template(user_id, template_id)
            return redirect(url_for("exercise_templates"))
        
        name = request.form.get("name", "").strip() 
        category = request.form.get("category", "").strip()
        target_sets_validator = IntValidator(request.form["target_sets"])
        target_reps_validator = IntValidator(request.form["target_reps"])
        if not(target_sets_validator.validate() and target_reps_validator.validate()):
            # TODO: Bind the error with the form
            return error_page("Invalud user input: integer is required")
        target_sets = target_sets_validator.get()
        target_reps = target_reps_validator.get()
        update_result = sql_handler.update_exercise_template(user_id, template_id, name, category, target_sets, target_reps)
        if update_result.success:
            update_notification = "Templated updated"
        else:
            update_notification = f"Failed to update: {update_result.data}"

    permission_result = sql_handler.get_exercise_template_creator_id(template_id)
    user_is_creator = False
    if permission_result.success:
        user_is_creator = permission_result.data == user_id
    else:
        # Not the proper way, temp implementation 
        return error_page("Server error: template id not in database")
    
    template_result = sql_handler.get_exercise_template_by_id(template_id)
    if template_result.success:
        return render_template("exercise-template.html", 
                               template = template_result.data,
                               has_edit_permission = user_is_creator,
                               notification = update_notification,
                               error = None)
    
    return render_template("exercise-template.html", 
                           template = None,
                           has_edit_permission = user_is_creator,
                           notification = update_notification,
                           error = template_result.data)

@app.route("/exercises/search", methods=["GET"])
def exercises_search() -> str:
    if not("user_id" in session):
        return error_page("Unauthorized access")
    user_validator = IntValidator(session["user_id"])
    if not user_validator.validate():
        return error_page("Server error: invalid user id")
    user_id = user_validator.get()
    
    search_query = request.args.get("query", "").strip() 
    if search_query:
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

@app.route("/exercises/add-template", methods=["POST"])
def exercises_add_template() -> Any:
    if not("user_id" in session):
        return error_page("Unauthorized access")
    user_validator = IntValidator(session["user_id"])
    if not user_validator.validate():
        return error_page("Server error: invalid user id")
    user_id = user_validator.get()
    
    template_id_validator = IntValidator(request.form.get("template_id", "").strip())
    if not template_id_validator.validate():
        return error_page("Server error: invalid exercise template id")
    
    sql_handler.insert_user_exercise_template(user_id, template_id_validator.get())
    return redirect(url_for("exercises_search"))

# Workouts

@app.route("/workouts", methods=["GET"])
def workouts() -> str:
    if not("user_id" in session):
        return error_page("Unauthorized access")
    user_validator = IntValidator(session["user_id"])
    if not user_validator.validate():
        return error_page("Server error: invalid user id")
    user_id = user_validator.get()
    
    query_result = sql_handler.get_workout_logs(user_id)
    if query_result.success:
        return render_template("workouts.html", 
                               workouts = query_result.data,
                               error = None)
    
    return render_template("workouts.html", 
                           workouts = [],
                           error = query_result.data)

@app.route("/workouts/templates", methods=["GET", "POST"])
def workout_templates() -> str:
    # TODO: Implement
    if not("user_id" in session):
        return error_page("Unauthorized access")
    user_validator = IntValidator(session["user_id"])
    if not user_validator.validate():
        return error_page("Server error: invalid user id")
    user_id = user_validator.get()

    if request.method == "POST":
        name = request.form.get("name", "").strip() 
    
    return render_template("workout-templates.html",
                           my_templates = [],
                           adopted_templates = [],
                           error = None)

@app.route("/workouts/search", methods=["GET"])
def workouts_search() -> str:
    # TODO: Implement
    return render_template("search-workouts.html")

@app.route("/workouts/add-template", methods=["POST"])
def workouts_add_template() -> Any:
    # TODO: Implement
    if not("user_id" in session):
        return error_page("Unauthorized access")
    user_validator = IntValidator(session["user_id"])
    if not user_validator.validate():
        return error_page("Server error: invalid user id")
    user_id = user_validator.get()
    
    template_id_validator = IntValidator(request.form.get("template_id", "").strip())
    if not template_id_validator.validate():
        # TODO: Better error handlign
        return error_page("Server error: invalid exercise template id")
    
    return redirect(url_for("workouts_search"))
