import requests
import os
import json
from loader import bot
from telebot.types import InputMediaPhoto
from loguru import logger


def output_hotels(chat_id, data_user: dict):
    sort_order = {'lowprice': 'PRICE', 'highprice': 'PRICE_HIGHEST_FIRST', 'bestdeal': 'DISTANCE_FROM_LANDMARK'}
    rapid_api_key = os.getenv('RAPID_API_KEY')

    url = "https://hotels4.p.rapidapi.com/properties/list"

    querystring = {"destinationId": data_user['destination_id'],
                   "pageNumber": "1",
                   "pageSize": data_user['count_hotels'],
                   "checkIn": data_user['check_in'],
                   "checkOut": data_user['check_out'],
                   "adults1": "1",
                   "sortOrder": sort_order[data_user['command']],
                   "locale": "en_US",
                   "currency": "USD"}
    if data_user['command'] == 'bestdeal':
        querystring['priceMin'], querystring['priceMax'] = \
            round(data_user['min_price'] / data_user['count_days']), \
            round(data_user['max_price'] / data_user['count_days'])
        querystring['landmarkIds'], querystring['pageSize'] = 'City center', '25'

    headers = {
        "X-RapidAPI-Key": rapid_api_key,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }
    logger.info(f"Направлен запрос к эндпоинту {url}")
    response = requests.request("GET", url, headers=headers, params=querystring)
    if response.status_code == requests.codes.ok:
        logger.info("Получен ответ от api")
        result = json.loads(response.text)
        count_input_hotels = 0
        my_hotels = []
        for hotel in result['data']['body']['searchResults']['results']:
            logger.info(f'Обрабатывается информация по отелю {hotel["name"]} id {hotel["id"]}')
            if 'landmarkIds' in querystring:
                if conversion_dist(hotel['landmarks'][0]['distance']) > data_user['dist_to_center']:
                    logger.info(f'Отель {hotel["name"]} id {hotel["id"]} не подходит по критериям поиска, исключаем')
                    continue
            count_input_hotels += 1
            if int(hotel["starRating"]) != 0:
                star_rating = '🌟' * int(hotel["starRating"])
            else:
                star_rating = 'отсутствует'
            if "guestReviews" in hotel:
                guest_reviews = f'{hotel["guestReviews"]["rating"]} из 10'
            else:
                guest_reviews = 'отсутствует'
            if 'streetAddress' in hotel['address']:
                address = f'{hotel["address"]["streetAddress"]}, {hotel["address"]["locality"]}'
            else:
                address = f'{hotel["address"]["locality"]}, {hotel["address"]["countryName"]}'
            day_price = round(hotel["ratePlan"]["price"]["exactCurrent"])
            total_price = round(day_price * data_user['count_days'])
            distance = conversion_dist(hotel["landmarks"][0]["distance"])
            caption_hotel = f'{hotel["name"]}\n' \
                            f'Количество звезд отеля: {star_rating}   ' \
                            f'Рейтинг отеля: {guest_reviews}\n' \
                            f'📍 {address}\n' \
                            f'Расстояние до центра: {distance} км\n' \
                            f'Цена за сутки: {day_price} $\n' \
                            f'Итоговая цена: {total_price} $\n' \
                            f'https://hotels.com/ho{hotel["id"]}'
            my_hotels.append(f'{hotel["name"]} {total_price}$ https://hotels.com/ho{hotel["id"]}')
            if data_user['photo']:
                medias = []
                photo_hotel = get_photo_hotel(hotel['id'], data_user['count_photo'])
                if not photo_hotel:
                    logger.info(f'Направлено описание отеля {hotel["name"]} id {hotel["id"]} '
                                f'без фото из-за ошибки на стороне properties/get-hotel-photos')
                    bot.send_message(chat_id, caption_hotel)
                    bot.send_message(chat_id, 'ИЗВИНИТЕ, ФОТО НЕ ЗАГРУЖЕНЫ')
                else:
                    for photo in photo_hotel:
                        if len(medias) == 0:
                            medias.append(InputMediaPhoto(photo, caption=caption_hotel))
                        else:
                            medias.append(InputMediaPhoto(photo))
                    logger.info(f'Направлено описание отеля {hotel["name"]} id {hotel["id"]} и его фото')
                    bot.send_media_group(chat_id, medias)
            else:
                logger.info(f'Направлено описание отеля {hotel["name"]} id {hotel["id"]} без фото')
                bot.send_message(chat_id, caption_hotel)
            if count_input_hotels == data_user['count_hotels']:
                break
        if count_input_hotels == 0 or response.text == 'None':
            return False
        my_hotels = '\n'.join(my_hotels)
        return count_input_hotels, my_hotels
    else:
        logger.info(f"Ответ от {url} не получен. Код состояния ответа {response.status_code}")
        return 'Error API'


def get_photo_hotel(hotel_id: str, count_photo: str):

    rapid_api_key = os.getenv('RAPID_API_KEY')
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    querystring = {"id": hotel_id}

    headers = {
        "X-RapidAPI-Key": rapid_api_key,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }
    logger.info(f"Направлен запрос к эндпоинту /get-hotel-photos по id отеля {hotel_id}")
    response = requests.request("GET", url, headers=headers, params=querystring)
    if response.status_code == requests.codes.ok:
        logger.info(f"Получен ответ от {url}")
        result_request = json.loads(response.text)['hotelImages']
        photo = []
        count_photo = int(count_photo)

        if len(result_request) < count_photo:
            count_photo = len(result_request)

        for element in result_request[:count_photo]:
            photo_link = element['baseUrl'].replace('{size}', 'y')
            photo.append(photo_link)
        logger.info(f"Получен ответ от api. Добавлено {len(photo)} фото отеля с id {hotel_id}")
        return photo
    else:
        logger.info(f"Ответ от {url} не получен. Код состояния ответа {response.status_code}")
        return False


def conversion_dist(distance: str) -> float:
    distance = distance.split()
    distance_km = round(1.60934 * float(distance[0]), 1)
    return distance_km
