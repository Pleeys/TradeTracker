from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from os import path
from flask_login import LoginManager
from flask_mail import Mail
from tradetracker.config import Config


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'alert-error'

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