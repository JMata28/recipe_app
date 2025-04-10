from flask import render_template, url_for, flash, redirect, request
from capstone_main import app, db, bcrypt
from capstone_main.models import User, Recipe
from capstone_main.forms import RegistrationForm, LoginForm
from capstone_main.private_variables import *
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
@app.route("/home")
def home_page():
    return render_template("home.html", title="Home Page", posts=posts)

@app.route("/about")
def about_page():
    return render_template("about.html")

@app.route("/register", methods = ['GET', 'POST'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password =  bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! You can now log in.', 'success')
        return redirect(url_for('home_page'))
    return render_template("register.html", title="Register", form=form)

@app.route("/login", methods = ['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home_page'))
        else:
            flash('Login unsuccesful. Please check email and password', 'danger')
    return render_template("login.html", title="Login", form=form)

@app.route("/logout")
def logout_page():
    logout_user()
    return redirect(url_for('home_page'))

@app.route("/account")
@login_required
def account_page():
    return render_template('account.html', title="Account")
