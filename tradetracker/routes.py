import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from tradetracker import app, db, bcrypt
from tradetracker.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, PortfolioForm
from tradetracker.models import User, Post, Stock
from flask_login import login_user, current_user, logout_user, login_required
from bs4 import BeautifulSoup 
import requests
import re
import csv
import pandas as pd
from datetime import datetime
from yahooquery import Ticker
import yfinance as yf
import pandas_datareader as web
import matplotlib.pyplot as plt
import random
import seaborn as sns
import itertools


@app.route('/')
@app.route('/home')
def home():
        page = request.args.get('page', 1, type=int)
        posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)
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

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data 
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post',post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route('/user/<string:username>')
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=3)
    return render_template('user_posts.html',posts=posts, user=user)

@app.route('/earnings')
def earnings():
    source = requests.get('https://www.earningswhispers.com/calendar')
    soup = BeautifulSoup(source.content, 'lxml')

    espcalendar = soup.find('ul', id='epscalendar')

    companies_html = soup.findAll('div', class_='company')
    tickers_html = soup.findAll('div', class_='ticker')
    times_html = soup.findAll('div', class_='time')
    revenue_growths_html = soup.findAll('div', class_='revgrowthprint')
    earnings_growths_html = soup.findAll('div', class_='growth')

    companies = ['Company name']
    tickers = ['Ticker']
    times = ['Time']
    revenue_growths = ['Expected Revenue Growth']
    earnings_growths = ['Expected Earnings Growth']

    for company in companies_html:
        companies.append(company.text)

    for ticker in tickers_html:
        tickers.append(ticker.text)

    for time in times_html:
        times.append(time.text)

    for revenue_growth in revenue_growths_html:
        revenue_growths.append(revenue_growth.text)

    for earning in earnings_growths_html:
        earning_script = earning.find('script', string=lambda text: text and 'showepsgrowth' in text)
        if earning_script:
            earning_text = re.search(r'showepsgrowth\("[^"]*",\s*"([^"]*)"\);', earning_script.string)
            if earning_text:
                earnings_growths.append(earning_text.group(1))

    earnings_list = list(zip(companies, tickers, times, revenue_growths, earnings_growths))

    df = pd.DataFrame(earnings_list[1:], columns=earnings_list[0])

    
    return render_template('earnings.html', earnings_list=earnings_list, df=df, title='Earnings')

@app.route('/download_earnings')
def download_earnings():
    earnings_list = earnings()
    filename = 'earnings.csv'
    with open(filename, 'w') as f:
        writer = csv.writer(f, delimiter='|')
        writer.writerows(earnings_list)
        flash('The earnings data has been downloaded and saved as a CSV file!', 'success')
    return redirect(url_for('earnings'))

def generate_random_colors(num_colors):
    colors = []
    for i in range(num_colors):
        color = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
        colors.append('rgba({}, {}, {}, 0.2)'.format(*color))
        colors.append('rgba({}, {}, {}, 1)'.format(*color))
    return colors

@app.route('/portfolio/<string:username>', methods=['GET','POST'])
@login_required
def portfolio(username):
    if username != current_user.username:
        abort(403)
    user = User.query.filter_by(username=username).first()
    stock = Stock.query.filter_by(user_id=user.id).first()
    if stock is not None:
        stocks = Stock.query.filter_by(user_id=user.id).all()
        tickers = [stock.ticker for stock in stocks]
        amounts = [stock.amount for stock in stocks]
        dates = [stock.date_posted.strftime('%Y-%m-%d') for stock in stocks]
        prices = []
        total = []   
    else:
        tickers = []
        amounts = []
        prices = []
        total = []
        dates = []
    form = PortfolioForm()
    if form.validate_on_submit():      
        add_stock = Stock(ticker=form.ticker.data, amount=form.amount.data, user_id=user.id)
        dates.append(add_stock.date_posted)
        db.session.add(add_stock)
        db.session.commit()
        flash('The stock has been added!', 'success')
        return(redirect(url_for('portfolio', username=current_user.username)))
        
    
    for ticker in tickers:
        ticker_value = yf.Ticker(ticker)
        stockinfo = ticker_value.fast_info
        last_price = round(stockinfo['lastPrice'],2)
        prices.append(last_price)
        index = tickers.index(ticker)
        total_round = round(last_price*amounts[index],2)
        total.append(total_round)

    porftolio_stocks=list(zip(tickers, amounts, prices, total, dates))
    
    ticker_labels = []
    ticker_amounts = []
    colors = []
    pieData = []
    if stock is not None:
        df = pd.DataFrame(porftolio_stocks[0:], columns=porftolio_stocks[0])
        same_stocks = Stock.query.filter_by(user_id=user.id).all()
        for stock in same_stocks:        
            if stock.ticker in ticker_labels:
                index = ticker_labels.index(stock.ticker)
                ticker_amounts[index] += stock.amount
            else:
                ticker_labels.append(stock.ticker)
                ticker_amounts.append(stock.amount)

                
    else: 
        df = []
        
    colors = sns.color_palette("pastel",len(ticker_labels)).as_hex()
    for i in range(len(ticker_labels)):
        pieData.append({'value': stock.amount, 'color': colors[i]})
    print(ticker_labels)
    print(ticker_amounts)
    print(colors)
    return render_template('portfolio.html',colors=colors, pieData=pieData, df=df, username=username, dates=dates, tickers=tickers, ticker_labels=ticker_labels, ticker_amounts=ticker_amounts, amounts=amounts, total=total, prices=prices, form=form, title='Portfolio')

