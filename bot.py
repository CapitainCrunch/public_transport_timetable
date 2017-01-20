import os
import time
from logging import log, INFO, basicConfig
import requests
import logging
from telegram import ReplyKeyboardMarkup, ParseMode, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, RegexHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from config import ALLTESTS, YA_API_KEY, PTT, transport_types, GOOGLE_API_KEY, GOOGLE_MAPS_DIRECTIONS_API_URL, YA_GEOCODER_URL
from model import Users, Stations, Favourites, DoesNotExist, after_request_handler, before_request_handler
from datetime import datetime as dt
from datetime import timedelta
from emoji import emojize
from DLdistance import DLdistance
from MySQLSelect import MySQLSelect
import sys

FIRST, SECOND, THIRD, FORTH, FIFTH, FAV, DEL_FAV = range(7)
user_data = dict()
DATE_FORMAT = '%Y-%m-%d'
# start_keyboard = [['Электричка'], ['Маршрут']]
start_keyboard = [['Электричка']]


def do_google_request(**additional_params):
    params = {
        'region': 'ru',
        'units': 'metric',
        'key': GOOGLE_API_KEY,
        'language': 'ru',
        'transit_mode': 'rail',
        'mode': 'transit'
    }

    params.update(additional_params)

    r = requests.get(GOOGLE_MAPS_DIRECTIONS_API_URL, params=params)
    resp = r.json()
    return resp


def make_predictions(station, **kwargs):
    sql = None
    dep_station_like = None
    railway = kwargs.get('railway')
    if railway:
        sql = 'select name from stations where lower(name) like "{}%" and railway_type = "{}" order by name'
        dep_station_like = MySQLSelect(sql.format(station, railway)).fetch_all()
    else:
        sql = 'select name from stations where lower(name) like "{}%" order by name'
        dep_station_like = MySQLSelect(sql.format(station)).fetch_all()
    keyboard = []
    if dep_station_like:
        for p in dep_station_like:
            p, = p
            keyboard.append([p])
        return keyboard
    predictions = {}
    before_request_handler()
    all_stations = (Stations.select(Stations.name)).distinct().execute()
    after_request_handler()
    station_names = [s.name for s in all_stations]
    for pstation in station_names:
        distance = DLdistance(pstation, station).distance()
        if distance <= 3:
            if distance not in predictions:
                predictions[distance] = []
            predictions[distance].append(pstation)
    for i in range(1, 4):
        presumable_stations = predictions.get(i)
        if presumable_stations:
            for p in presumable_stations:
                keyboard.append([p])
    return keyboard


def compile_msg_from_request(r_json, count=None):
    msg = '------------'
    c = 0
    if count:
        c = count
    for trains in r_json['threads']:
        dep_time = dt.strptime(trains['departure'], '%Y-%m-%d %H:%M:%S')
        arr_time = dt.strptime(trains['arrival'], '%Y-%m-%d %H:%M:%S')
        lambda_time = dep_time - dt.now()
        m, s = divmod(lambda_time.seconds, 60)
        h, m = divmod(m, 60)
        if dep_time > dt.now():
            if c <= 5 or dep_time < dt.now() + timedelta(hours=1.5):
                if h:
                    msg += '\n<i>Уходит в</i><b> ' + dep_time.strftime('%H:%M') + '</b> (через <i>{} ч {}</i> мин.)'.format(h, m)
                else:
                    msg += '\n<i>Уходит в</i><b> ' + dep_time.strftime('%H:%M') + '</b> (через <i>{}</i> мин.)'.format(m)
                msg += '\n<i>Приезжает в</i><b> ' + arr_time.strftime('%H:%M') + '</b>'
                msg += '\n<i>В пути примерно</i><b> ' + str(int(trains['duration'] / 60)) + '</b> минут'
                if trains['stops']:
                    msg += '\n<i>Остановки:</i><b> ' + trains['stops'] + '</b>'
                msg += '\n------------'
                c += 1

    return (msg, c)


def request_route(from_code, to_code):
    params = {'apikey': YA_API_KEY,
              'format': 'json',
              'from': 's'+from_code,
              'to': 's'+to_code,
              'lang': 'ru',
              'transport_types': 'suburban',
              'date': dt.now().strftime(DATE_FORMAT)}

    api_url = 'https://api.rasp.yandex.net/v1.0/search/'
    r = requests.get(api_url, params=params).json()
    msg, count = compile_msg_from_request(r)
    if count < 5:
        next_day = (dt.now() + timedelta(days=1)).strftime(DATE_FORMAT)
        params.update({'date': next_day})
        r = requests.get(api_url, params=params).json()['threads']
        msg, count = compile_msg_from_request(r, count=count)
    return msg


# ==================================== BOT PART ====================================

def start(bot, update):
    username = update.message.from_user.username
    name = update.message.from_user.first_name
    uid = update.message.from_user.id
    bot.sendMessage(uid, 'Выбери тип транспорта',
                    reply_markup=ReplyKeyboardMarkup((start_keyboard), resize_keyboard=True))
    try:
        before_request_handler()
        Users.get(Users.telegram_id == uid)
    except DoesNotExist:
        Users.create(telegram_id=uid, username=username, name=name)
    after_request_handler()
    return ConversationHandler.END


