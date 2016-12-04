# -*- coding: utf-8 -*-
"""Файл для запуска бота.
Здесь же маршрутизация сообщения.

PaVel 12.2016
"""

import datetime, random
from models import Group, Member, DBSession
from bot import bot
from db_connector import save_to_log


def send_message(id, text):
    try:
        bot.send_message(id,text)
    except Exception as e:
        err_text = "{} Send Error (tid: {}): {} : {}".format(datetime.datetime.now().strftime('%x %X'), id, e.__class__, e)
        print(err_text)
        save_to_log('system', comment_text=err_text)

def start_shuffle():
    random.seed()
    session = DBSession()
    groups = session.query(Group).filter(Group.date_shuffle <= datetime.datetime.now().date(), Group.shuffle_done == False, Group.active == True).all()
    for group in groups:
        if len(group.members) == 0:
            group.shuffle_done = True
            session.commit()
            send_message(group.owner.telegramid,
                             'К сожалению, в вашей группе "{}" нет ни одного участника. Некому высылать подарки'.format(group.name))
        elif len(group.members) == 1:
            group.shuffle_done = True
            session.commit()
            send_message(group.owner.telegramid,
                             'К сожалению в вашей группе "{}" всего один учатник. Некому высылать подарки.'.format(group.name))
            send_message(group.members[0].user.telegramid,
                             'Вы единственный участник группы {}. Подарите себе что-нибудь приятное'.format(group.name))
        elif len(group.members) > 1:
            member_list = group.members[:]
            random.shuffle(member_list)
            member_list[-1].send_to = member_list[0].user
            for i in range(len(member_list)-1):
                member_list[i].send_to = member_list[i+1].user
            group.shuffle_done = True
            session.commit()
            for member in group.members:
                to_member = session.query(Member).filter(Member.group == group, Member.user == member.send_to).first()
                text = '''Распределение получателей для группу {} завершено!\nВы Санта для {}. Пожелания к подарку: {}
    подарок высылать по следующему адресу: {} {}. На имя {}'''.format(group.name, to_member.user.name, to_member.suggestions,
                                                                      to_member.user.index, to_member.user.address,
                                                                      to_member.user.fio)
                send_message(member.user.telegramid, text)
            send_message(group.owner.telegramid,
                             'Распределение получателей для группу {} завершено! Участников: {}.\
                              Всем участникам разосланы их получатели.'.format(group.name, len(group.members)))
    session.close()
    save_to_log('system', comment_text="Shuffle done")

if __name__ == '__main__':
    start_shuffle()