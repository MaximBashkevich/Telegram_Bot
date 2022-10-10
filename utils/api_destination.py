import requests
import re
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict
import os
from loguru import logger


def city_founding(town: str) -> List or bool:
    RAPID_API_KEY = os.getenv('RAPID_API_KEY')

    url = "https://hotels4.p.rapidapi.com/locations/v2/search"

    querystring: Dict = {"locale": "ru_RU", 'query': town}

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }
    logger.info(f"Направлен запрос к эндпоинту {url}")
    response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
    if response.status_code == requests.codes.ok:
        logger.info("Получен ответ от api")
        pattern = r'(?<="CITY_GROUP",).+?[\]]'
        find = re.search(pattern, response.text)
        if find:
            result = json.loads(f"{{{find[0]}}}")
            cities = list()
            for dest_id in result['entities']:
                clear_destination = re.sub(r'(<span)(.*)(span>)', querystring['query'], dest_id['caption'])
                cities.append({'city_name': clear_destination,
                               'destination_id': dest_id['destinationId']
                               }
                              )
            return cities
        else:
            logger.info(f"Ответ от {url} получен, но отсутствует информация с id локации")
            return False
    else:
        logger.info(f"Ответ от {url} не получен. Код состояния ответа {response.status_code}")
        return 'Error API'


def city_markup(town: str) -> InlineKeyboardMarkup or bool:
    # Функция "city_founding" уже возвращает список словарей с нужным именем и id
    cities = city_founding(town=town)
    if not cities:
        return False
    elif cities == 'Error API':
        return 'Error'
    else:
        destinations = InlineKeyboardMarkup()
        for city in cities:
            destinations.add(InlineKeyboardButton(
                text=city['city_name'],
                callback_data=f'XXX{city["destination_id"]}')
            )
        destinations.add(InlineKeyboardButton(
            text='ОТМЕНА, нет нужного в списке',
            callback_data='XXX'))
        logger.info("Сформирована inline клавиатура для уточнения локации")
        return destinations
