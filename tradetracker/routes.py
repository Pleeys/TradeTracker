import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from tradetracker import app, db, bcrypt
from tradetracker.forms import RegistrationForm, LoginForm, UpdateAccountForm
from tradetracker.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required


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
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.username.data is not None and len(form.username.data) < 4:
        flash('Username must have at least 5 characters', 'error')
    elif form.email.data is not None and ("@" not in form.email.data or "." not in form.email.data or form.email.data.index(".") < form.email.data.index("@")):
        flash('Invalid email address', 'error')
    elif form.password.data is not None and len(form.password.data) < 7:
        flash('Password must have at least 8 characters', 'error')
    elif not(form.password.data == form.confirm_password.data):
        flash('The passwords do not match', 'error')
    elif form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('UTF-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'error')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125,125)
    i = Image.open(form_picture)
    i = i.convert('RGB')
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file  = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@app.rout("/post/new")
@login_required
def new_post():
    return render_template('create_post.html', title='New Post')