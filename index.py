import json

import telegram
from dotenv import load_dotenv
from flask import Flask, request, Response, session, url_for, redirect, render_template
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from requests.exceptions import HTTPError
from requests_oauthlib import OAuth2Session

load_dotenv()
import os

from bot import *

webhook = dispatcher.bot.get_webhook_info()
if webhook.url:
    dispatcher.bot.delete_webhook()

dispatcher.bot.set_webhook(url='https://bot-blue-alpha.vercel.app/' + TOKEN)

GOOGLE_CLIENT_ID = '655553482219-ho3edlipgsh8io3fjguui3ume3u2cose.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'


class Auth:
    CLIENT_ID = GOOGLE_CLIENT_ID
    CLIENT_SECRET = GOOGLE_CLIENT_SECRET
    REDIRECT_URI = 'https://bot-blue-alpha.vercel.app/authorized'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']


SECRET_KEY = os.environ.get("SECRET_KEY") or 'asdjaslkdj32kl3j2klj32ljkl2'


class Config:
    """Base config"""
    APP_NAME = "Test Google Login"
    SECRET_KEY = SECRET_KEY


class DevConfig(Config):
    """Dev config"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{os.getenv("PLANETSCALE_DB_USERNAME")}' \
                              f':{os.getenv("PLANETSCALE_DB_PASSWORD")}' \
                              f'@{os.getenv("PLANETSCALE_DB_HOST")}' \
                              f'/{os.getenv("PLANETSCALE_DB")}'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            # 'ssl_mode': 'VERIFY_IDENTITY',
            # https://stackoverflow.com/questions/60285240/is-there-a-way-to-emulate-ssl-mode-preferred-in-pymysql
            'ssl': {'ca': os.getenv('PLANETSCALE_SSL_CERT_PATH')}
        }
    }


class ProdConfig(Config):
    """Production config"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{os.getenv("USERNAME")}:{os.getenv("PASSWORD")}@{os.getenv("HOST")}/{os.getenv("DATABASE")}'


config = {
    'dev': DevConfig,
    'prod': ProdConfig,
    'default': DevConfig
}

app = Flask(__name__)
app.config.from_object(config['dev'])
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    tokens = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Auth.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            Auth.CLIENT_ID,
            state=state,
            redirect_uri=Auth.REDIRECT_URI)
    oauth = OAuth2Session(
        Auth.CLIENT_ID,
        redirect_uri=Auth.REDIRECT_URI,
        scope=Auth.SCOPE)
    return oauth


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/policy')
def policy():
    return render_template('policy.html')


@app.route('/terms')
def policy():
    return render_template('terms.html')

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        Auth.AUTH_URI, access_type='offline')
    session['oauth_state'] = state
    return render_template('login.html', auth_url=auth_url)


@app.route('/authorized')
def callback():
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('index'))
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        google = get_google_auth(state=session['oauth_state'])
        try:
            token = google.fetch_token(
                Auth.TOKEN_URI,
                client_secret=Auth.CLIENT_SECRET,
                authorization_response=request.url)
        except HTTPError:
            return 'HTTPError occurred.'
        google = get_google_auth(token=token)
        resp = google.get(Auth.USER_INFO)
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            user = User.query.filter_by(email=email).first()
            if user is None:
                user = User()
                user.email = email
            user.name = user_data['name']
            print(token)
            user.tokens = json.dumps(token)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
        return 'Could not fetch your information.'


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/' + TOKEN, methods=['POST'])
def bot_webhook():
    update = telegram.update.Update.de_json(request.get_json(force=True), bot=dispatcher.bot)
    dispatcher.process_update(update)
    return Response('Ok', status=200)
