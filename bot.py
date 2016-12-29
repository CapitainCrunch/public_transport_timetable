from telegram import ReplyKeyboardMarkup, ParseMode, Emoji, ReplyKeyboardHide, KeyboardButton
from telegram.ext import Updater, CommandHandler, RegexHandler, MessageHandler, Filters, ConversationHandler
from config import ALLTESTS, ADMIN_ID, YA_API_KEY, PTT, transport_types, transport_types_rev, GOOGLE_API_KEY
import requests
import logging
import json
from model import Stations, Favourites, LastUserChoice, save_to_db, DoesNotExist, fn, after_request_handler, before_request_handler
from datetime import datetime as dt
from datetime import timedelta
import re
import os
from emoji import emojize
from DLdistance import DLdistance

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
# logging.basicConfig(filename='logs.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


SECOND, THIRD = range(2)

user_data = dict()

def start(bot, update):
    print(update)

    uid = update.message.from_user.id
    bot.sendMessage(uid, 'Выбери тип транспорта',
                    reply_markup=ReplyKeyboardMarkup([['Электричка']], one_time_keyboard=True))
    return ConversationHandler.END


def ask_departure_station(bot, update):
    print(update)
    uid = update.message.from_user.id
    bot.sendMessage(uid, 'Введи название станции, с которой поедешь')
    return SECOND


def ask_arrival_station(bot, update):
    print(update)
    message = update.message.text.lower()
    uid = update.message.from_user.id
    before_request_handler()
    try:
        dep_station = Stations.get(fn.lower(Stations.name) == message)
        a = 1
    except DoesNotExist:
        predictions = {}
        all_stations = (Stations.select(Stations.name)).distinct().execute()
        after_request_handler()
        station_names = [s.name for s in all_stations]
        for station in station_names:
            distance = DLdistance(station, message).distance()
            if distance <= 3:
                if distance not in predictions:
                    predictions[distance] = []
                predictions[distance].append(station)
        keyboard = []
        max_long = 0
        for i in range(1, 4):
            presumable_stations = predictions.get(i)
            if presumable_stations:
                keyboard.append([])
                if len(predictions) > max_long:
                    max_long = len(presumable_stations)
        for _ in range(max_long):
            keyboard.append([])

        column = 0
        pos = 0
        for k, v in sorted(predictions.items(), key=lambda x: x[0]):
            for p in v:
                if pos > column:
                    pos = column
                if k == 1:
                    keyboard[pos].append(p)
                    keyboard[pos].append(emojize(":white_small_square:", use_aliases=True))
                    keyboard[pos].append(emojize(":white_small_square:", use_aliases=True))
                    pos += 1
                elif k == 2:
                    keyboard[pos].append(p)
                    keyboard[pos].append(emojize(":white_small_square:", use_aliases=True))
                    keyboard[pos].append(p)
                    pos += 1
                elif k == 3:
                    keyboard[pos].append(emojize(":white_small_square:", use_aliases=True))
                    keyboard[pos].append(emojize(":white_small_square:", use_aliases=True))
                    keyboard[pos].append(p)
                    pos += 1
                column += 1
            column += 1




        bot.sendMessage(uid, 'Такой станции нет, но у меня есть предположения. Посмотри клавиатуру',
                        reply_markup=ReplyKeyboardMarkup(keyboard))
        return
    bot.sendMessage(uid, 'Введи название станции прибытия',
                    reply_markup=ReplyKeyboardMarkup([[]]))
    return THIRD

def get_route(bot, update): pass

updater = Updater(PTT)
dp = updater.dispatcher
dp.add_handler(CommandHandler('start', start))

station = ConversationHandler(
    entry_points=[MessageHandler(Filters.text, ask_departure_station)],
    states={SECOND: [MessageHandler(Filters.text, ask_arrival_station)],
            THIRD: [RegexHandler('^/.*?', get_route)]},
    fallbacks=[RegexHandler('^Назад$', start)]
)

dp.add_handler(station)
updater.start_polling()
updater.idle()
