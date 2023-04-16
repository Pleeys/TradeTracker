from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from os import path
from flask_login import LoginManager
from flask_mail import Mail
from tradetracker.config import Config



db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'alert-error'

mail = Mail()





def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from tradetracker.users.routes import users
    from tradetracker.posts.routes import posts
    from tradetracker.main.routes import main
    from tradetracker.errors.handlers import errors
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(main)
    app.register_blueprint(errors)
    
    def create_database():
        with app.app_context():
            if path.exists('instance/site.db'):
                return
            db.create_all()
            print('Created Database!')
            
    create_database()
    
    return app