from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def numbers_to_ten() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(row_width=10, one_time_keyboard=True, resize_keyboard=True)
    numbers = []
    for number in range(1, 11):
        numbers.append(KeyboardButton(str(number)))
    keyboard.add(*numbers)
    return keyboard


def numbers_to_five() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(row_width=5, one_time_keyboard=True, resize_keyboard=True)
    numbers = []
    for number in range(1, 6):
        numbers.append(KeyboardButton(str(number)))
    keyboard.add(*numbers)
    return keyboard
