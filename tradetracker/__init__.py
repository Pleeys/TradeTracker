from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from os import path
from flask_login import LoginManager
from flask_mail import Mail
import os
import base64


app = Flask(__name__)
app.config['SECRET_KEY'] = base64.b64encode(os.urandom(16)).decode('utf-8')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'alert-error'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)

from tradetracker.users.routes import users
from tradetracker.posts.routes import posts
from tradetracker.main.routes import main

app.register_blueprint(users)
app.register_blueprint(posts)
app.register_blueprint(main)

def create_database():
    with app.app_context():
        if path.exists('instance/site.db'):
            return
        db.create_all()
        print('Created Database!')
            
create_database()