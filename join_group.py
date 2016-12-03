# -*- coding: utf-8 -*-
'''Create_group

PaVel 12.2016
'''
import standard, utils
import db_connector
from telebot import types
from models import User, Group, Member

bot = None
message = None
session = None
user = None
group = None
opGroup = 'join_group'  # Операция для таблицы операций.


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
            ask('Пришлите текстом\n')

    if key_ad_info_step in user.operation.additional_info:
        step = user.operation.additional_info.pop(key_ad_info_step)
        if step == val_ad_info_need_answer:
            return check_answer()
        else:
            ask()
    else:
        ask()

def find_group():
    key_ad_info_step = 'step'
    val_ad_info_need_name = 'need_name'
    val_ad_info_need_select = 'need_select'
    key_ad_info_buttons = 'buttons-group_id'

    def ask_name(ask_msg=''):
        ask_text = 'Введите название или часть названия группы, которую вы ищете. Не менее 3х символов.'
        user.operation.additional_info[key_ad_info_step] = val_ad_info_need_name
        bot.send_message(message.chat.id, ask_msg+ask_text,
                         reply_markup=standard.cancel_keyboard())
        return 0

    def ask_select():
        if message.content_type == 'text':
            if len(message.text) >= 3:
                groups = session.query(Group).filter(Group.name_lower.like('%'+message.text.lower()+'%'),
                                                     Group.active==True).all()
                if groups:
                    text = 'Список найденных групп:\n'
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                    user.operation.additional_info[key_ad_info_buttons] = {}
                    for i in range(len(groups)):
                        # структура id, Name, author
                        text += '{}) <b>{}</b> от автора {}\n'.format(i + 1, groups[i].name, groups[i].owner.name)
                        button_text = '{}) {}'.format(i + 1, groups[i].name)
                        markup.row(button_text)
                        user.operation.additional_info[key_ad_info_buttons][button_text] = groups[i].id
                    text += '\nВыберите свою группу кнопкой ниже.'
                    markup.row(standard.cancel_commands[0].capitalize())
                    user.operation.additional_info[key_ad_info_step] = val_ad_info_need_select
                    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
                    return 0
                else:
                    return ask_name('Не найдено ни одной группы с таким названием\n')
            else:
                return ask_name('Введите не меньше 3х символов названия\n')
        else:
            return ask_name('Пришлите имя текстом\n')

    def do_select():
        if message.content_type == 'text':
            group_id = user.operation.additional_info.get(key_ad_info_buttons, dict()).get(message.text)
            group = session.query(Group).filter(Group.id == group_id).first()
            if group:
                user.operation.additional_info['group_id'] = group.id
                text = 'Выбрана группа <b>{}</b> от автора {}. Дата распределения: {}.'.format(group.name, group.owner, group.date_shuffle.strftime('%d.%m.%Y'))
                bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=standard.cancel_keyboard())
                member = session.query(Member).filter(Member.group == group, Member.user == user).first()
                if member:
                    db_connector.put_user_operation(session, user)
                    bot.send_message(message.chat.id,
                                     'Вы уже участвуете в этой группе. Ваши пожелания: "{}"'.format(member.suggestions),
                                     reply_markup=standard.standard_keyboard())
                    return 0
                return 1
            else:
                return ask_name('Выбор нужно делать кнопкой\n')
        else:
            return ask_name('Выбор нужно делать кнопкой\n')

    if key_ad_info_step in user.operation.additional_info:
        step = user.operation.additional_info.pop(key_ad_info_step)
        if step == val_ad_info_need_name:
            return ask_select()
        elif step == val_ad_info_need_select:
            return do_select()
        else:
            return ask_name()
    else:
        return ask_name()


def ask_password():
    val = get_text_val(
        'Введите пароль для доступа к этой группе')
    if val:
        if group.password == val:
            return 1
        else:
            bot.send_message(message.chat.id, 'Неверный пароль', reply_markup=standard.cancel_keyboard())
            return ask_password()
    return 0


def ask_suggestion():
    val = get_text_val('Введите ваши пожелания к подарку.')
    if val:
        member = Member(group=group, user=user,)
        session.add(member)
        member.suggestions = val
        member.active = True
        return 1
    return 0


def finish():
    member = session.query(Member).filter(Member.group == group, Member.user == user).first()
    if member:
        msg = '''Ваше участие в группе {} зарегистрировано. Дата распределения: {}
Подарок будет выслан получателю "{}" по адресу {} {}.
Ваши пожелания к подарку: {}'''.format(group.name, group.date_shuffle.strftime('%d.%m.%Y'),
                                      user.fio, user.index, user.address,
                                      member.suggestions)
    else:
        msg = 'Что-то пошло не так. Попробуйте ещё раз'
    db_connector.put_user_operation(session, user)
    bot.send_message(message.chat.id,
                     msg, reply_markup=standard.standard_keyboard())

def cancel_all():
    db_connector.put_user_operation(session, user)
    bot.send_message(message.chat.id,
                     'Отменено', reply_markup=standard.standard_keyboard())


def route_flow(bot_in, message_in, session_in):
    """Основной поток маршрутизации.
    """

    global bot, message, session, user, group
    flow_list = [
        'find_group',
        'ask_password',
        'ask_suggestion',
        'done',
    ]
    status_dic = {
        'find_group': find_group,
        'ask_password': ask_password,
        'ask_suggestion': ask_suggestion,
        'done': finish,
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
