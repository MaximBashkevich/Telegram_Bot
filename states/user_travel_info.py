from telebot.handler_backends import State, StatesGroup


class UserInfo(StatesGroup):
    city = State()
    destination_id = State()
    budget = State()
    dist_to_center = State()
    count_hotels = State()
    check_in = State()
    check_out = State()
    photo = State()
    count_photo = State()
    correct_input = State()