def is_from_favourites(bot, update):
    log(INFO, update)
    uid = update.message.from_user.id
    bot.sendMessage(uid, 'Я подскажу расписание на ближайшие 1.5 часа. Выбери как будем искать', reply_markup=ReplyKeyboardMarkup((['Избранное'], ['Поиск'], ['Назад'])))
    return FIRST


def process_favourites(bot, update):
    log(INFO, update)
    uid = update.message.from_user.id
    message = update.message.text
    if message == '/delete':
        bot.sendMessage(uid, 'Выбери направление, которое хочешь удалить')
        return DEL_FAV
    if message == 'Назад':
        bot.sendMessage(uid, 'Выбери как будем искать', reply_markup=ReplyKeyboardMarkup((['Избранное'], ['Поиск'], ['Назад'])))
        return FIRST
    from_station, to_station = message.split(emojize(':black_rightwards_arrow:'))
    from_code, to_code = MySQLSelect('''SELECT s_from.code, s_to.code
                            FROM stations s_from
                            join stations s_to
                              on s_from.railway_type = s_to.railway_type
                            where s_from.name = "{}" and s_to.name = "{}"'''.format(from_station.strip(), to_station.strip())).fetch_one()
    msg = request_route(from_code, to_code)
    bot.sendMessage(uid, msg, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardMarkup((['Избранное'], ['Поиск'], ['Назад'])))
    return FIRST


def ask_departure_station(bot, update):
    log(INFO, update)
    uid = update.message.from_user.id
    message = update.message.text
    if message == 'Поиск':
        bot.sendMessage(uid, 'Введи название станции, с которой поедешь. Можно не дописывать, '
                             'например по <b>домод</b> я подскажу тебе станцию <b>Домодедово</b>',
                        parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardMarkup([['Назад']]))
        return SECOND
    if message == 'Избранное':
        keyboard = []
        routes = MySQLSelect('select direction from favourites where user_id = {}'.format(uid)).fetch_all()
        if routes:
            for r in routes:
                from_code, to_code = r[0].split('|')
                before_request_handler()
                from_station = Stations.get(Stations.code == from_code)
                to_station = Stations.get(Stations.code == to_code)
                after_request_handler()
                butt = from_station.name + ' ' + emojize(':black_rightwards_arrow:') + ' ' + to_station.name
                keyboard.append([butt])
            keyboard.append(['Назад'])
            bot.sendMessage(uid, 'Выбирай из избранных, если хочешь удалить из выбранных, то нажми сюда {} /delete'.format(emojize(':black_rightwards_arrow:')),
                            reply_markup=ReplyKeyboardMarkup(keyboard))
            return FAV
        else:
            bot.sendMessage(uid, 'В избранных пусто', reply_markup=ReplyKeyboardMarkup((['Избранное'], ['Поиск'], ['Назад'])))

    if message == 'Назад':
        bot.sendMessage(uid, 'Выбери тип транспорта. Я подскажу расписание на ближайшие 3 часа',
                        reply_markup=ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=True))
        return ConversationHandler.END


def ask_arrival_station(bot, update):
    log(INFO, update)
    message = update.message.text.lower()
    uid = update.message.from_user.id
    if message == 'назад':
        bot.sendMessage(uid, 'Выбери как будем искать', reply_markup=ReplyKeyboardMarkup((['Избранное'], ['Поиск'], ['Назад'])))
        return FIRST
    before_request_handler()
    dep_station = MySQLSelect('select code, name, railway_type from stations where lower(name) = "{}"'.format(message)).fetch_all()
    if user_data.get(uid):
        if user_data.get(uid).get('is_second_try'):
            s, r = message.split()
            dep_station = MySQLSelect('select code, name, railway_type from stations where lower(name) = "{}" and railway_type = "{}"'.format(s, r)).fetch_all()
    after_request_handler()
    if dep_station:
        if len(dep_station) == 1:
            code, name, railway = dep_station[0]
            user_data[uid] = {'from': {'code': code, 'railway': railway, 'name': name}}
            arr_station = MySQLSelect('select name from stations where railway_type = "{}" order by name'.format(railway)).fetch_all()
            bot.sendMessage(uid, 'Ага, у тебя <b>{}</b> направление. Выбери или напиши станцию прибытия'.format(railway),
                            reply_markup=ReplyKeyboardMarkup(arr_station),
                            parse_mode=ParseMode.HTML)
            return THIRD
        else:
            keyboard = []
            for c, s, r in dep_station:
                keyboard.append([s + ' ' + r])
            if not user_data.get(uid) is dict:
                user_data[uid] = {}
            user_data[uid].update([('is_second_try', True)])
            bot.sendMessage(uid, 'Я нашел несколько станций с такими названиями. Выбери нужную',
                            reply_markup=ReplyKeyboardMarkup(keyboard))
    else:
        keyboard = make_predictions(message)
        if keyboard:
            bot.sendMessage(uid,
                            'Такой станции нет, но у меня есть предположения. Посмотри клавиатуру, сверху наиболее предпологаемые варианты',
                            reply_markup=ReplyKeyboardMarkup(keyboard))
        else:
            bot.sendMessage(uid, 'Что-то не могу ничего найти {}\nПопробуй снова'.format(
                emojize(':pensive_face:')))


