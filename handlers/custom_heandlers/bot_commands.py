from loader import bot
from states.user_travel_info import UserInfo
from telebot.types import Message, CallbackQuery
from keyboards.reply import reply_question, count_elements
from keyboards.inline import inline_question
from utils import api_destination, api_hotels, request_info
from datetime import datetime, timedelta
from telegram_bot_calendar import DetailedTelegramCalendar
from database import *
from loguru import logger


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def custom_commands(message: Message) -> None:
    logger.info(f"Пользователь {message.from_user.id} использует команду {message.text}")
    bot.set_state(message.from_user.id, UserInfo.city, message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город для поиска')
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_user:
        data_user['id'], data_user['name'], data_user['command'] = \
            message.from_user.id, message.from_user.first_name, message.text[1:]


@bot.message_handler(commands=['history'])
def user_history(message: Message) -> None:
    logger.info(f"Пользователь {message.from_user.id} использует команду {message.text}")
    history = user_db.get_history(message.from_user.id)

    bot.send_message(
        message.from_user.id,
        text=f"{message.from_user.first_name}, история ваших запросов:\n\n{history}",
        disable_web_page_preview=True,
    )
    if history == '(нет данных)':
        final_message(message.from_user.id)
    else:
        bot.send_message(message.from_user.id, 'Очистить историю запросов?', reply_markup=inline_question.yes_no())


@bot.callback_query_handler(func=lambda call: call.data == 'No' or call.data == 'Yes')
def clear_history(call: CallbackQuery) -> None:
    if call.data == 'Yes':
        logger.info(f"Пользователь {call.from_user.id} очистил историю поиска")
        user_db.delete_history(call.from_user.id)
        bot.send_message(call.from_user.id, 'История поиска очищена')
        final_message(call.from_user.id)


@bot.message_handler(state=UserInfo.city)
def get_city(message: Message) -> None:
    if message.text.isalpha():
        logger.info(f"Пользователь {message.from_user.id} ввел город: {message.text}")
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_user:
            data_user['city'] = message.text.capitalize()
            question = api_destination.city_markup(message.text)
        if not question:
            bot.set_state(message.from_user.id, UserInfo.city, message.chat.id)
            bot.send_message(message.from_user.id, 'По данному запросу ничего не найдено.\n'
                                                   'Введите город для поиска еще раз')
        if question == 'Error':
            bot.send_message(message.from_user.id, 'К сожалению сервис временно недоступен.\n'
                                                   'Попробуйте сделать запрос чуть позже')
        else:
            bot.send_message(message.from_user.id, 'Уточните, пожалуйста:', reply_markup=question)
            logger.info(f"Пользователю {message.from_user.id} направлена inline клавиатура для уточнения локации")
    else:
        logger.info(f"Пользователь {message.from_user.id} ввел город в некорректном формате")
        bot.send_message(message.from_user.id, 'Название города может содержать только буквы!')


@bot.callback_query_handler(func=lambda call: call.data.startswith('XXX'))
def callback_destination(call: CallbackQuery) -> None:
    if call.data == 'XXX':
        logger.info(f"Пользователь {call.from_user.id} отменил ввод город")
        bot.set_state(call.from_user.id, UserInfo.city)
        bot.send_message(call.from_user.id, text='Введите город для поиска')
    else:
        with bot.retrieve_data(call.from_user.id) as data_user:
            data_user['destination_id'] = f'{call.data[3:]}'
            logger.info(f"Пользователь {call.from_user.id} выбрал локацию c id: {call.data}")
            if data_user['command'] == 'bestdeal':
                get_budget(call.from_user.id)
            else:
                bot.set_state(call.from_user.id, UserInfo.count_hotels, call.from_user.id)
                bot.send_message(
                    call.from_user.id,
                    'Сколько отелей вам показать?',
                    reply_markup=count_elements.numbers_to_ten())


def get_budget(user_id: int):
    bot.send_message(user_id, text='Введите диапозон цены в $ через пробел')
    bot.set_state(user_id, UserInfo.budget)


@bot.message_handler(state=UserInfo.budget)
def budget(message: Message) -> None:
    if message.text.replace(' ', '').isdigit():
        logger.info(f"Пользователь {message.from_user.id} ввел бюджет {message.text} $")
        mes_budget = list(map(int, message.text.split()))
        if len(mes_budget) == 2:
            mes_budget = sorted(mes_budget)
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data_user:
                data_user['min_price'], data_user['max_price'] = mes_budget[0], mes_budget[1]
            bot.set_state(message.from_user.id, UserInfo.dist_to_center)
            bot.send_message(message.from_user.id, 'Введите расстояние до центра (в км)')
        else:
            logger.info(f"Пользователь {message.from_user.id} ввел бюджет некорректно")
            bot.send_message(message.from_user.id, 'Неверный ввод, введите два числа через пробел!')
    else:
        logger.info(f"Пользователь {message.from_user.id} ввел бюджет некорректно")
        bot.send_message(message.from_user.id, 'Неверный ввод, введите два числа через пробел!')


@bot.message_handler(state=UserInfo.dist_to_center)
def get_distance(message: Message) -> None:
    if message.text.isdigit():
        logger.info(f"Пользователь {message.from_user.id} ввел расстояние до центра: {message.text}")
        bot.set_state(message.from_user.id, UserInfo.check_in)
        distance = int(message.text)
        if 0 < distance <= 50:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data_user:
                data_user['dist_to_center'] = distance
            bot.set_state(message.from_user.id, UserInfo.count_hotels, message.from_user.id)
            bot.send_message(
                message.from_user.id,
                'Сколько отелей вам показать?',
                reply_markup=count_elements.numbers_to_ten())
        else:
            logger.info(f"Пользователь {message.from_user.id} ввел расстояние до центра некорректно")
            bot.send_message(message.from_user.id, 'Неверный ввод, введите цифрами целое число(не более 50)!')
    else:
        bot.send_message(message.from_user.id, 'Неверный ввод, введите цифрами целое число(не более 50)!')
        logger.info(f"Пользователь {message.from_user.id} ввел расстояние до центра некорректно")


@bot.message_handler(state=UserInfo.count_hotels)
def get_count_hotels(message: Message) -> None:
    if message.text.isdigit():
        logger.info(f"Пользователь {message.from_user.id} ввел количество отелей: {message.text}")
        bot.set_state(message.from_user.id, UserInfo.check_in)
        hotels = int(message.text)
        if not 0 < hotels <= 10:
            logger.info(f"Пользователь {message.from_user.id} "
                        f"ввел количество отелей, превышающее максимально допустимое")
            bot.send_message(message.from_user.id, 'Сожалею, но могу вывести максимум 10 отелей')
            hotels = 10
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_user:
            data_user['count_hotels'] = hotels
            input_check_in(message.from_user.id)
    else:
        logger.info(f"Пользователь {message.from_user.id} ввел количество отелей некорректно")
        bot.send_message(message.from_user.id, 'Неверный ввод, введите цифрами!')


def input_check_in(user_id):
    now = datetime.now().date()
    calendar, step = DetailedTelegramCalendar(calendar_id=1, locale='ru', min_date=now).build()
    bot.send_message(user_id,
                     "Выберите дату заезда",
                     reply_markup=calendar)
    logger.info(f"Пользователю {user_id} направлена Inline клавиатура для ввода даты заезда")


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal(call):
    result, key, step = DetailedTelegramCalendar(calendar_id=1).process(call.data)
    if not result and key:
        bot.edit_message_text("Выберите дату заезда",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        logger.info(f"Пользователь {call.from_user.id} ввел дату заезда: {result}")
        result = str(result)
        bot.edit_message_text(f"Дата заезда {result}",
                              call.message.chat.id,
                              call.message.message_id)
        bot.set_state(call.message.chat.id, UserInfo.check_in, call.from_user.id)
        with bot.retrieve_data(call.from_user.id) as data_user:
            data_user['check_in'] = result
        result = datetime.strptime(result, '%Y-%m-%d') + timedelta(days=1)
        result = datetime.date(result)
        input_check_out(call.from_user.id, result)


def input_check_out(user_id, start_date):
    calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru',
                                              min_date=start_date, current_date=start_date).build()
    bot.send_message(user_id,
                     "Выберите дату выезда",
                     reply_markup=calendar)
    logger.info(f"Пользователю {user_id} направлена Inline клавиатура для ввода даты выезда")


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal(call):
    result, key, step = DetailedTelegramCalendar(calendar_id=2).process(call.data)
    if not result and key:
        bot.edit_message_text(f"Выберите дату выезда",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        logger.info(f"Пользователь {call.from_user.id} ввел дату выезда: {result}")
        result = str(result)
        bot.edit_message_text(f"Дата выезда {result}",
                              call.message.chat.id,
                              call.message.message_id)
        bot.set_state(call.message.chat.id, UserInfo.check_in, call.from_user.id)
        with bot.retrieve_data(call.from_user.id) as data_user:
            start_date = datetime.strptime(str(data_user['check_in']), '%Y-%m-%d')
            end_date = datetime.strptime(result, '%Y-%m-%d')
            count_days = end_date - start_date
            count_days = count_days.days + 1
            data_user['check_out'], data_user['count_days'] = result, count_days
        bot.set_state(call.from_user.id, UserInfo.photo, call.from_user.id)
        bot.send_message(call.from_user.id, 'Показать фотографии?', reply_markup=reply_question.yes_no())


@bot.message_handler(state=UserInfo.photo)
def get_photo(message: Message) -> None:
    bot.set_state(message.from_user.id, UserInfo.count_photo, message.chat.id)
    if message.text.lower() == 'да':
        logger.info(f"Пользователь {message.from_user.id} запросил фотографии")
        bot.send_message(message.from_user.id, 'Сколько фотографий показать?',
                         reply_markup=count_elements.numbers_to_five())
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_user:
            data_user['photo'] = True
    elif message.text.lower() == 'нет':
        logger.info(f"Пользователь {message.from_user.id} отказался от вывода фотографий")
        bot.set_state(message.from_user.id, UserInfo.correct_input, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_user:
            data_user['photo'], data_user['count_photo'] = False, 0
        text = request_info.user_input(data_user)
        bot.send_message(message.from_user.id, text)
        bot.send_message(message.chat.id, 'Параметры поиска верные?', reply_markup=reply_question.yes_no())
    else:
        logger.info(f"Пользователь {message.from_user.id} ответил некорректно про фото")
        bot.send_message(
            message.from_user.id,
            'Неверный ввод, введите "Да" или "Нет"!',
            reply_markup=reply_question.yes_no())


@bot.message_handler(state=UserInfo.count_photo)
def get_count_pictures(message: Message) -> None:
    if message.text.isdigit():
        photos = int(message.text)
        if 0 < photos <= 5:
            logger.info(f"Пользователь {message.from_user.id} запросил {photos} фото отеля")
            bot.set_state(message.from_user.id, UserInfo.correct_input, message.chat.id)
        else:
            logger.info(f"Пользователь {message.from_user.id} превысил димит вывода фото отеля")
            bot.send_message(message.chat.id, 'Сожалею, но могу вывести максимум 5 фото')
            photos = 5
        bot.set_state(message.from_user.id, UserInfo.correct_input, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_user:
            data_user['count_photo'] = photos
        text = request_info.user_input(data_user)
        bot.send_message(message.from_user.id, text)
        logger.info(f"Пользователю {message.from_user.id} направлен запрос на подтверждение параметров поиска\n"
                    f"Параметры:\n{text}")
        bot.send_message(message.chat.id, 'Параметры поиска верные?',
                         reply_markup=reply_question.yes_no())
    else:
        logger.info(f"Пользователь {message.from_user.id} ввел количество фото некорректно")
        bot.send_message(message.from_user.id, 'Неверный ввод, введите цифрами!',
                         reply_markup=reply_question.yes_no())


@bot.message_handler(state=UserInfo.correct_input)
def is_true_input(message: Message) -> None:
    if message.text.lower() == 'да':
        logger.info(f"Пользователь {message.from_user.id} подтвердил параметры поиска")
        bot.send_message(message.from_user.id, 'Делаю запрос')
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_user:
            bot.send_sticker(message.from_user.id,
                             "CAACAgIAAxkBAAEFuFFjDlJkPjyYQMg2t1VDGwNilQQwEwACJhkAAm2BoUsKGKK06NfdhSkE")
            user_hotels = api_hotels.output_hotels(message.from_user.id, data_user)
        if not user_hotels:
            logger.info(f'Отели не найдены по заданным параметрам')
            user_db.save_data(
                data_user,
                'отели не найдены'
            )
            bot.send_message(message.from_user.id,
                             text='Сожалею, но по заданным критериям не удалось найти отели')
        else:
            user_db.save_data(
                data_user,
                user_hotels[1]
            )
            bot.send_message(
                message.from_user.id,
                text=f'😇Поиск Завершен😇!\n'
                     f'Найдено отелей: {user_hotels[0]}'
            )
        logger.info(f'Запрос и параметры, введенные пользователем записаны в базу данных')
        bot.delete_state(message.from_user.id, message.chat.id)
        final_message(message.from_user.id)
    else:
        logger.info(f"Пользователь {message.from_user.id} отменил ввод параметров")
        bot.send_message(message.from_user.id, 'Эх... Попробуем снова\nВведите город для поиска')
        bot.set_state(message.from_user.id, UserInfo.city, message.chat.id)


def final_message(user_id) -> None:
    bot.send_message(user_id,
                     text='👇Для продолжения поиска выберите новую команду из меню')


@bot.message_handler(state=None)
def bot_echo(message: Message):
    bot.reply_to(message, "Я вас не понял, попробуйте выбрать команду из меню или нажмите /help")
