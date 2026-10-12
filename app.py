import sqlite3
import secrets
import config
import utils
import users as users_repo
import exercises as exercises_repo
import workouts as workouts_repo
from typing import Any
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
    authenticated = not(user_id is None)
    if authenticated:
        users = users_repo.get_other_users(int(user_id))
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
        if user_id: 
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
    session.clear()
    return redirect(url_for("home"))

@app.route("/profile/<int:user_id>")
def profile(user_id: int) -> str | Any:
    get_auth_user()
    profile_info = users_repo.get_user_profile_info(user_id)
    if not profile_info:
        abort(PAGE_NOT_FOUND)
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
        exercise_id = int(str(request.form.get("exercise_id")))
        exercises_repo.delete_exercise_log(user_id, exercise_id)
    e = exercises_repo.get_exercise_logs(user_id)
    return render_template("exercises.html", exercises = e)

@app.route("/exercises/<int:exercise_id>", methods = ["GET"])
def view_exercise(exercise_id: int) -> str | Any:
    user_id = get_auth_user()
    e = exercises_repo.get_exercise_log(exercise_id)
    if not e:
        abort(PAGE_NOT_FOUND)
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
            et_id = int(request.form["template_id"])
            exercises_repo.delete_my_exercise_template(user_id, et_id)
            return redirect(url_for("exercise_templates"))
        if request.form.get("is_pop_owner_template") == "true":
            et_id = int(request.form["template_id"])
            exercises_repo.delete_my_exercise_template_latest_version(user_id, et_id)
            return redirect(url_for("exercise_templates"))
        if request.form.get("is_delete_adopted_template") == "true":
            et_id = int(request.form["template_id"])
            exercises_repo.delete_adopted_exercise_template(user_id, et_id)
            return redirect(url_for("exercise_templates"))
        if request.form.get("is_pop_adopted_template") == "true":
            et_id = int(request.form["template_id"])
            prev_version_id = exercises_repo.get_exercise_template_previous_version_id(et_id)
            if not prev_version_id:
                print("prev_version_id does not exist")
                abort(BAD_REQUEST)
            exercises_repo.update_adopted_exercise_template(user_id, et_id, prev_version_id)
            return redirect(url_for("exercise_templates"))
        if request.form.get("is_update_adopted_template") == "true":
            et_id = int(request.form["template_id"])
            next_version_id = exercises_repo.get_exercise_template_next_version_id(et_id)
            if not next_version_id:
                print("next_version_id does not exist")
                abort(BAD_REQUEST)
            exercises_repo.update_adopted_exercise_template(user_id, et_id, next_version_id)
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
    get_previous = request.args.get("get_previous")
    is_latest_version = True
    if get_previous == "true":
        prev_template_id = exercises_repo.get_exercise_template_previous_version_id(template_id)
        if not prev_template_id:
            abort(BAD_REQUEST)
        template_id = prev_template_id
        is_latest_version = False
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
            return redirect(url_for("exercise_templates"))
    
    template = exercises_repo.get_exercise_template(template_id)
    if not template:
        abort(PAGE_NOT_FOUND)
    comments = exercises_repo.get_excercise_template_comments(template_id)
    creator_id = exercises_repo.get_exercise_template_creator_id(template_id)
    return render_template("exercise-template.html",
                           template = template,
                           comments = comments,
                           # Only the latest version can be modified
                           editable = is_latest_version and creator_id == user_id)

@app.route("/exercises/search", methods = ["GET", "POST"])
def exercises_search() -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        template_id = int(str(request.form.get("template_id")))
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
        workout_id = int(str(request.form.get("workout_id")))
        workouts_repo.delete_workout_log(user_id, workout_id) 
    w = workouts_repo.get_workout_logs(user_id)
    return render_template("workouts.html", workouts = w)

@app.route("/workouts/<int:workout_id>", methods = ["GET", "POST"])
def view_workout(workout_id: int) -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        if request.form.get("is_delete_exercise") == "true":
            exercise_id = int(str(request.form.get("exercise_id")))
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
            wet_id = int(str(request.form.get("wet_id")))
            workouts_repo.add_exercise_to_workout_log(workout_id, wet_id, name, reps_lst, weights_lst)

    workout = workouts_repo.get_workout_log(workout_id)
    if not workout:
        abort(PAGE_NOT_FOUND)
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
        if request.form.get("wt_commit") == "true":
            wt_id = int(request.form["wt_id"])
            wt_name = request.form["wt_name"]
            wt_desc = request.form["wt_desc"]
            #workouts_repo.add_workout_log(user_id, wt_id, wt_name, wt_desc) 
            return redirect(url_for("workouts"))
        if request.form.get("wt_delete_owner") == "true":
            wt_id = int(request.form["wt_id"])
            workouts_repo.delete_my_workout_template(user_id, wt_id)
            return redirect(url_for("workout_templates"))
        if request.form.get("wt_pop_owner") == "true":
            wt_id = int(request.form["wt_id"])
            workouts_repo.delete_my_workout_template_latest_version(user_id, wt_id)
            return redirect(url_for("workout_templates"))
     
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

