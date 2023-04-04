from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user 
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from tradetracker.models import User
from flask import flash
import yfinance as yf 


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                            validators=[DataRequired(), Length(min=2, max=20),])
    email = StringField('Email',
                            validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                            validators=[DataRequired()])
    confirm_password = PasswordField('Confirm_Password',
                            validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()     
        if user:
            flash('Username already exists', 'error')
            raise ValidationError()
        
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()   
        if user:
            flash('Email already exists', 'error')
            raise ValidationError()
        
class LoginForm(FlaskForm):
    email = StringField('Email',
                            validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                            validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                            validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                            validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()     
            if user:
                flash('Username already exists', 'error')
                raise ValidationError()
        
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()   
            if user:
                flash('Email already exists', 'error')
                raise ValidationError()
            
class PortfolioForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired(), Length(min=3, max=4)])
    amount = IntegerField('Amount', validators=[DataRequired(), NumberRange(min=0, message="Value must be non-negative")])
    submit = SubmitField('Add')

    def validate_ticker(form, ticker):
        try:
            is_ticker = yf.Ticker(ticker.data)
            is_ticker.info
        except: 
             flash('Invalid stock name!', 'error')
             raise ValidationError()

class RequestResetForm(FlaskForm):
    email = StringField('Email',
                            validators=[DataRequired(), Email()])
    submit = SubmitField('Reset')
    

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()   
        if user is None:
            flash('There is no account with that email. You must register first!', 'error')
            raise ValidationError()

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', 
                            validators=[DataRequired()])
    confirm_password = PasswordField('Confirm_Password',
                            validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')          