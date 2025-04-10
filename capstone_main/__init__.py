from flask import Flask
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager


#load variables from .env
load_dotenv()

#access .env variables
secret_key = os.getenv("SECRET_KEY")
database_uri = os.getenv("DATABASE_URI")

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page' #to deal with the @login_required decorator
login_manager.login_message_category = 'info'

from capstone_main import routes