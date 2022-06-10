import telegram
from flask import Flask, request

from bot import *
from logtail import LogtailHandler

handler = LogtailHandler(source_token='DctS4Y1nxhXKroiLgaDKLcgi')
logger.handlers = []
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.info('Logtail is ready!!!')

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
