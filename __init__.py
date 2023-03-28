from flask import Flask, render_template, request, url_for
import mysql.connector
from db_loggin import dbconfig

conn = mysql.connector.connect(**dbconfig)
cursor = conn.cursor()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()