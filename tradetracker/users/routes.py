from flask import render_template, url_for, flash, redirect, abort, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from tradetracker import db, bcrypt
from tradetracker.models import User, Post, Stock
from tradetracker.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                                   RequestResetForm, ResetPasswordForm, PortfolioForm)
from tradetracker.users.utils import save_picture, send_reset_email
import pandas as pd
from functools import reduce
import yfinance as yf
users = Blueprint('users', __name__)

@users.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.username.data is not None and len(form.username.data) < 4:
        flash('Username must have at least 5 characters', 'error')
    elif form.email.data is not None and ("@" not in form.email.data or "." not in form.email.data):
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
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)

@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'error')
    return render_template('login.html', title='Login', form=form)

@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

@users.route('/user/<string:username>')
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=3)
    return render_template('user_posts.html',posts=posts, user=user)

@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'error')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('UTF-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@users.route('/portfolio/<string:username>', methods=['GET','POST'])
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
        print(tickers)  
        print(amounts)
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
        return(redirect(url_for('users.portfolio', username=current_user.username)))
        
    ticker_to_value = {}
    for i in range(len(tickers)):     
        if tickers[i]  not in ticker_to_value:
                ticker_to_value[tickers[i]] = yf.Ticker(tickers[i])
        ticker_value = ticker_to_value[tickers[i]]
        stockinfo = ticker_value.fast_info
        last_price = round(stockinfo['lastPrice'],2)
        prices.append(last_price)
        amount = amounts[i]
        total_round = round(last_price*amount,2)
        total.append(total_round)


    porftolio_stocks=list(zip(tickers, amounts, prices, total, dates))
    ticker_labels = []
    ticker_amounts = []
    pieData = []
    ticker_id = []
    total_prices = []
    if stock is not None:
        df = pd.DataFrame(porftolio_stocks[0:], columns=porftolio_stocks[0])
        same_stocks = Stock.query.filter_by(user_id=user.id).all()

        for stock in same_stocks:       
            ticker_id.append(stock.id) 
            ticker_value = ticker_to_value[stock.ticker]
            stockinfo = ticker_value.fast_info
            last_price = round(stockinfo['lastPrice'],2)
            if stock.ticker in ticker_labels:
                index = ticker_labels.index(stock.ticker)
                ticker_amounts[index] += stock.amount
                total_prices[index] += round(stock.amount*last_price,2)
            else:
                ticker_labels.append(stock.ticker)
                ticker_amounts.append(stock.amount)
                total_prices.append(round(stock.amount*last_price,2))
                
                
        print(total_prices)
        overview = list(zip(ticker_labels, ticker_amounts, total_prices))
        df_overview = pd.DataFrame(overview[0:], columns=overview[0])

        summary = round(reduce(lambda acc, val: acc + val, total_prices),2)
                
    else: 
        overview = list(zip(ticker_labels, ticker_amounts, total_prices))
        df = pd.DataFrame(porftolio_stocks, columns=['Ticker', 'Amount', 'Price', 'Total', 'Date'])
        df_overview = pd.DataFrame(overview, columns=['Ticker', 'Amount', 'Total'])
        summary = 0

    return render_template('portfolio.html', summary=summary, df_overview=df_overview, pieData=pieData, df=df,
                            username=username, ticker_labels=ticker_labels, ticker_amounts=ticker_amounts, ticker_id=ticker_id, form=form, title='Portfolio')

@users.route("/portfolio/<int:ticker_id>/delete", methods=['POST'])
@login_required
def delete_stock(ticker_id):
    stock = Stock.query.get_or_404(ticker_id)
    if stock.user_id != current_user.id:
        abort(403)
    db.session.delete(stock)
    db.session.commit()
    flash('Your stock has been deleted!', 'success')
    return(redirect(url_for('users.portfolio', username=current_user.username)))

