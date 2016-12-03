from telebot import types

find_group = ['найти группу', ]
create_group = ['создать группу']
cancel_commands = ['отмена', 'cancel']


def standard_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(*find_group)
    markup.row(*create_group)
    return markup

def cancel_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Отмена')
    return markup