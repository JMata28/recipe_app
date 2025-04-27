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
    page = request.args.get('page', 1, type=int)
    recipes = Recipe.query.order_by(Recipe.date_posted.asc()).paginate(page=page, per_page=5)
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
        flash(f'Account created for {form.username.data}!', 'success')
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

def save_picture(form_picture, is_recipe_pic):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    if is_recipe_pic == True:
        picture_path = os.path.join(app.root_path, 'static/recipe_pictures', picture_fn)
    else:
        picture_path = os.path.join(app.root_path, 'static/profile_pictures', picture_fn)
    
    output_size = (500, 500) 
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
            picture_file = save_picture(form.picture.data, False)
            current_user.image_file =  picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account_page')) #causes the browser to send a GET request to avoide the POST GET REDIRECT PATTERN
    elif request.method == 'GET':
        form.username.data = current_user.username #pre-fills out the username in the form
        form.email.data = current_user.email #pre-fills out the email in the form
    image_file =  url_for('static', filename='profile_pictures/' + current_user.image_file)
    return render_template('account.html', title="Account", image_file=image_file, form=form)

@app.route("/recipe/new", methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        if form.dish_picture.data: 
            dish_picture_file = save_picture(form.dish_picture.data, True)
        else:
            dish_picture_file = 'default_recipe_pic.png' 
        new_dish = Recipe(dish_name=form.recipe_name.data, time_needed=form.time_needed.data, serves=form.serves.data, ingredients=form.ingredients.data, recipe=form.instructions.data, image_file=dish_picture_file, author=current_user)
        db.session.add(new_dish)
        db.session.commit()
        flash('Your new recipe has been posted!', 'success')
        return redirect(url_for('home_page'))
    return render_template('create_recipe.html', title='New Recipe',
                           form=form, legend='New Recipe')


@app.route("/recipe/<int:recipe_id>")
def recipe_page(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if current_user.is_authenticated:
        saved_status='unsaved'
        for saved_recipe in current_user.saved_recipes:
            if saved_recipe.id == recipe_id:
                saved_status='saved'
        return render_template('recipe.html', title=recipe.dish_name, post=recipe, saved_status = saved_status)
    else: 
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
        recipe.time_needed = form.time_needed.data
        recipe.serves = form.serves.data
        recipe.ingredients = form.ingredients.data
        recipe.recipe = form.instructions.data
        if form.dish_picture.data: 
            dish_picture_file = save_picture(form.dish_picture.data, True)
            recipe.image_file = dish_picture_file
        db.session.commit()
        flash('Your recipe has been updated!', 'success')
        return redirect(url_for('recipe_page', recipe_id=recipe.id))
    elif request.method == 'GET':
        form.recipe_name.data = recipe.dish_name
        form.time_needed.data = recipe.time_needed
        form.serves.data =  recipe.serves
        form.ingredients.data = recipe.ingredients
        form.instructions.data=recipe.recipe
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

@app.route("/user/<string:username>")
def user_recipes(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    recipes = Recipe.query.filter_by(author=user)\
        .order_by(Recipe.date_posted.asc())\
        .paginate(page=page, per_page=5)
    return render_template('display_recipes.html', posts=recipes, user=user, recipe_type = 'user_recipes')

@app.route("/user/saved_recipes")
def saved_recipes():
    page = request.args.get('page', 1, type=int)
    recipes = Recipe.query.filter(Recipe.users_who_saved.contains(current_user)).order_by(Recipe.date_posted.asc()).paginate(page=page, per_page=5) #the implementation of the .filter and the .contains methods was explained by ChatGPT
    return render_template('display_recipes.html', posts=recipes, user=current_user, recipe_type = 'saved_recipes')

@app.route("/save_recipe/<int:recipe_id>", methods=['POST'])
@login_required
def save_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe in current_user.saved_recipes:
        flash('You have already saved this recipe.', 'info')
    else: 
        current_user.saved_recipes.append(recipe)
        db.session.commit()
        flash('Recipe added to your saved recipes!', 'success')
    return redirect(request.referrer or url_for('saved_recipes'))   #The request.referrer method was a good ChatGPT suggestion

@app.route("/unsave_recipe/<int:recipe_id>", methods=['POST'])
@login_required
def unsave_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe in current_user.saved_recipes:
        current_user.saved_recipes.remove(recipe)
        db.session.commit()
        flash('Recipe removed from your saved recipes!', 'success')
    else:
        flash('This recipe is already not in your saved recipes.', 'info')
    return redirect(request.referrer or url_for('saved_recipes')) #The request.referrer method was a good ChatGPT suggestion

