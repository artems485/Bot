import logging
from enum import IntEnum

from simplegmail import Gmail
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

updater = Updater(use_context=True, token='5569549699:AAGRHqOgcprg2iqkkmlV1DzSUaUBbUCwdtM')
dispatcher = updater.dispatcher


class State(IntEnum):
    START = 0,
    SETTINGS = 1,
    UPDATE_SECRET = 2,
    UPDATE_TOKEN = 3


def start(update: Update, context: CallbackContext):
    kb = ReplyKeyboardMarkup([[KeyboardButton('Настройки')]], resize_keyboard=True)
    update.message.reply_text('Привет', reply_markup=kb)
    return State.START


def settings(update: Update, context: CallbackContext):
    kb = ReplyKeyboardMarkup([[KeyboardButton('Обновить email')], [KeyboardButton('Назад')]], resize_keyboard=True)
    update.message.reply_text('Выберите опцию из списка', reply_markup=kb)
    return State.SETTINGS


def update_email(update: Update, context: CallbackContext):
    kb = ReplyKeyboardMarkup([[KeyboardButton('Назад')]], resize_keyboard=True)
    update.message.reply_text('Скиньте файл client_secret.json', reply_markup=kb)
    return State.UPDATE_SECRET


def secret_file_name(chat_id):
    return f'secrets/{chat_id}.json'


def update_secret(update: Update, context: CallbackContext):
    context.bot.get_file(update.message.document).download()
    file_name = secret_file_name(update.effective_chat.id)
    with open(file_name, 'wb') as f:
        gmail = Gmail(file_name)
        context.bot.get_file(update.message.document).download(out=f)
        kb = ReplyKeyboardMarkup([[KeyboardButton('Назад')]], resize_keyboard=True)
        update.message.reply_text('Скиньте файл gmail_token.json', reply_markup=kb)
        return State.UPDATE_TOKEN


def back_to_main_menu(update: Update, context: CallbackContext):
    kb = ReplyKeyboardMarkup([[KeyboardButton('Настройки')]], resize_keyboard=True)
    update.message.reply_text('Привет', reply_markup=kb)
    return State.START


conversation = ConversationHandler(name='main',
                                   entry_points=[CommandHandler(command='start', callback=start)],
                                   states={State.START: [MessageHandler(Filters.text('Настройки'), settings)],
                                           State.SETTINGS: [
                                               MessageHandler(Filters.text('Обновить email'), update_email),
                                               MessageHandler(Filters.text('Назад'), back_to_main_menu)],
                                           State.UPDATE_SECRET: [
                                               MessageHandler(Filters.text('Назад'), settings),
                                               MessageHandler(Filters.document, update_secret)],
                                           State.UPDATE_TOKEN: [MessageHandler(Filters.text('Назад'), settings)]},
                                   fallbacks=[CommandHandler(command='start', callback=start)])
dispatcher.add_handler(conversation)
updater.start_polling()
updater.idle()
