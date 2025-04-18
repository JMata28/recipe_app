from datetime import datetime, timezone
from capstone_main import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader #decorator necessary to deal with logins
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default_profile_pic.jpg')
    password = db.Column(db.String(60), nullable=False)
    recipes = db.relationship('Recipe', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}, '{self.image_file}')"


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dish_name = db.Column(db.String(150), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc)) #corrected for the deprecation of datetime.utcnow
    ingredients = db.Column(db.Text, nullable =  False)
    recipe = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Recipe('{self.dish_name}', '{self.date_posted}')"

