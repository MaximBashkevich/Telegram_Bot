import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env')
else:
    load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
DEFAULT_COMMANDS = (
    ('start', "Запустить бота"),
    ('help', "Вывести справку"),
    ('lowprice', 'поиск самых дешёвых отелей'),
    ('highprice', 'поиск самых дорогих отелей'),
    ('bestdeal', 'поиск отелей, наиболее подходящих по цене и расположению'),
    ('history', 'история поиска')

)
