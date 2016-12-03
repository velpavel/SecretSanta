# -*- coding: utf-8 -*-
'''Функции админа.

PaVel 12.2016
'''
import configparser
from telebot import types
from models import User, Operation, Log, Group, Member
from sqlalchemy import desc, func

config = configparser.ConfigParser()
config.read('config.ini')
admin_id = config['BASE'].get('Admin_id')
admin_id = int(admin_id) if admin_id.isdigit() else 0

admin_commands = ['admin', 'last_users', 'last_groups', 'log']


def admin_flow(bot, message, session):
    if message.from_user.id == admin_id:
        comm_list = message.text.lower().split(' ')
        if comm_list[0] == '/last_users':
            count = session.query(User).count()
            users = []
            for u in session.query(User).order_by(desc(User.registrationDate)).limit(10):
                users.append('{}. {}'.format(u.name, u.registrationDate))
            bot.send_message(message.chat.id, 'Всего {} \nПоследние\n{}'.format(count, '\n'.join(users)))
        elif comm_list[0] == '/log':
            if len(comm_list) >= 2: count_str = comm_list[1]
            else: count_str = 10
            last_recs = session.query(Log).order_by(desc(Log.datetime)).limit(count_str).all()
            text = 'Последние записи из лога. Количество {}:\n'.format(count_str) + '\n'.join([str(r) for r in last_recs])
            bot.send_message(message.chat.id, text)
        elif comm_list[0] == '/last_groups':
            q = session.query(Group, func.count(Member.id).label('members_found')).outerjoin(Member, Member.group_id == Group.id).filter(Group.active==True).group_by(Group.id).all()
            text = 'Всего групп {} \n\n'.format(session.query(Group).filter(Group.active==True).count())
            for group, count_members in q:
                text += '<b>{}</b> автора {}. Участников: {}\n'.format(group.name, group.owner, count_members)
            bot.send_message(message.chat.id, text, parse_mode='HTML')
        elif comm_list[0] == '/admin':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for command in admin_commands:
                markup.add(types.KeyboardButton('/'+command))
            bot.send_message(message.chat.id, 'Админ команды', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, 'Нет такой команды')
    else:
        bot.send_message(message.chat.id, "Недоступно")