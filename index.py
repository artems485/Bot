import telegram
from flask import Flask, request, Response

from bot import *

webhook = dispatcher.bot.get_webhook_info()
if webhook.url:
    dispatcher.bot.delete_webhook()

dispatcher.bot.set_webhook(url='https://bot-blue-alpha.vercel.app/' + TOKEN)

app = Flask(__name__)


@app.route('/')
def base():
    return 'Hi'


@app.route('/' + TOKEN, methods=['POST'])
def bot_webhook():
    update = telegram.update.Update.de_json(request.get_json(force=True), bot=dispatcher.bot)
    dispatcher.process_update(update)
    return Response('Ok', status=200)