def send_rzd_route(bot, update):
    log(INFO, update)
    message = update.message.text
    uid = update.message.from_user.id

    from_code = user_data[uid]['from']['code']
    railway = user_data[uid]['from']['railway']

    arr_station = MySQLSelect('select code, name from stations where name = "{}" and railway_type = "{}"'.format(message, railway)).fetch_one()
    if arr_station:
        to_code, name = arr_station
        user_data[uid].update([('to', {'code': to_code, 'name': name})])
        msg = request_route(from_code, to_code)
        bot.sendMessage(uid, msg, parse_mode=ParseMode.HTML)
        time.sleep(2)
        bot.sendMessage(uid, 'Добавить в избранное',
                        reply_markup=ReplyKeyboardMarkup([['Да', 'Нет']]),
                        parse_mode=ParseMode.HTML,
                        disable_notifications=True)
        return FORTH

    else:
        keyboard = make_predictions(message, railway=user_data[uid]['from']['railway'])
        if keyboard:
            bot.sendMessage(uid,
                            'Такой станции нет, но у меня есть предположения. Посмотри клавиатуру. Сверху наиболее предпологаемые варианты',
                            reply_markup=ReplyKeyboardMarkup(keyboard))
        else:
            bot.sendMessage(uid, 'Что-то не могу ничего найти {}\nПопробуй снова'.format(emojize(':pensive_face:')))


def add_to_favourites(bot, update):
    log(INFO, update)
    message = update.message.text
    uid = update.message.from_user.id
    if message == 'Нет':
        bot.sendMessage(uid, 'Обращайся ' + emojize(':winking_face:', use_aliases=True), reply_markup=ReplyKeyboardMarkup((['Избранное'], ['Поиск'], ['Назад'])))
    if message == 'Да':
        from_station = user_data[uid]['from']['code']
        to_station = user_data[uid]['to']['code']
        direction = from_station + '|' + to_station
        try:
            before_request_handler()
            Favourites.get(Favourites.direction == direction)
            bot.sendMessage(uid, 'Такое направление уже есть ' + emojize(':winking_face:'), reply_markup=ReplyKeyboardMarkup((['Избранное'], ['Поиск'], ['Назад'])))
        except DoesNotExist:
            Favourites.create(user=uid, direction=direction)
            bot.sendMessage(uid, 'Добавил ' + emojize(':winking_face:'), reply_markup=ReplyKeyboardMarkup((['Избранное'], ['Поиск'], ['Назад'])))
        after_request_handler()
    del user_data[uid]
    return FIRST


def delete_favourite(bot, update):
    log(INFO, update)
    message = update.message.text
    uid = update.message.from_user.id
    if message == 'Назад':
        bot.sendMessage(uid, 'Выбери как будем искать', reply_markup=ReplyKeyboardMarkup((['Избранное'], ['Поиск'], ['Назад'])))
        return FIRST
    from_station, to_station = message.split(emojize(':black_rightwards_arrow:'))
    from_code, to_code = MySQLSelect('''SELECT s_from.code, s_to.code
                            FROM stations s_from
                            join stations s_to
                              on s_from.railway_type = s_to.railway_type
                            where s_from.name = "{}" and s_to.name = "{}"'''.format(from_station.strip(), to_station.strip())).fetch_one()
    s = from_code + '|' + to_code
    Favourites.delete().where(Favourites.direction == s).execute()
    bot.sendMessage(uid, 'Удалил', reply_markup=ReplyKeyboardMarkup((['Избранное'], ['Поиск'], ['Назад']), one_time_keyboard=True))
    return FIRST



if __name__ == '__main__':
    updater = None
    token = None
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        token = sys.argv[-1]
        if token.lower() == 'ptt':
            updater = Updater(PTT)
            basicConfig(filename=BASE_DIR + '/out.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    else:
        updater = Updater(ALLTESTS)
        basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    dp = updater.dispatcher

    station = ConversationHandler(
        entry_points=[RegexHandler('^Электричка$', is_from_favourites)],
        states={FIRST: [MessageHandler(Filters.text, ask_departure_station)],
                SECOND: [MessageHandler(Filters.text, ask_arrival_station)],
                THIRD: [MessageHandler(Filters.text, send_rzd_route)],
                FORTH: [RegexHandler('(Да)|(Нет)', add_to_favourites)],
                FAV: [RegexHandler('.*', process_favourites)],
                DEL_FAV: [MessageHandler(Filters.text, delete_favourite)]},
        fallbacks=[CommandHandler('start', start)]
    )

    dp.add_handler(station)
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(RegexHandler('.*', start))
    updater.start_polling()
    updater.idle()
