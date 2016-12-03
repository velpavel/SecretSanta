# -*- coding: utf-8 -*-
'''Rrgister

PaVel 12.2016
'''
import standard
import db_connector
from telebot import types
from models import User

bot = None
message = None
session = None
user = None
opRegister = 'register'  # Операция для таблицы операций.
opChange = 'change_profile'


def get_text_val(ask_text):
    key_ad_info_step = 'step'
    val_ad_info_need_answer = 'need_answer'

    def ask(ask_msg=''):
        user.operation.additional_info[key_ad_info_step] = val_ad_info_need_answer
        bot.send_message(message.chat.id, ask_msg+ask_text,
                         reply_markup=types.ReplyKeyboardHide())

    def check_answer():
        if message.content_type == 'text':
            return message.text
        else:
            ask('Пришлите имя текстом\n')

    if key_ad_info_step in user.operation.additional_info:
        step = user.operation.additional_info.pop(key_ad_info_step)
        if step == val_ad_info_need_answer:
            return check_answer()
        else:
            ask()
    else:
        ask()


def ask_name():
    val = get_text_val('Представьтесь. Введите ваше имя/ник.')
    if val:
        user.name = val
        return 1
    return 0


def ask_fio():
    val = get_text_val('Введите ваши Фамилию Имя Отчество для получения почтового отправления (например, "Иванов Иван Иванович")')
    if val:
        user.fio = val
        return 1
    return 0


def ask_address():
    val = get_text_val(
        'Введите ваш почтовый адрес (например, "г. Москва, ул Тверская д.8/1 кв. 202")')
    if val:
        user.address = val
        return 1
    return 0


def ask_index():
    val = get_text_val(
        'Введите ваш почтовый индекс (например, "123480")')
    if val:
        user.index = val
        return 1
    return 0


def finish_reg():
    user.registrationDone = 1
    db_connector.put_user_operation(session, user)
    bot.send_message(message.chat.id,
                     'Регистрация завершена. Теперь введите название группы в которой вы участвуете или создайте свою', reply_markup = standard.standard_keyboard())


def register_flow(bot_in, message_in, session_in):
    """Основной поток маршрутизации.
    """

    flow_list = [
        'ask_name',
        'ask_fio',
        'ask_address',
        'ask_index',
        'done',
    ]
    status_dic = {
        'ask_name': ask_name,
        'ask_fio': ask_fio,
        'ask_address': ask_address,
        'ask_index': ask_index,
        'done': finish_reg
    }
    global bot, message, session, user
    bot = bot_in
    message = message_in
    session = session_in
    user = session.query(User).filter_by(telegramid=message.from_user.id).first()
    user.operation.decode_additional()

    if not user.operation.current_operation or user.operation.current_operation != opRegister:
        user.operation.current_operation = opRegister
        current_step = 0
        bot.send_message(message.chat.id,
                         'Для начала необходимо зарегистрироватсья - ввести свои данные для получения посылок')
    else:
        if user.operation.operation_status in flow_list:
            current_step = flow_list.index(user.operation.operation_status)
        else:
            current_step = 0
    user.operation.operation_status = flow_list[current_step]
    while status_dic[flow_list[current_step]]():
        current_step += 1
        user.operation.operation_status = flow_list[current_step]

    user.operation.code_additional()
