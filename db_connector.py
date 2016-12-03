# -*- coding: utf-8 -*-
"""Работа с БД

PaVel 09.2016
"""
import inspect, datetime
from models import DBSession, User, Operation, Log

# Работа с user_operation.
# Текущие состояния пользователя при необходимости сохраняются в user_operation.
# current_operation - Операция (регистраиця, работа с задачами и т.п.)
# operation_status - шаг/этап операции.
# additional_info - вся необходимая доп инфа. при необходимости сохранить группу параметров использовать json

def put_user_operation(session, user, operation=None, status=None, additional_info=None):
    """Сохранить в БД инфу об операции пользователя.

    id - TelegramID пользователя. message.from_user.id
    Вариант put_user_operation(id) - очищает записи об операциях пользователя.
    """
    session.add(user)
    user.operation.current_operation=operation
    user.operation.operation_status=status
    user.operation.additional_info=additional_info
    user.operation.code_additional()
# /Работа с user_operation.


def save_to_log(from_who='user', message_type=None, message=None, comment_text='', msg_text=''):
    """Сохранить в лог. Внимательно передавать from_who

    from_who - 'bot', 'user', 'system'. От кого сообщение
    message - тип message. Сообщение от пользователя.
    comment_text - дополнительный текст.
    msg_text - текст сообщения. Использовать для сохранения ответа бота на message пользователя

    Примеры.
    save_to_log('user', message) - сохранить сообщение от пользователя.
    save_to_log('system', comment_text=err_text) - сохранить сообщение от системы. Например, об ошибке.
    save_to_log('bot', message=message_from_user, msg_text=bot_msg_text) - сохранить сообщение от бота пользоателю.
    """
    if from_who not in ('bot', 'user', 'system'):
        comment_text += ' ' + from_who
        from_who = 'need_help'
    operation = None
    tid = None
    session = DBSession()
    if message:
        tid = message.from_user.id
        if from_who == 'user':
            if message.content_type == 'text':
                msg_text = message.text
            if message.content_type == 'contact':
                msg_text = str(message.contact)

        operation = session.query(Operation).filter_by(telegramid=tid).first()

    if operation is None: operation = Operation()
    log = Log(datetime=datetime.datetime.now(), from_who=from_who, user_id=tid, msg_text=msg_text,
              msg_type=message_type, operation=operation.current_operation, status=operation.operation_status,
              additional_info=operation.additional_info_db, function=inspect.stack()[1][3], comment=comment_text)
    session.add(log)
    session.commit()
    session.close()