from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=10)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(max=150)], render_kw={"class": "content"})
    submit = SubmitField('Post')

class StockForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired(), Length(min=1, max=4)])
    submit = SubmitField('Search')

