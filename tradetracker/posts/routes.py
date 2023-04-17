from flask import (render_template, url_for, flash, redirect, request, abort, Blueprint)
from flask_login import current_user, login_required
from tradetracker import db
from tradetracker.models import Post
from tradetracker.posts.forms import PostForm, StockForm
from bs4 import BeautifulSoup 
import requests
import re
import pandas as pd
import csv
from tradetracker.config import Config
from datetime import datetime, timedelta
posts = Blueprint('posts', __name__)

@posts.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@posts.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@posts.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
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
        return redirect(url_for('posts.post',post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

@posts.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('main.home'))

def fetch_earnings():
    try:
        source = requests.get('https://www.earningswhispers.com/calendar')
        soup = BeautifulSoup(source.content, 'lxml')
    except:
        flash('We\'re sorry, an error occurred with the API. Please try again later!', 'error')
        return redirect(url_for('main.home'))

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

    return(earnings_list)

@posts.route('/earnings')
def earnings():
    earnings_list = fetch_earnings()
    df = pd.DataFrame(earnings_list[1:], columns=earnings_list[0])

    return render_template('earnings.html', earnings_list=earnings_list, df=df, title='Earnings')

@posts.route('/download_earnings')
def download_earnings():
    earnings_list = fetch_earnings()
    filename = 'earnings.csv'
    with open(filename, 'w') as f:
        writer = csv.writer(f, delimiter='|')
        writer.writerows(earnings_list)
        flash('The earnings data has been downloaded and saved as a CSV file!', 'success')
    return redirect(url_for('posts.earnings'))


@posts.route('/news')
def news():
    key = Config.AV_KEY

    today = datetime.now()
    month_ago = today - timedelta(days=30)
    month_ago_str = month_ago.strftime("%Y%m%dT%H%M")
    try:
        url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=COIN,CRYPTO:BTC,FOREX:USD&time_from={month_ago_str}&sort=LATEST&apikey={key}'
        r = requests.get(url)
        data = r.json()
        articles = pd.DataFrame(data['feed'])
        articles['time_published'] = pd.to_datetime(articles['time_published']).dt.strftime('%Y-%m-%d')

        return render_template('news.html', title='Stock News', data=data, articles=articles)
    except:
        flash('We\'re sorry, an error occurred with the API. Please try again later!', 'error')
        return redirect(url_for('main.home'))
    
@posts.route('/overview', methods=['GET', 'POST'])
def overview():

    key = Config.AV_KEY
    form = StockForm()

    if form.ticker.data:
        ticker = form.ticker.data
    else:
        ticker = 'MSFT'
    try:
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={key}'
        r = requests.get(url)
        data = r.json()
    except KeyError:
        flash('Ticker does not exists!', 'error')
        return redirect(url_for('main.home'))
    except:
        flash('We\'re sorry, an error occurred with the API. Please try again later!', 'error')
        return redirect(url_for('main.home'))
    if 'Description' in data:
        description = data['Description']
        del data['Description']
    else:
        flash('Ticker does not exists!', 'error')
        ticker = ''
        description = ''
    if form.validate_on_submit():
        ticker = form.ticker.data
        return redirect(url_for('posts.overview', ticker=ticker))

    return render_template('overview.html', title='Company Overview', data=data, form=form, description=description, ticker=ticker)
