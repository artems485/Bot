import json
import time

import telegram
from dotenv import load_dotenv
from flask import request, Response, session, url_for, redirect, render_template
from flask_login import login_required, login_user, \
    logout_user, current_user
from requests.exceptions import HTTPError

load_dotenv()

from app import *
from bot import *

webhook = dispatcher.bot.get_webhook_info()
time.sleep(1.5)
if webhook.url:
    dispatcher.bot.delete_webhook()
time.sleep(1.5)
dispatcher.bot.set_webhook(url='https://bot-blue-alpha.vercel.app/' + TOKEN)


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/policy')
def policy():
    return render_template('policy.html')


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/login')
def login():
    try:
        telegram_id = int(request.form['telegram_id'])
    except Exception:
        return redirect(url_for('index'))

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        Auth.AUTH_URI, access_type='offline')
    session['oauth_state'] = state
    session['telegram_id'] = telegram_id
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
        telegram_id = session['telegram_id']
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
            try:
                user = User.query.filter_by(email=email).first()

                if user is None:
                    user = User()
                    user.email = email
                user.telegram_id = telegram_id
                user.name = user_data['name']
                print(token)
                user.tokens = json.dumps(token)
                db.session.add(user)
                db.session.commit()
                login_user(user)
            except Exception as e:
                logger.error(e)
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
