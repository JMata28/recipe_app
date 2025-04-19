import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from capstone_main import app, db, bcrypt
from capstone_main.models import User, Recipe
from capstone_main.forms import RegistrationForm, LoginForm, UpdateAccountForm, RecipeForm
from capstone_main.private_variables import *
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
@app.route("/home")
def home_page():
    recipes = Recipe.query.all()
    return render_template("home.html", title="Home Page", posts=recipes)

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

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static', picture_fn)

    output_size = (125, 125) 
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods = ['GET', 'POST'])
@login_required
def account_page():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data: 
            picture_file = save_picture(form.picture.data)
            current_user.image_file =  picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account_page')) #causes the browser to send a GET request to avoide the POST GET REDIRECT PATTERN
    elif request.method == 'GET':
        form.username.data = current_user.username #pre-fills out the username in the form
        form.email.data = current_user.email #pre-fills out the email in the form
    image_file =  url_for('static', filename=current_user.image_file)
    return render_template('account.html', title="Account", image_file=image_file, form=form)

@app.route("/recipe/new", methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        new_dish = Recipe(dish_name=form.recipe_name.data, recipe=form.recipe.data, author=current_user)
        db.session.add(new_dish)
        db.session.commit()
        flash('Your new recipe has been posted!', 'success')
        return redirect(url_for('home_page'))
    return render_template('create_recipe.html', title='New Recipe',
                           form=form, legend='New Recipe')


@app.route("/recipe/<int:recipe_id>")
def recipe_page(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('recipe.html', title=recipe.dish_name, post=recipe)


@app.route("/recipe/<int:recipe_id>/update", methods=['GET', 'POST'])
@login_required
def update_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)
    form = RecipeForm()
    if form.validate_on_submit():
        recipe.dish_name = form.recipe_name.data
        recipe.recipe = form.recipe.data
        db.session.commit()
        flash('Your recipe has been updated!', 'success')
        return redirect(url_for('recipe_page', recipe_id=recipe.id))
    elif request.method == 'GET':
        form.recipe_name.data = recipe.dish_name
        form.recipe.data = recipe.recipe
    return render_template('create_recipe.html', title='Update Recipe',
                           form=form, legend='Update Recipe')


@app.route("/recipe/<int:recipe_id>/delete", methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)
    db.session.delete(recipe)
    db.session.commit()
    flash('Your recipe has been deleted!', 'success')
    return redirect(url_for('home_page'))
