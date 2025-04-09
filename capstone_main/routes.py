from flask import render_template, url_for, flash, redirect
from capstone_main import app
from capstone_main.models import User, Recipe
from capstone_main.forms import RegistrationForm, LoginForm
from capstone_main.private_variables import *

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