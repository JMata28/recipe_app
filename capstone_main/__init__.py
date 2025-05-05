from flask import Flask
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from google import genai

#load variables from .env
load_dotenv()

#access .env variables
secret_key = os.getenv("SECRET_KEY")
database_uri = os.getenv("DATABASE_URI")
gemini_api_key = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page' #to deal with the @login_required decorator
login_manager.login_message_category = 'info'
client = genai.Client(api_key=gemini_api_key)

from capstone_main import routes

'''
    The database should be created separately, since it is not done automatically by the application, to ensure that all the data is structured with the lates db models. Commands to create database: 

    in the terminal, run $python3 

    from capstone_main import app, db
    with app.app_context():
        db.create_all()

'''