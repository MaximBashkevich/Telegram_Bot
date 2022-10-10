from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def yes_no() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(InlineKeyboardButton(text="Нет", callback_data='No'),
                 InlineKeyboardButton(text="Да", callback_data='Yes'))
    return keyboard
