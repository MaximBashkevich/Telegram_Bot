from peewee import SqliteDatabase, Model, CharField, DateTimeField, TextField, IntegerField, BooleanField
from datetime import datetime
import os


path = os.path.join('database/bot_data.db')
db = SqliteDatabase(path)


class UserBot(Model):
    class Meta:
        database = db
        db_table = 'UsersBot'

    date_request = DateTimeField()
    user_id = CharField(max_length=20)
    user_name = CharField(max_length=50)
    command = CharField(max_length=10)
    city = CharField(max_length=30)
    count_hotels = IntegerField()
    period = CharField(max_length=30)
    photo = BooleanField()
    count_photo = IntegerField()
    hotels = TextField()
    distance = CharField(max_length=5, default='')
    budget = CharField(max_length=10, default='')


def save_data(data_user: dict, hotels: str) -> None:
    if data_user['command'] == 'bestdeal':
        UserBot(
            date_request=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            user_id=data_user['id'],
            user_name=data_user['name'],
            command=data_user['command'],
            city=data_user['city'],
            count_hotels=data_user['count_hotels'],
            period=f"{data_user['check_in']}\t{data_user['check_out']}",
            photo=data_user['photo'],
            count_photo=data_user['count_photo'],
            hotels=hotels,
            distance=data_user['dist_to_center'],
            budget=f"{data_user['min_price']}-{data_user['max_price']}$"
        ).save()
    else:
        UserBot(
            date_request=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            user_id=data_user['id'],
            user_name=data_user['name'],
            command=data_user['command'],
            city=data_user['city'],
            count_hotels=data_user['count_hotels'],
            period=f"{data_user['check_in']}\t{data_user['check_out']}",
            photo=data_user['photo'],
            count_photo=data_user['count_photo'],
            hotels=hotels,
        ).save()


def get_history(user_id: int) -> str:
    requests = [entry for entry in UserBot.select().where(UserBot.user_id == user_id)]
    if len(requests) != 0:
        history = []
        for entry in requests:
            history.append(
                f"\n?????????????? - {entry.command}\n"
                f"???????? ?? ??????????: {entry.date_request}\n"
                f"?????????????????? ????????????:\n"
                f"??????????: {entry.city}\n"
                f"???????????????????? ????????????: {entry.count_hotels}\n"
                f"???????????? ????????????????????: {entry.period}\n"
                f"???????????????????? ????????????????????: {entry.count_photo}\n"
            )
            if entry.command == 'bestdeal':
                history.append(
                    f"???????????? - {entry.budget}\n"
                    f"???????????????????? ???? ???????????? ???????????? - {entry.distance}\n"
                )
            history.append(
                f"?????????????????? ????????????:\n{entry.hotels}\n"
            )
        history = ''.join(history)
        return history
    else:
        return '(?????? ????????????)'


def delete_history(user_id: int) -> None:
    lines = [line for line in UserBot.select().where(UserBot.user_id == user_id)]
    for line in lines:
        line.delete_instance()
