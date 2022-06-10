from enum import IntEnum
import logging

from app import User
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackContext, \
    Dispatcher

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = '5569549699:AAGRHqOgcprg2iqkkmlV1DzSUaUBbUCwdtM'
updater = Updater(use_context=True, token=TOKEN)
dispatcher: Dispatcher = updater.dispatcher


class State(IntEnum):
    START = 0,
    SETTINGS = 1,
    AUTHORIZATION = 2,


def start(update: Update, context: CallbackContext):
    kb = ReplyKeyboardMarkup([[KeyboardButton('Настройки')]], resize_keyboard=True)
    update.message.reply_text('Привет', reply_markup=kb)
    return State.START


def settings(update: Update, context: CallbackContext):
    context.chat_data['authorization'] = False
    kb = ReplyKeyboardMarkup([[KeyboardButton('Обновить email')], [KeyboardButton('Назад')]], resize_keyboard=True)
    if 'authorized' not in context.chat_data or not context.chat_data['authorized']:
        update.message.reply_text('Вы не авторизированы!\nВыберите опцию из списка', reply_markup=kb)
    else:
        user = User.query.filter_by(telegram_id=update.effective_chat.id).first()
        update.message.reply_text(f'Текущий email: {user.email}!\nВыберите опцию из списка', reply_markup=kb)
    return State.SETTINGS


def update_email(update: Update, context: CallbackContext):
    kb = ReplyKeyboardMarkup([[KeyboardButton('Я авторизировался')], [KeyboardButton('Назад')]], resize_keyboard=True)
    update.message.reply_text(
        f'Авторизируйтесь: https://bot-blue-alpha.vercel.app/login?telegram_id={update.effective_chat.id}',
        reply_markup=kb)
    context.chat_data['authorization'] = True
    return State.AUTHORIZATION


def i_authorized(update: Update, context: CallbackContext):
    user = User.query.filter_by(telegram_id=update.effective_chat.id).first()
    if user is None:
        kb = ReplyKeyboardMarkup([[KeyboardButton('Я авторизировался')], [KeyboardButton('Назад')]],
                                 resize_keyboard=True)
        update.message.reply_text(
            f'Попробуйте снова: https://bot-blue-alpha.vercel.app/login?telegram_id={update.effective_chat.id}',
            reply_markup=kb)
        return State.AUTHORIZATION
    context.chat_data['authorized'] = True
    return settings(update, context)


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
                                           State.AUTHORIZATION: [
                                               MessageHandler(Filters.text('Назад'), settings),
                                               MessageHandler(Filters.text('Я авторизировался'), i_authorized)
                                           ]},
                                   fallbacks=[CommandHandler(command='start', callback=start)], per_chat=True)
dispatcher.add_handler(conversation)
