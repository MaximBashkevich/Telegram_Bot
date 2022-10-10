from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def yes_no() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add(KeyboardButton("Нет"), KeyboardButton("Да"))
    return keyboard