@app.route("/workouts/templates/create", methods = ["GET", "POST"])
def create_workout_template() -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        if request.form.get("wt_submit") == "true": 
            name = request.form.get("name", "").strip() 
            if not name:
                flash("[VIRHE] Treenillä on oltava nimi")
                return redirect(url_for("create_workout_template"))
            desc = request.form.get("desc", "").strip()
            tags_input = request.form.get("tags", "").strip()
            tags = tags_input.split(",") if tags_input else [] 
            tag_count = len(tags)
            tags = [t.strip() for t in tags if t.strip()]
            if len(tags) != tag_count:
                flash("[VIRHE] Virheellinen luokitus")
                return redirect(url_for("create_workout_template"))    
            exercises = [
                int(e["exercise_template_id"])
                for e in session["wtc"]["exercises"]
            ]
            if exercises:
                workouts_repo.add_my_workout_template(user_id, name, desc, tags, exercises)
                del session["wtc"]
                return redirect(url_for("workout_templates"))
            flash("[VIRHE] Treenillä on oltava harjoituksia")
            
            name = session["wtc"]["name"] = name
            desc = session["wtc"]["description"] = desc
            tags = session["wtc"]["tags"] = tags
            session["wtc"]["modified"] = True
            session.modified = True
    
        elif request.form.get("et_add") == "true":
            exercise_id = int(request.form["et_id"])
            exercise = workouts_repo.get_exercise_template(exercise_id)
            if not exercise:
                abort(BAD_REQUEST)
            session["wtc"]["exercises"].append(dict(exercise))
            session["wtc"]["modified"] = True
            session.modified = True
        else:
            # Remove
            et_id = int(request.form["et_id"])
            # Remove first in case there are many instances of the same exercise
            remove_index = -1
            for index, e in enumerate(session["wtc"]["exercises"]):
                if e["exercise_template_id"] == et_id:
                    remove_index = index
                    break
            if remove_index != -1:
                del session["wtc"]["exercises"][remove_index]
                session["wtc"]["modified"] = True
                session.modified = True
            else:
                flash("Harjoitusta ei ole lisätty pohjaan")
        
        return render_template("create-workout-template.html") 
    
    # GET
    # This session won't preserve between visits to different pages
    # The session handling becomes too complex with many edge cases 
    # for trying to accomplish that
    if "wtc" in session:
        del session["wtc"]
    my_exercise_templates = exercises_repo.get_exercise_templates(user_id)
    session["wtc"] = {
        "user_id": user_id,
        "name": "",
        "description": "",
        "tags": [],
        "exercises": [],
        "my_templates": [dict(et) for et in my_exercise_templates]
    }
    return render_template("create-workout-template.html") 

