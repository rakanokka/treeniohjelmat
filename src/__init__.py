from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template(
        "index.html",
        content="Home page"
    )

@app.route("/login")
def login():
    return render_template(
        "login.html",
        content="Login page"
    )
