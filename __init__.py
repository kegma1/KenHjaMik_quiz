from flask import Flask, render_template, request, url_for, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import Form, StringField, PasswordField, validators, ValidationError, RadioField, FieldList, FormField, SubmitField
import secrets
import mysql.connector
from db_loggin import dbconfig
import datetime

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
        conn.commit()

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
            
            return render_template("make_quiz.html", title="Quiz list", quizList = quizList, form = form)
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
                
            return render_template("make_question.html", title="Quiz editing", quizID = quizID, quiz_len = quiz_len, questionList = questionList, form = form, quizInfo = quizInfo)
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
            return render_template("make_question.html", title="Question editing", info = questionInfo, questionID = questionid, form=questionForm)
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

        return render_template("play_list.html",\
            title="All quizzes",\
            all_quizzes = all_quizzes, \
            a_q_len = all_quizzes_len
        )

    return redirect(url_for("index"))


@app.route("/play/<quiz>", methods=["POST", "GET"])
def play_quiz(quiz):
    if "is_logged_in" in session and session["is_logged_in"]:

        if not ("questions" in session and "curr_question" in session):
            return redirect(url_for("play_list"))
         
        if request.method == 'POST':
            answer = ""
            if session["curr_question"][1] == "Essay":
                answer = request.form["essey_textarea"]
            elif session["curr_question"][1] == "Flervalg":
                answer = "".join(request.form.getlist("cb_choice"))
            elif session["curr_question"][1] == "Multiple choice":
                answer = str(request.form["mc_choice"])

            temp_answers = session["answers"]
            temp_answers.append((answer, session["curr_question"][3]))
            session["answers"] = temp_answers

            return redirect(url_for("next_question", quiz = quiz))
            
        choices = None
        if session["curr_question"][1] != "Essay":
            choices = get_choices(quiz, session["curr_question"][3])

        return render_template("play_quiz.html",\
            title=f'Playing {session["curr_question"][2]}',\
            question=session["curr_question"][0],\
            question_type=session["curr_question"][1],\
            choices=choices
        )

    return redirect(url_for("index"))

def get_choices(quiz, question):
    query = """
        SELECT choice1, choice2, choice3, choice4 FROM `choices` 
        WHERE question_quiz = %s AND question_question_ID = %s
    """
    cursor.execute(query, (quiz, question))
    x = cursor.fetchone()
    conn.commit()
    return x

@app.route("/play/<quiz>/get")
def get_question(quiz):
    if "is_logged_in" in session and session["is_logged_in"]:
        
        get_quiz_query = '''
        SELECT q.question, qt.type, qz.name, q.question_ID  FROM `question` q
        INNER JOIN `questionType` qt on q.questionType = qt.questionType_ID 
        INNER JOIN `quiz` qz on q.quiz = qz.quiz_ID
        WHERE q.quiz = %s
        '''
        cursor.execute(get_quiz_query, (quiz,))
        session["questions"] = cursor.fetchall()
        session["curr_question"] = session["questions"][0]
        session["questions"].pop(0)
        session["answers"] = []
                    
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
            insert_query = """
                INSERT INTO `answer` (`answer`, `question`, `user`, `status`, `time_of_playthough`) 
                VALUES (%s, %s, %s, 1, %s) 
            """
            time_of_playthough = datetime.datetime.now()
            for answer, question in session["answers"]:
                args = (answer, question, session["username"], time_of_playthough)
                cursor.execute(insert_query, args)
            conn.commit()
            return redirect(url_for('play_list'))
            
        return redirect(url_for('play_quiz', quiz = quiz))

    return redirect(url_for("index"))

# ------------------ View result -------------------
@app.route("/results")
def list_playthroughts():
    if "is_logged_in" in session and session["is_logged_in"]:
        get_playtroughs_query = """
            SELECT qz.name, cs.status, a.time_of_playthough, SUM(a.status), qz.totalQuestions FROM `answer` a
            INNER JOIN `correctionStatus` cs ON a.status = cs.correctionStatus_ID
            INNER JOIN `question` q ON a.question = q.question_ID
            INNER JOIN `quiz` qz ON q.quiz = qz.quiz_ID
            WHERE a.user = %s
            GROUP BY `time_of_playthough`
        """
        cursor.execute(get_playtroughs_query, (session["username"],))
        playtroughs = cursor.fetchall()
        conn.commit()
        
        return render_template("list_playthoughs.html",\
            title=f"{session['username']}'s results",\
            playtroughs=playtroughs\
        )
    return redirect(url_for("index"))