@app.route("/workouts/templates/edit", methods = ["GET", "POST"])
def edit_workout_template() -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST":
        check_csrf()
        if request.form.get("wt_submit") == "true": 
            name = request.form.get("name", "").strip() 
            if not name:
                flash("[VIRHE] Treenillä on oltava nimi")
                return redirect(url_for("edit_workout_template", 
                                        wt_id = session["wte"]["template_id"]))
            desc = request.form.get("desc", "").strip()
            tags_input = request.form.get("tags", "").strip()
            tags = tags_input.split(",") if tags_input else [] 
            tag_count = len(tags)
            tags = [t.strip() for t in tags if t.strip()]
            if len(tags) != tag_count:
                flash("[VIRHE] Virheellinen luokitus")
                return redirect(url_for("edit_workout_template",
                                        wt_id = session["wte"]["template_id"]))    
            exercises = [
                int(e["exercise_template_id"])
                for e in session["wte"]["exercises"]
            ]
            if exercises:
                template_id = session["wte"]["template_id"]
                workouts_repo.update_my_workout_template(user_id, template_id, name, desc, tags, exercises)
                del session["wte"]
                return redirect(url_for("workout_templates"))
            flash("[VIRHE] Treenillä on oltava harjoituksia")
            
            session["wte"]["name"] = name
            session["wte"]["description"] = desc
            session["wte"]["tags"] = tags
            session.modified = True
    
        elif request.form.get("et_add") == "true":
            exercise_id = int(request.form["et_id"])
            exercise = workouts_repo.get_exercise_template(exercise_id)
            if not exercise:
                abort(BAD_REQUEST)
            session["wte"]["exercises"].append(dict(exercise))
            session.modified = True
        else:
            # Remove
            et_id = int(request.form["et_id"])
            # Remove first in case there are many instances of the same exercise
            remove_index = -1
            for index, e in enumerate(session["wte"]["exercises"]):
                if e["exercise_template_id"] == et_id:
                    remove_index = index
                    break
            if remove_index != -1:
                del session["wte"]["exercises"][remove_index]
                session.modified = True
            else:
                flash("Harjoitusta ei ole lisätty pohjaan")
        
        return render_template("edit-workout-template.html")
    
    # GET
    # This session won't preserve between visits to different pages
    # The session handling becomes too complex with many edge cases 
    # for trying to accomplish that
    if "wte" in session:
        del session["wte"]
    template_id = request.args.get("wt_id")
    wt_id = int(str(template_id))
    wt = workouts_repo.get_workout_template(wt_id) 
    if not wt:
        abort(BAD_REQUEST)
    name = wt["name"]
    description = wt["description"] or ""
    tags = wt["tags"].split(",") if wt["tags"] else []
    exercises = workouts_repo.get_workout_template_exercises(user_id, wt_id)
    my_exercise_templates = exercises_repo.get_exercise_templates(user_id)
    session["wte"] = {
        "modified": False,
        "user_id": user_id,
        "template_id": template_id,
        "name": name,
        "description": description,
        "tags": tags,
        "exercises": [dict(et) for et in exercises],
        "my_templates": [dict(et) for et in my_exercise_templates]
    }
            
    return render_template("edit-workout-template.html")

@app.route("/workouts/templates/<int:template_id>", methods = ["GET", "POST"])
def view_workout_template_(template_id: int) -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST": 
        check_csrf()
        if request.form.get("wt_update") == "true":
            name = session["wt_edit"]["template"]["name"]
            desc = session["wt_edit"]["template"]["description"]
            tags = session["wt_edit"]["tags"]
            print(session["wt_edit"])
            exercise_template_ids = [
                int(e["exercise_template_id"])
                for e in session["wt_edit"]["exercises"]
            ] 
            workouts_repo.update_workout_template(user_id, template_id, name, desc, tags)
            workouts_repo.update_workout_template_exercises(user_id, template_id, exercise_template_ids)
            del session["wt_edit"]
            return redirect(url_for("workout_templates"))
        if request.form.get("et_remove") == "true":
            et_index = int(request.form["et_index"])
            del session["wt_edit"]["exercises"][et_index]
            session.modified = True
        elif request.form.get("wt_comment") == "true":
            content = request.form.get("content", "").strip()
            workouts_repo.add_workout_template_comment(user_id, template_id, content)
        else:
            # Update template
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
            session["wt_edit"]["template"]["name"] = name
            session["wt_edit"]["template"]["description"] = desc
            session["wt_edit"]["tags"] = tags
            session.modified = True
    
    if not("wt_edit" in session):
        first_or_prev_workout_id = workouts_repo.get_previous_workout_template_id(template_id)
        print(first_or_prev_workout_id)
        template = workouts_repo.get_workout_template(first_or_prev_workout_id)
        if not template:
            abort(PAGE_NOT_FOUND)
        tags = template["tags"].split(",") if template["tags"] else []
        exercises = workouts_repo.get_workout_template_exercises(user_id, first_or_prev_workout_id)
        session["wt_edit"] = {
            "template": dict(template),
            "tags": tags,
            "exercises": [dict(e) for e in exercises] 
        }
    comments = workouts_repo.get_workout_template_comments(template_id)
    creator_id = workouts_repo.get_workout_template_creator_id(template_id) 
    return render_template("workout-template.html",
                           comments = comments,
                           editable = user_id == creator_id)

@app.route("/workouts_/templates/<int:template_id>", methods = ["GET", "POST"])
def view_workout_template_OLD(template_id: int) -> str | Any:
    user_id = get_auth_user()
    if request.method == "POST": 
        check_csrf()
        if request.form.get("is_remove_exercise") == "true":
            exercise_id = int(str(request.form.get("exercise_template_id")))
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
        abort(PAGE_NOT_FOUND)
    tags = template["tags"].split(",") if template["tags"] else []
    exercises = workouts_repo.get_workout_template_exercises(user_id, template_id)
    comments = workouts_repo.get_workout_template_comments(template_id)
    creator_id = workouts_repo.get_workout_template_creator_id(template_id)
    return render_template("workout-template.html",
                           template = template,
                           tags = tags,
                           exercises = exercises,
                           comments = comments,
                           editable = user_id == creator_id)

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
        template_id = int(str(request.form.get("template_id")))
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
