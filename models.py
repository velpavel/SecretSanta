# -*- coding: utf-8 -*-
"""Модели

PaVel 12.2016
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Date, DateTime, Boolean, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import create_engine
import configparser, json

config = configparser.ConfigParser()
config.read('config.ini')
Base = declarative_base()
dialect = config['DB']['Dialect']
base_url = ''
if dialect == 'sqlite':
    base_url = 'sqlite:///{}'.format(config['DB']['Dbpath'])
else:
    driver = config['DB'].get('Driver')
    username = config['DB'].get('Driver')
    password = config['DB'].get('Driver')
    dbpath = config['DB'].get('Driver')
    if driver: driver = '+' + driver
    # dialect+driver://username:password@host:port/database
    base_url = '{}{}://{}:{}@{}'.format(dialect, driver, username, password, dbpath)
engine = create_engine(base_url)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'user'
    telegramid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    fio = Column(String(255))
    address = Column(String())
    index = Column(String())
    registrationDone = Column(Boolean(), default=False)
    registrationDate = Column(DateTime)
    active = Column(Boolean, default=True)

    def __repr__(self):
        return self.name


class Operation(Base):
    __tablename__ = 'user_operation'
    telegramid = Column(Integer, ForeignKey('user.telegramid'), primary_key=True, index=True)
    user = relationship(User, backref=backref("operation", uselist=False))
    current_operation = Column(String(50))
    operation_status = Column(String(50))
    additional_info_db = Column(String())
    additional_info = {}

    def __repr__(self):
        return '{}: {}. {}'.format(self.user, self.current_operation, self.operation_status)

    def decode_additional(self):
        if self.additional_info_db and self.additional_info_db != 'null':
            self.additional_info = json.loads(self.additional_info_db)
        else:
            self.additional_info = dict()

    def code_additional(self):
        self.additional_info_db = json.dumps(self.additional_info)


class Log(Base):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime)
    from_who = Column(String(50))
    user_id = Column(Integer, ForeignKey('user.telegramid'), index=True)
    user = relationship(User)
    msg_type = Column(String(50))
    msg_text = Column(String())
    operation = Column(String(50))
    status = Column(String(50))
    additional_info = Column(String())
    function = Column(String(50))
    comment = Column(String())

    def __repr__(self):
        return '{} {}: {}. {}'.format(self.datetime.strftime('%d.%m.%Y %X'),
                                      self.user if self.user else self.from_who,
                                      self.msg_text if self.msg_text else self.comment, self.operation)


class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(50), index=True)
    name_lower = Column(String(50), index=True) # костыль, т.к. в SQLite не работает lower() для русского, а значит не работает регистронезависимый поиск
    #description = Column(String(255))
    owner_id = Column(Integer, ForeignKey('user.telegramid'), index=True)
    owner = relationship(User, backref=backref('groups'))
    password = Column(String())
    date_shuffle = Column(Date)
    shuffle_done = Column(Boolean, default=False)
    active = Column(Boolean, default=False)

    def __repr__(self):
        return self.name


class Member(Base):
    __tablename__ = 'member'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    group_id = Column(Integer, ForeignKey('group.id'), index=True)
    group = relationship(Group, backref=backref('members'))
    user_id = Column(Integer, ForeignKey('user.telegramid'), index=True)
    user = relationship(User, foreign_keys=[user_id])
    suggestions = Column(String())
    send_to_id = Column(Integer, ForeignKey('user.telegramid'))
    send_to = relationship(User, foreign_keys=[send_to_id])
    track_number = Column(String())
    active = Column(Boolean, default=False)

    def __repr__(self):
        return self.user.name

def create_all():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    create_all()
