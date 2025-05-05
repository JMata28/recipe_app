from datetime import datetime, timezone
from capstone_main import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader #decorator necessary to deal with logins
def load_user(user_id):
    return User.query.get(int(user_id))

#user_recipe table made to implement many-to-many relationship for users save recipes
user_recipe = db.Table('user_recipe', 
                       db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                       db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'))
                       )

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default_profile_pic.png')
    password = db.Column(db.String(60), nullable=False)
    recipes = db.relationship('Recipe', backref='author', lazy='select') #older versions of SQLAlchhemy used lazy=True instead of lazy='select'
    saved_recipes = db.relationship('Recipe', secondary=user_recipe, backref='users_who_saved')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}, '{self.image_file}')"


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dish_name = db.Column(db.String(150), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc)) #corrected for the deprecation of datetime.utcnow
    description = db.Column(db.Text, nullable=False)
    dish_type = db.Column(db.String(50), default='Other')
    time_needed = db.Column(db.String(100), nullable=False)
    serves = db.Column(db.Integer, nullable= False)
    ingredients = db.Column(db.Text, nullable =  False)
    recipe = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default_recipe_pic.png')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Recipe('{self.dish_name}', '{self.date_posted}')"

