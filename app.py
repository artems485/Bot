import os

from flask import Flask
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from requests_oauthlib import OAuth2Session

GOOGLE_CLIENT_ID = '762970632572-2ait8506rq0f06vqs4d0vuf57gd8n8le.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'


class Auth:
    CLIENT_ID = GOOGLE_CLIENT_ID
    CLIENT_SECRET = GOOGLE_CLIENT_SECRET
    REDIRECT_URI = 'https://bot-blue-alpha.vercel.app/authorized'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email', 'https://www.googleapis.com/auth/gmail.readonly']


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
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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
    telegram_id = db.Column(db.Integer, unique=True, nullable=False)
    authenticated = db.Column(db.Boolean, default=True)
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
