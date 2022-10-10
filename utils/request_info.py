def user_input(data_user: dict) -> str:
    items = [f"Город - {data_user['city']}\n"
             f"Количество отелей - {data_user['count_hotels']}\n"
             f"Дата заезда- {data_user['check_in']}\n"
             f"Дата выезда- {data_user['check_out']}"]
    if data_user['photo']:
        items.append(f"Показать {data_user['count_photo']} фото")
    if data_user['command'] == 'bestdeal':
        items.append(f"Расстояние до центра города - {data_user['dist_to_center']} км")
        items.append(f"Бюджет - {data_user['min_price']}-{data_user['max_price']}$")
    text = '\n'.join(items)
    return text
