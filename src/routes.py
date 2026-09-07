import sqlite3
from typing import Any
from flask import render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from .repository import sql_handler
from .app import app

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
        user = sql_handler.get_user_by_username(username) 
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        return render_template(
                    "login.html",
                    error = "Invalid username or password.")
    return render_template("login.html")