@app.route("/results/<playthrough>")
def view_playthrought(playthrough):
    if "is_logged_in" in session and session["is_logged_in"]:
        get_answers_query = """
            SELECT cs.status, a.comment, a.answer, q.question, qt.type, a.question, q.quiz FROM `answer` a
            INNER JOIN `correctionStatus` cs ON a.status = cs.correctionStatus_ID
            INNER JOIN `question` q ON a.question = q.question_ID
            INNER JOIN `quiz` qz ON q.quiz = qz.quiz_ID
            INNER JOIN `questionType` qt ON q.questionType = qt.questionType_ID
            WHERE a.user = %s and a.time_of_playthough = %s
            ORDER BY q.question_ID
        """
        cursor.execute(get_answers_query, (session["username"], playthrough))
        answers = cursor.fetchall()
        conn.commit()
        
        return render_template("view_playtrough.html",\
            title=f"{playthrough}",\
            answers=answers,\
            fetch_options=fetch_options\
        )
    return redirect(url_for("index"))

def fetch_options(quiz, question, type, answer):
    choices = get_choices(quiz, question)
    
    if type == "Flervalg":
        html = ""
        for i, choice in enumerate(choices, start=1):
            is_checked = str(i) in answer
            html += f"<input type='checkbox' name='cb_choice' id='cb-{i}' {'checked' if is_checked else 'disabled'}><label for='cb-{i}'>{choice}</label><br>"
        return html
    elif type == "Multiple choice":
        html = ""
        for i, choice in enumerate(choices, start=1):
            is_checked = str(i) in answer
            html += f"<input type='radio'  id='mc-{i}' {'checked' if is_checked else 'disabled'} {'checked' if is_checked else ''}><label for='mc-{i}'>{choice}</label><br>"
        return html

# ------------------ Grading -------------------

@app.route("/grading", methods=["POST", "GET"])
def grading():
    if "is_logged_in" in session and session["is_logged_in"] and "is_admin" in session:
        cursor.execute("SELECT quiz_ID, name, description, totalQuestions FROM `quiz`")
        quizzes = cursor.fetchall()
    
        return render_template('grading.html', quizzes = quizzes, q_len = len(quizzes))
    
    return redirect(url_for("index"))

@app.route("/grading/<quiz_ID>", methods=["POST", "GET"])
def quiz_grading(quiz_ID):
    if "is_logged_in" in session and session["is_logged_in"]and "is_admin" in session:
        
        quiz_unique_query = '''
            SELECT a.user, a.time_of_playthough, SUM(a.status) AS stat, qz.totalQuestions AS totq
            FROM answer a
            INNER JOIN correctionStatus cs ON a.status = cs.correctionStatus_ID
            INNER JOIN question q ON a.question = q.question_ID
            INNER JOIN quiz qz ON q.quiz = qz.quiz_ID
            WHERE qz.quiz_ID = %s
            GROUP BY a.user, a.time_of_playthough, qz.totalQuestions
            HAVING SUM(a.status) = qz.totalQuestions;
        '''
        cursor.execute(quiz_unique_query, (quiz_ID,))
        quiz_unique_users = cursor.fetchall()
        conn.commit()
                
        return render_template("grading_quiz.html", quiz_ID = quiz_ID, quiz_users = quiz_unique_users)
        
    return redirect(url_for("index"))
    
@app.route("/grading/<quiz_ID>/<user>/<time>", methods=["POST", "GET"])
def user_quiz_grading(quiz_ID, user, time):
    if "is_logged_in" in session and session["is_logged_in"]and "is_admin" in session:
        
        quiz_ID_query = '''
            SELECT a.question, a.answer, a.user, a.comment, a.time_of_playthough, q.question, q.questionType, qt.type
            FROM `answer` a 
            INNER JOIN `question` q 
            ON q.question_ID = a.question
            INNER JOIN `questionType` as qt
            ON qt.questionType_ID = q.questionType
            WHERE q.quiz = %s AND a.user = %s AND a.time_of_playthough = %s
            ORDER BY a.question
        '''
        
        cursor.execute(quiz_ID_query, (quiz_ID, user, time))
        quiz_ID_playthrough = cursor.fetchall()
        conn.commit()
        
        if request.method == "POST":
            for i in range(len(quiz_ID_playthrough)):
                
                update_query = '''
                    UPDATE answer
                    SET comment = %s, status = %s
                    WHERE question = %s AND user = %s AND time_of_playthough = %s
                '''
                cursor.execute(update_query, (request.form[f"text_field-{i+1}"], int(request.form[f"radio_button-{i+1}"]), quiz_ID_playthrough[i][0], user, time))
                conn.commit()
            
            return redirect(url_for("quiz_grading", quiz_ID = quiz_ID))
        
        return render_template("grading_quiz_user.html", quiz_ID = quiz_ID, quiz_ID_playthrough = quiz_ID_playthrough, fetch_options = fetch_options)
        
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run()