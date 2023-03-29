from flask import Flask, render_template, request, url_for, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import mysql.connector
from db_loggin import dbconfig

conn = mysql.connector.connect(**dbconfig)
cursor = conn.cursor()

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)

@app.route("/", methods = ["GET", "POST"])
def index():
    return render_template("index.html", title="login")

@app.route("/login", methods = ["POST"])
def login():
    if request.method == "POST":
        print(request.form["select"])
        if request.form["select"] == "edit":
            ## check if is admin
            session["is_logged_in"] = True
            session["is_admin"] = True
            session["username"] = request.form["username"]

            return redirect(url_for("edit_list"))
        else:
            session["is_logged_in"] = True
            session["is_admin"] = False
            session["username"] = request.form["username"]

            return redirect(url_for("play_list"))

@app.route("/edit")
def edit_list():
    if "is_admin" in session and "is_logged_in" in session:
        if session["is_admin"] and session["is_logged_in"]:
            return "access granted"

    return "access denied"

@app.route("/edit/<quiz>")
def edit_quiz(quiz):
    if "is_admin" in session and "is_logged_in" in session:
        if session["is_admin"] and session["is_logged_in"]:
            return f"access granted {quiz}"

    return "access denied"

@app.route("/play")
def play_list():
    if "is_logged_in" in session:
        if session["is_logged_in"]:
            return "access granted"

    return "access denied"

@app.route("/play/<quiz>")
def play_quiz(quiz):
    if "is_logged_in" in session:
        if session["is_logged_in"]:
            return f"access granted {quiz}"

    return "access denied"


if __name__ == "__main__":
    app.run()