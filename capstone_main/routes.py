import os
import secrets
import requests
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from capstone_main import app, db, bcrypt, client
from capstone_main.models import User, Recipe, Rating
from capstone_main.forms import RegistrationForm, LoginForm, UpdateAccountForm, RecipeForm
from flask_login import login_user, current_user, logout_user, login_required
from pydantic import BaseModel


@app.route("/")
@app.route("/home")
def home_page():
    page = request.args.get('page', 1, type=int)
    recipes = Recipe.query.order_by(Recipe.date_posted.asc()).paginate(page=page, per_page=8)
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
        return redirect(url_for('account_page')) #causes the browser to send a GET request to avoid the POST GET REDIRECT PATTERN
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
        new_dish = Recipe(dish_name=form.recipe_name.data.lower(), description=form.description.data, dish_type = form.dish_type.data, time_needed=form.time_needed.data, serves=form.serves.data, ingredients=form.ingredients.data, recipe=form.instructions.data, image_file=dish_picture_file, author=current_user)
        db.session.add(new_dish)
        db.session.commit()
        flash('Your new recipe has been posted!', 'success')
        return redirect(url_for('home_page'))
    return render_template('create_recipe.html', title='New Recipe',
                           form=form, legend='New Recipe')

#Format for quering the Google Gemini in JSON format was obtained from Google Gemini Documentation: https://ai.google.dev/gemini-api/docs/structured-output?lang=python
class Similar_recipes(BaseModel):
  brief_description_of_dish: str
  dish_type: str 
  time_needed: str
  serves: int
  ingredients: str
  instructions: str

class Similar_recipe_names(BaseModel):
    dish_name: str

@app.route("/recipe/<int:recipe_id>", methods=['GET', 'POST'])
def recipe_page(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    if current_user.is_authenticated:
        prompt = "Give me two names of dishes similar to:" + recipe.dish_name
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt, config={
        'response_mime_type': 'application/json',
        'response_schema': list[Similar_recipe_names],})
        similar_recipe_name_list: list[Similar_recipe_names] = response.parsed

        saved_status='unsaved'
        for saved_recipe in current_user.saved_recipes:
            if saved_recipe.id == recipe_id:
                saved_status='saved'
        
        rated_status ='unrated'
        for rated_recipe in current_user.ratings:
            if rated_recipe.recipe_id == recipe_id:
                rated_status = 'rated'
        
        avg_rating = db.session.query(db.func.avg(Rating.rating)).filter_by(recipe_id=recipe.id).scalar() #Note
        rating_count = db.session.query(db.func.count(Rating.id)).filter_by(recipe_id=recipe.id).scalar()

        return render_template('recipe.html', title=recipe.dish_name, post=recipe, saved_status = saved_status, rated_status = rated_status, avg_rating = avg_rating, rating_count = rating_count, similar_recipe_name_list = similar_recipe_name_list)
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
        recipe.dish_name = form.recipe_name.data.lower()
        recipe.description=form.description.data
        recipe.dish_type = form.dish_type.data
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
        form.recipe_name.data = recipe.dish_name.title()
        form.description.data = recipe.description
        form.dish_type.data = recipe.dish_type
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

@app.route("/recipe/ai_recipe/<string:dish_name>", methods=['GET', 'POST'])
@login_required
def ai_recipe(dish_name):
    prompt = "Generate one recipe for " + dish_name + ". Make sure that the recipe is safe to consume and relatively brief."
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt, config={
        'response_mime_type': 'application/json',
        'response_schema': Similar_recipes,
    })
    similar_recipe: Similar_recipes = response.parsed
    form = RecipeForm()
    if form.validate_on_submit():
        if form.dish_picture.data: 
            dish_picture_file = save_picture(form.dish_picture.data, True)
        else:
            dish_picture_file = 'default_recipe_pic.png' 
        new_dish = Recipe(dish_name=form.recipe_name.data.lower(), description=form.description.data, dish_type = form.dish_type.data, time_needed=form.time_needed.data, serves=form.serves.data, ingredients=form.ingredients.data, recipe=form.instructions.data, image_file=dish_picture_file, author=current_user)
        db.session.add(new_dish)
        db.session.commit()
        flash('Your new recipe has been posted!', 'success')
        return redirect(url_for('user_recipes', username=current_user.username) )
    elif request.method == 'GET':
        form.recipe_name.data = dish_name.title()
        form.description.data = similar_recipe.brief_description_of_dish
        form.dish_type.data = similar_recipe.dish_type
        form.time_needed.data = similar_recipe.time_needed
        form.serves.data =  similar_recipe.serves
        form.ingredients.data = similar_recipe.ingredients
        form.instructions.data= similar_recipe.instructions
    return render_template('create_recipe.html', title='AI Recipe',
                           form=form, legend='New AI-Generated Recipe')

@app.route("/search", methods=['GET', 'POST'])
def search_recipe():
    dish_name = request.form.get('dish_name') #to get the data from the search bar form item in the html
    page = request.args.get('page', 1, type=int)
    recipes_found = Recipe.query.filter_by(dish_name=dish_name.lower()).order_by(Recipe.date_posted.asc()).paginate(page=page, per_page=5)
    return render_template('display_recipes.html', title='Recipe Search Results', posts=recipes_found, user=current_user, recipe_type='search_recipes', dish_name_entered=dish_name)

@app.route("/rate_recipe/<int:recipe_id>", methods=['POST'])
@login_required
def rate_recipe(recipe_id):
    number_of_stars = request.form.get('rating')
    #recipe= Recipe.query.get_or_404(recipe_id)
    new_rating = Rating(user_id=current_user.id, recipe_id=recipe_id, rating=number_of_stars)
    db.session.add(new_rating)
    db.session.commit()
    flash('Rating submited!', 'success')
    #print("New rating of: " + str(new_rating.rating) + " stars by user " + str(new_rating.user.username) + "for " + str(new_rating.recipe.dish_name.title()))

    return redirect(request.referrer or url_for('home_page'))   #The request.referrer method was a good ChatGPT suggestion