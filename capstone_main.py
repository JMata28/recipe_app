from flask import Flask, render_template, url_for, flash, redirect
from private_variables import *
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, LoginForm

#load variables from .env
load_dotenv()

#access .env variables
secret_key = os.getenv("SECRET_KEY")
database_uri = os.getenv("DATABASE_URI")

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)

@app.route("/")
@app.route("/home")
def home_page():
    return render_template("home.html", title="Home Page", posts=posts)

@app.route("/about")
def about_page():
    return render_template("about.html")

@app.route("/register", methods = ['GET', 'POST'])
def register_page():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home_page'))
    return render_template("register.html", title="Register", form=form)

@app.route("/login", methods = ['GET', 'POST'])
def login_page():
    form = LoginForm()
    return render_template("login.html", title="Login", form=form)

if __name__ == '__main__':
    app.run(debug=True)