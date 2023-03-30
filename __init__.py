from flask import Flask, render_template, request, url_for, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import mysql.connector
from db_loggin import dbconfig

conn = mysql.connector.connect(**dbconfig)
cursor = conn.cursor(prepared=True)

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)

@app.route("/")
def index():
    return render_template("index.html", title="login")

@app.route("/login", methods = ["POST"])
def login():
    if request.method == "POST":

        get_users_query = "SELECT Username, Password, Is_admin  FROM `user` WHERE Username = %s;"
        cursor.execute(get_users_query, (request.form["username"],))
        user = cursor.fetchone()
        # check if password is correct
        if not check_password_hash(user[1], request.form["password"]):
            return redirect(url_for("index"))

        if request.form["select"] == "edit":
            session["is_logged_in"] = True
            session["username"] = request.form["username"]

            if user[2] == 1:
                session["is_admin"] = True
            else:
                session["is_admin"] = False

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

    return redirect(url_for("index"))

@app.route("/edit/<quiz>")
def edit_quiz(quiz):
    if "is_admin" in session and "is_logged_in" in session:
        if session["is_admin"] and session["is_logged_in"]:
            return f"access granted {quiz}"

    return redirect(url_for("index"))

@app.route("/play")
def play_list():
    if "is_logged_in" in session:
        if session["is_logged_in"]:
            return "access granted"

    return redirect(url_for("index"))

@app.route("/play/<quiz>")
def play_quiz(quiz):
    if "is_logged_in" in session:
        if session["is_logged_in"]:
            return f"access granted {quiz}"

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run()