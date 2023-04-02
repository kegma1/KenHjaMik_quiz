from flask import Flask, render_template, request, url_for, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import Form, StringField, PasswordField, validators, ValidationError, RadioField
import secrets
import mysql.connector
from db_loggin import dbconfig

conn = mysql.connector.connect(**dbconfig)
cursor = conn.cursor(prepared=True)

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)

class LoginForm(Form):
    username = StringField("Brukernavn", [validators.Length(min=4, max=25), validators.DataRequired()])
    password = PasswordField("Passord", [validators.DataRequired()])
    login_type = RadioField("", choices=[("play", "Play"), ("edit", "Edit")], default="play")

    user_data = None

    def set_user(self, username):
        cursor.execute("SELECT Username, Password, Is_admin  FROM `user` WHERE Username = %s;", (username,))
        self.user_data = cursor.fetchone()

    def validate_username(self, username):
        self.set_user(username.data)
        if self.user_data == None:
            raise ValidationError(f"User '{username.data}' does not exist")
        
    def validate_password(self, password):
        if self.user_data != None:
            pwd = self.user_data[1]
            if not check_password_hash(pwd, password.data):
                raise ValidationError("Wrong password")

            
    def validate_login_type(self, login_type):
        if login_type.data == "edit":
            if self.user_data != None:
                is_admin = self.user_data[2]
                if is_admin != 1:
                    raise ValidationError("Access denide")


@app.route("/", methods = ["GET", "POST"])
def index():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        print("login", form.login_type.data) 
        if form.login_type.data == "edit":
            session["is_logged_in"] = True
            session["username"] = form.username.data
            session["is_admin"] = True
            return redirect(url_for("edit_list"))
        else:
            session["is_logged_in"] = True
            session["is_admin"] = False
            session["username"] = form.username.data
            return redirect(url_for("play_list"))
        
    return render_template("index.html", title="login", form=form)

class RegisterUserForm(Form):
    username = StringField('Brukernavn', [validators.Length(min=4, max=25), validators.DataRequired()])
    password = PasswordField('Passord', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Bekreft passord')

    def validate_username(self, username):
        get_users_query = "SELECT Username FROM `user` WHERE Username = %s;"
        cursor.execute(get_users_query, (username.data,))
        if cursor.fetchall() != []:
            raise ValidationError("Username already exists")

@app.route("/signup", methods = ["GET", "POST"])
def sign_up():
    form = RegisterUserForm(request.form)
    if request.method == "POST" and form.validate():
        usename = form.username.data
        password = form.password.data
        
        hashed_password = generate_password_hash(password)
        creat_new_user_query = """
           INSERT INTO `user` (`Username`, `Password`, `Is_admin`) VALUES (%s, %s, 0) 
        """
        args = (usename, hashed_password)
        cursor.execute(creat_new_user_query, args)
        conn.commit()
        return redirect(url_for("index"))

    return render_template("sign_up.html", title="sign up", form=form)


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