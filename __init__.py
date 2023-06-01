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
    login_type = RadioField("", choices=[("play", "Play"), ("edit", "Admin")], default="play")

    user_data = None

    def set_user(self, username):
        cursor.execute("SELECT username, password, isAdmin  FROM `user` WHERE username = %s;", (username,))
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
                    raise ValidationError("Access denied")


@app.route("/", methods = ["GET", "POST"])
def index():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
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
    username = StringField('Brukernavn', [validators.Length(min=4, max=255), validators.DataRequired()])
    firstName = StringField('First name', [validators.Length(min=4, max=255), validators.DataRequired()])
    lastName = StringField('Last name', [validators.Length(min=4, max=255), validators.DataRequired()])
    password = PasswordField('Passord', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Bekreft passord')

    def validate_username(self, username):
        get_users_query = "SELECT username FROM `user` WHERE username = %s;"
        cursor.execute(get_users_query, (username.data,))
        if cursor.fetchall() != []:
            raise ValidationError("Username already exists")

@app.route("/signup", methods = ["GET", "POST"])
def sign_up():
    form = RegisterUserForm(request.form)
    if request.method == "POST" and form.validate():
        usename = form.username.data
        password = form.password.data
        firstName = form.firstName.data
        lastName = form.lastName.data
        
        hashed_password = generate_password_hash(password)
        creat_new_user_query = """
           INSERT INTO `user` (`username`, `password`, `isAdmin`, `firstName`, `lastName`) VALUES (%s, %s, 0, %s, %s) 
        """
        args = (usename, hashed_password, firstName, lastName)
        cursor.execute(creat_new_user_query, args)
        conn.commit()
        return redirect(url_for("index"))

    return render_template("sign_up.html", title="sign up", form=form)


# ------------------ Edit -------------------

class Quiz(Form):
    quizName = StringField('Quiz name', [validators.Length(min=1, max=25), validators.DataRequired()])
    quizTheme = StringField('Quiz description')

@app.route("/edit", methods = ["GET", "POST"])
def edit_list():
    if "is_admin" in session and "is_logged_in" in session:
        if session["is_admin"] and session["is_logged_in"]:
            form = Quiz(request.form)
            if request.method == "POST" and form.validate():
                name = form.quizName.data
                theme = form.quizTheme.data

                creat_new_quiz_query = """INSERT INTO `quiz` (`name`, `description`) VALUES (%s, %s)"""

                args = (name, theme)
                cursor.execute(creat_new_quiz_query, args)
                conn.commit()
                return redirect(url_for('edit_list'))
            
            get_quiz_query = "SELECT name, description, quiz_ID, totalQuestions FROM `quiz`"
            cursor.execute(get_quiz_query)
            quizList = cursor.fetchall()
            
            return render_template("MakeQuiz.html", title="Quiz list", quizList = quizList, form = form)
    return redirect(url_for("index"))

class Question(Form):
    question = StringField('Question', [validators.Length(min=1, max=100), validators.DataRequired()])
    
    type = RadioField('', choices=[(1, 'Multichoice'), (2, 'Essay'), (3, 'Multiple Choice')], default = None)

@app.route('/edit/quiz<int:id>', methods =['GET', 'POST'])
def edit_quiz(id):
    if "is_admin" in session and "is_logged_in" in session:
        if session["is_admin"] and session["is_logged_in"]:
            quizID = id
            form = Question(request.form)
            if request.method == 'POST' and form.validate():
                question = form.question.data
                type = form.type.data

                if type == '2':
                    creat_new_question = """INSERT INTO `question` (Question, questionType, quiz) VALUES (%s, %s, %s)"""
                    args = (question, type, id)
                    cursor.execute(creat_new_question, args)
                    conn.commit()
                    PlusCount(quizID)
                    return redirect(url_for('edit_quiz', id = id))
                elif type == '1' or type == '3':
                    return redirect(url_for('edit_question', id = id, questionid = None, argument = [question, type]))
            
            get_question_query = "SELECT Question, Question_ID, Quiz FROM `question` WHERE Quiz = %s"
            questionid = [id]
            cursor.execute(get_question_query, questionid)
            questionList = cursor.fetchall()

            get_quiz_theme_query = "SELECT name, description, quiz_ID FROM `quiz` WHERE quiz_ID = %s"
            cursor.execute(get_quiz_theme_query, questionid)
            quizInfo = cursor.fetchall()

            quiz_len = len(questionList)
                
            return render_template("MakeQuestion.html", title="Quiz editing", quizID = quizID, quiz_len = quiz_len, questionList = questionList, form = form, quizInfo = quizInfo)
    return redirect(url_for("index"))

@app.route('/edit/update<int:quizid>', methods = ["GET", "POST"])
def configure_quiz(quizid):
    form = Quiz(request.form)
    if request.method == "POST" and form.validate():
        name = form.quizName.data
        theme = form.quizTheme.data

        creat_new_quiz_query = "UPDATE `quiz` SET Quiz_name = %s, Quiz_description = %s WHERE Quiz_ID = %s"

        args = (name, theme, quizid)
        cursor.execute(creat_new_quiz_query, args)
        conn.commit()
    return redirect(url_for("edit_quiz", id = quizid))

class Options(Form):
    option1 = StringField('Option 1', [validators.Length(min=1, max=100), validators.DataRequired()])
    option2 = StringField('Option 2', [validators.Length(min=1, max=100), validators.DataRequired()])
    option3 = StringField('Option 3', [validators.Length(min=1, max=100), validators.DataRequired()])
    option4 = StringField('Option 4', [validators.Length(min=1, max=100), validators.DataRequired()])

@app.route('/edit/quiz<int:quizid>/question<int:questionid>', methods = ['GET', 'POST'])
def edit_question(quizid, questionid, arguments):
    if "is_admin" in session and "is_logged_in" in session:
        if session["is_admin"] and session["is_logged_in"]:
            questionForm = Question(request.form)
            optionsForm = Options(request.form)

            if request.method == "POST" and questionForm.validate() and optionsForm.validate():
                question = questionForm.question.data
                type = questionForm.type.data

                option1 = optionsForm.option1.data
                option2 = optionsForm.option2.data
                option3 = optionsForm.option3.data
                option4 = optionsForm.option4.data

                creat_new_options = "UPDATE `choices` SET choice1 = %s, choice2 = %s, choice3 = %s, choice4 = %s, question_question_ID = %s, question_quiz = %s WHERE choices_ID = %s"
                creat_new_question = "UPDATE `question` SET Question = %s, questionType = %s WHERE Question_ID = %s"
                args = (question, questionid)
                
                cursor.execute(creat_new_question, args)
                conn.commit() 
                return redirect(url_for("edit_quiz", id = quizid))

            creat_question_query = "SELECT Question, Answer1, Answer2, Answer3, Answer4, Correct_answer, Quiz FROM `question` WHERE Question_ID = %s"
            arg = [questionid]
            cursor.execute(creat_question_query, arg)
            questionInfo = cursor.fetchone()
            return render_template("EditQuestion.html", title="Question editing", info = questionInfo, questionID = questionid, questionForm=questionForm, optionsForm=optionsForm)
    return redirect(url_for("index"))

@app.route('/deleteQuiz/<int:id>')
def deleteQuiz(id):
    if "is_admin" in session and "is_logged_in" in session:
        if session["is_admin"] and session["is_logged_in"]:
            id = [id]
            delQuestionQuery = "DELETE FROM `question` WHERE Quiz = %s"
            delQuery = "DELETE FROM `quiz` WHERE quiz_ID = %s"
            
            cursor.execute(delQuestionQuery, id)
            cursor.execute(delQuery, id)
            conn.commit()
            return redirect(url_for('edit_list'))
    return f'Fuck you'


@app.route('/edit/delete/question/<int:questionid>/<int:quizid>')
def deleteQuestion(questionid, quizid):
    if "is_admin" in session and "is_logged_in" in session:
        if session["is_admin"] and session["is_logged_in"]:

            id = [questionid]
            delQuery = "DELETE FROM `question` WHERE Question_ID = %s"
            
            cursor.execute(delQuery, id)
            conn.commit()
            MinusCount(quizid)
            return redirect(url_for('edit_quiz', id = quizid))
    return f'Fuck you'


def PlusCount(quizID):
    get_question_query = "SELECT totalQuestions FROM `quiz` WHERE quiz_ID = %s"
    args = [quizID]
    cursor.execute(get_question_query, args)
    (value,) = cursor.fetchone()
    value += 1

    update_question_query = "UPDATE `quiz` SET totalQuestions = %s WHERE quiz_ID = %s"
    arg = (value, quizID)
    cursor.execute(update_question_query, arg)
    conn.commit()

def MinusCount(quizID):
    get_question_query = "SELECT totalQuestions FROM `quiz` WHERE quiz_ID = %s"
    args = [quizID]
    cursor.execute(get_question_query, args)
    (value,) = cursor.fetchone()
    value -= 1
    
    update_question_query = "UPDATE `quiz` SET totalQuestions = %s WHERE quiz_ID = %s"
    arg = (value, quizID)
    cursor.execute(update_question_query, arg)
    conn.commit()

# ------------------ Play -------------------

@app.route("/play", methods=["POST", "GET"])
def play_list():
    if "is_logged_in" in session and session["is_logged_in"]:

        cursor.execute("SELECT * FROM `quiz`")
        all_quizzes = cursor.fetchall()
        all_quizzes_len = len(all_quizzes)

        return render_template("play_list.html", title="All quizzes", all_quizzes = all_quizzes, a_q_len = all_quizzes_len)

    return redirect(url_for("index"))



@app.route("/play/<quiz>", methods=["POST", "GET"])
def play_quiz(quiz):
    if "is_logged_in" in session and session["is_logged_in"]:

        if not ("questions" in session and "curr_question" in session):
            return redirect(url_for("play_list"))
         
        if request.method == 'POST':
            return redirect(url_for("next_question", quiz = quiz))
            
        return render_template("play_quiz.html", title='Playing', question=session["curr_question"][1])

    return redirect(url_for("index"))

@app.route("/play/<quiz>/get")
def get_question(quiz):
    if "is_logged_in" in session and session["is_logged_in"]:
        
        get_quiz_query = '''
        SELECT * FROM `question`
        WHERE quiz = %s
        '''
        
        cursor.execute(get_quiz_query, (quiz,))
        session["questions"] = cursor.fetchall()
        session["curr_question"] = session["questions"][0]
        session["questions"].pop(0)
                    
        return redirect(url_for('play_quiz', quiz = quiz))

    return redirect(url_for("index"))

@app.route("/play/<quiz>/next")
def next_question(quiz):
    if "is_logged_in" in session and session["is_logged_in"]:

        if not ("questions" in session and "curr_question" in session):
            return redirect(url_for("play_list"))
        
        if session["questions"]:
            session["curr_question"] = session["questions"][0]
            session["questions"].pop(0)
        else:
            return redirect(url_for('play_list'))
            
        return redirect(url_for('play_quiz', quiz = quiz))

    return redirect(url_for("index"))
    
if __name__ == "__main__":
    app.run()