from telegram import ReplyKeyboardMarkup, ParseMode, Emoji, ReplyKeyboardHide, KeyboardButton
from telegram.ext import Updater, CommandHandler, RegexHandler, MessageHandler, Filters, ConversationHandler
from config import ALLTESTS, ADMIN_ID, YA_API_KEY, PTT, transport_types, transport_types_rev, GOOGLE_API_KEY
import requests
import logging
import json
from model import Stations, save_to_db, DoesNotExist, fn
from datetime import datetime as dt
from datetime import timedelta
import re
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
# logging.basicConfig(filename='logs.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


SECOND, THIRD = range(2)

user_data = dict()

def start(bot, update):
    print(update)
    uid = update.message.from_user.id
    bot.sendMessage(uid, 'Отправь мне свою геолокацию, чтобы я нашел ближайшие станции',
                    reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text='Отправить геолокацию', request_location=True)]]))
    return ConversationHandler.END


def get_nearest_stations(bot, update):
    print(update)
    nearest_station = 'https://api.rasp.yandex.net/v1.0/nearest_stations/?apikey={key}&format=json&lat={lat}&lng={lon}&lang=ru'
    uid = update.message.from_user.id
    lon = update.message.location.longitude
    lat = update.message.location.latitude
    keyboard = set()
    r = requests.get(nearest_station.format(key=YA_API_KEY,
                                            lon=lon,
                                            lat=lat))
    r = json.loads(r.content.decode('utf8'))
    print(r)
    stations = r.get('stations')
    _data = []
    if stations:
        if uid not in user_data:
            user_data[uid] = []
        user_data[uid] = stations
        for s in stations:
            keyboard.add(s['transport_type'])
            _data.append(dict(title=s['title'],
                              lat=s['lat'],
                              lon=s['lng'],
                              station_type=s['station_type'],
                              code=s['code'],
                              type=s['type'],
                              transport_type=s['transport_type'],
                              short_title=s['short_title'] if s['short_title'] else None,
                              popular_title=s['popular_title'] if s['popular_title'] else None))
        save_to_db(Stations, _data)
        bot.sendMessage(uid, 'Выбери тип транспорта', reply_markup=ReplyKeyboardMarkup([[transport_types[k]] for k in sorted(keyboard)]))
        return SECOND


#TODO: в клавиатуре писать сколько километров до станции

def choose_transport_type(bot, update):
    uid = update.message.from_user.id
    message = transport_types_rev[update.message.text]
    stations = []
    for s in user_data[uid]:
        if s['transport_type'] == message:
            stations.append(s['title'] if not s['popular_title'] else s['popular_title'])
    bot.sendMessage(uid, 'Вот названия остановок', reply_markup=ReplyKeyboardMarkup([[s] for s in sorted(stations)]))
    return THIRD


def send_map(bot, update):
    uid = update.message.from_user.id
    message = update.message.text
    if message == 'Назад':
        return ConversationHandler.END
    try:
        check_aliases = (Stations.select().where((Stations.title == message) |
                                                 (Stations.popular_title == message))).execute()
        alias = [c for c in check_aliases]
        if alias:
            station = alias[0]
            lat = station.lat
            lon = station.lon
            bot.sendLocation(uid, lat, lon, disable_notification=True)
            bot.sendMessage(uid, 'Выслал геометку ' + message)
    except DoesNotExist:
        pass

updater = Updater(PTT)
dp = updater.dispatcher
dp.add_handler(CommandHandler('start', start))

station = ConversationHandler(
    entry_points=[MessageHandler(Filters.location, get_nearest_stations)],
    states={SECOND: [MessageHandler(Filters.text, choose_transport_type)],
            THIRD: [MessageHandler(Filters.text, send_map)]},
    fallbacks=[RegexHandler('^Назад$', start)]
)

dp.add_handler(station)
updater.start_polling()
updater.idle()
