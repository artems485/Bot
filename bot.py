from enum import IntEnum
import logging
import json

import mail
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
    EXIT = 3


def start(update: Update, context: CallbackContext):
    user = User.query.filter_by(telegram_id=update.effective_chat.id).first()
    if not user or not user.authenticated:
        kb = ReplyKeyboardMarkup([[KeyboardButton('Настройки')]], resize_keyboard=True)
        update.message.reply_text('Привет!\nЧтобы продолжить работу, авторизуйтесь через настройки', reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup([[KeyboardButton('Информация о чеках за последние 3 месяца')],\
            [KeyboardButton('Настройки')]], resize_keyboard=True)
        update.message.reply_text('Выберите нужную опцию из списка', reply_markup=kb)
    return State.START


def settings(update: Update, context: CallbackContext):
    context.chat_data['authorization'] = False
    user = User.query.filter_by(telegram_id=update.effective_chat.id).first()
    if not user or not user.authenticated:
        kb = ReplyKeyboardMarkup([[KeyboardButton('Обновить email')], [KeyboardButton('Назад')]], resize_keyboard=True)
        update.message.reply_text('Вы не авторизированы!\nВыберите опцию из списка', reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton('Обновить email')], [KeyboardButton('Выйти')], [KeyboardButton('Назад')]],
            resize_keyboard=True)
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
    if not user or not user.authenticated:
        kb = ReplyKeyboardMarkup([[KeyboardButton('Я авторизировался')], [KeyboardButton('Назад')]],
                                 resize_keyboard=True)
        update.message.reply_text(
            f'Попробуйте снова: https://bot-blue-alpha.vercel.app/login?telegram_id={update.effective_chat.id}',
            reply_markup=kb)
        return State.AUTHORIZATION
    return settings(update, context)


def exit_menu(update: Update, context: CallbackContext):
    kb = ReplyKeyboardMarkup([[KeyboardButton('Я вышел')], [KeyboardButton('Назад')]], resize_keyboard=True)
    update.message.reply_text('Перейдите по ссылке и выйдите https://bot-blue-alpha.vercel.app', reply_markup=kb)
    return State.EXIT


def i_exited(update: Update, context: CallbackContext):
    user = User.query.filter_by(telegram_id=update.effective_chat.id).first()
    if not user or not user.authenticated:
        kb = ReplyKeyboardMarkup([[KeyboardButton('Обновить email')], [KeyboardButton('Назад')]], resize_keyboard=True)
        update.message.reply_text('Вы не авторизированы!\nВыберите опцию из списка', reply_markup=kb)
        return State.SETTINGS
    kb = ReplyKeyboardMarkup([[KeyboardButton('Я вышел')], [KeyboardButton('Назад')]], resize_keyboard=True)
    update.message.reply_text('Не получилось, попробуйте еще раз https://bot-blue-alpha.vercel.app', reply_markup=kb)
    return State.EXIT


def checks_for_last_3_months(update: Update, context: CallbackContext):
    user = User.query.filter_by(telegram_id=update.effective_chat.id).first()
    user_token = json.loads(user.tokens)["access_token"]
    reply_text = mail.list_of_checks(user_mail=user.email, user_token=user_token)
    kb = ReplyKeyboardMarkup([[KeyboardButton('Информация о чеках за последние 3 месяца')],\
        [KeyboardButton('Настройки')]], resize_keyboard=True)
    update.message.reply_text(f'Вот, что мне удалось найти:\n{reply_text}', reply_markup=kb)
    return State.START


conversation = ConversationHandler(name='main',
                                   entry_points=[CommandHandler(command='start', callback=start)],
                                   states={State.START: [
                                               MessageHandler(Filters.text('Настройки'), settings),
                                               MessageHandler(Filters.text('Информация о чеках за последние 3 месяца'), \
                                                checks_for_last_3_months)
                                            ],
                                           State.SETTINGS: [
                                               MessageHandler(Filters.text('Обновить email'), update_email),
                                               MessageHandler(Filters.text('Назад'), start),
                                               MessageHandler(Filters.text('Выйти'), exit_menu)
                                            ],
                                           State.EXIT: [
                                               MessageHandler(Filters.text('Назад'), settings),
                                               MessageHandler(Filters.text('Я вышел'), i_exited),
                                            ],
                                           State.AUTHORIZATION: [
                                               MessageHandler(Filters.text('Назад'), settings),
                                               MessageHandler(Filters.text('Я авторизировался'), i_authorized)
                                            ]},
                                   fallbacks=[CommandHandler(command='start', callback=start)], per_chat=True)
dispatcher.add_handler(conversation)
