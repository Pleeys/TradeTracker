from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, LoginForm


app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'

db = SQLAlchemy(app)
DB_NAME = "database.db"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{DB_NAME}'






posts = [
    {
    'author': 'Corey Schafter',
    'title': 'Blog Post 1',
    'content': 'First post content',
    'date_posted': 'April 20, 2018'
    },
    {
    'author': 'Jane Doe',
    'title': 'Blog Post 2',
    'content': 'Second post content',
    'date_posted': 'April 21, 2018'
    }
]
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html',posts=posts)

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        if not(email and '@' in email and '.' in email.split('@')[1]):
            flash('Invalid email address. Please enter a valid email address.', category='error')       
        elif not(username and len(username)>= 3):
            flash('Username must be at least 3 characters long. Please choose a longer username.', category='error')
        elif not(password1 and password2 and password1 == password2 and len(password1) >= 8):
            flash('Passwords do not match or are too short. Please enter matching passwords that are at least 8 characters long.', category='error')
        else:
            flash('Account created!', 'success')
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin@blog.com' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


if __name__ == '__main__':
    app.run(debug=True)