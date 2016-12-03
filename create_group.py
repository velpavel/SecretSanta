# -*- coding: utf-8 -*-
'''Create_group

PaVel 12.2016
'''
import standard, utils
import db_connector
import datetime
from telebot import types
from models import User, Group

bot = None
message = None
session = None
user = None
group = None
opGroup = 'create_group'  # Операция для таблицы операций.


def get_text_val(ask_text):
    key_ad_info_step = 'step'
    val_ad_info_need_answer = 'need_answer'

    def ask(ask_msg=''):
        user.operation.additional_info[key_ad_info_step] = val_ad_info_need_answer
        bot.send_message(message.chat.id, ask_msg+ask_text,
                         reply_markup=standard.cancel_keyboard())

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
    val = get_text_val('Введите название вашей группы участников Тайного Санты (не менее 3х символов).')
    if val:
        if len(val) < 3:
            bot.send_message(message.chat.id, 'Название должно состоять не менее, чем из 3х символов', reply_markup=standard.cancel_keyboard())
            return ask_name()
        elif session.query(Group).filter(Group.name_lower==val.lower(), Group.active==True).first():
            bot.send_message(message.chat.id, 'Группа с таким названием уже существует. Придумайте новое',
                             reply_markup=standard.cancel_keyboard())
            return ask_name()
        else:
            group.name = val
            group.name_lower = val.lower()
            return 1
    return 0


def ask_password():
    val = get_text_val(
        'Введите пароль для доступа к вашей группе. Только люди, знающие этот пароль, смогут участвовать с вами в Тайном Санте')
    if val:
        group.password = val
        return 1
    return 0


def ask_date():
    msg = '''Введите дату окончания приёма заявок. В этот день генератор случайных чисел распределит отправителей и получателей и вышлет участникам их адресатов.
Дату необходимо воодить в формате дд.мм.гггг т.е. 15 декабря 2016 года это 15.12.2016 '''
    val = get_text_val(msg)
    if val:
        try:
            to_date = datetime.datetime.strptime(val, '%d.%m.%Y').date()
        except:
            to_date = 0
        if to_date:
            if to_date <= datetime.datetime.now().date():
                bot.send_message(message.chat.id, 'Это было давно... Выберите число из будущего', reply_markup=standard.cancel_keyboard())
                return ask_date()
            group.date_shuffle = to_date
            return 1
        else:
            bot.send_message(message.chat.id, 'Неверный формат даты', reply_markup=standard.cancel_keyboard())
            return ask_date()
    return 0


def finish():
    msg = '''Ваша группа "{}" создана. Пароль группы: {}\n Дата распределения: {}. Приглашайте участников.
    Обратите внимание! Вы сами пока не считаетесь участником своей группы. Для участия Вам надо выбрать группу и зарегистрироваться в ней.'''.format(group.name, group.password, group.date_shuffle.strftime('%d.%m.%Y'))
    group.active = True
    db_connector.put_user_operation(session, user)
    bot.send_message(message.chat.id,
                     msg, reply_markup=standard.standard_keyboard())


def cancel_all():
    if group:
        session.delete(group)
    db_connector.put_user_operation(session, user)
    bot.send_message(message.chat.id,
                     'Создание группы отменено', reply_markup=standard.standard_keyboard())


def route_flow(bot_in, message_in, session_in):
    """Основной поток маршрутизации.
    """

    global bot, message, session, user, group
    flow_list = [
        'ask_name',
        'ask_password',
        'ask_date',
        'done',
    ]
    status_dic = {
        'ask_name': ask_name,
        'ask_password': ask_password,
        'ask_date': ask_date,
        'done': finish
    }

    bot = bot_in
    message = message_in
    session = session_in
    user = session.query(User).filter_by(telegramid=message.from_user.id).first()
    user.operation.decode_additional()

    if not user.operation.current_operation or user.operation.current_operation != opGroup:
        user.operation.current_operation = opGroup
        current_step = 0
    else:
        if user.operation.operation_status in flow_list:
            current_step = flow_list.index(user.operation.operation_status)
        else:
            current_step = 0
    group = user.operation.additional_info.get('group_id')
    if group:
        group = session.query(Group).filter(Group.id == group, Group.owner == user).first()
    if not group:
        print('code', user.operation.additional_info_db)
        print('de_code', user.operation.additional_info)
        group = Group(owner=user)
        session.add(group)
        user.operation.code_additional()
        session.commit()
        user.operation.decode_additional() # @Разобраться. Без этого после отмены в additional итогда что-то левое после commit образуется
        user.operation.additional_info['group_id'] = group.id
        current_step = 0

    if utils.text_lower_wo_command(message) in standard.cancel_commands:
        cancel_all()
        user.operation.code_additional()
        return

    user.operation.operation_status = flow_list[current_step]
    while status_dic[flow_list[current_step]]():
        current_step += 1
        user.operation.operation_status = flow_list[current_step]

    user.operation.code_additional()
