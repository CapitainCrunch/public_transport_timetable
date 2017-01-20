"""
code to get route steps from A to B in text
"""

# def ask_departure_point(bot, update):
#     log(INFO, update)
#     uid = update.message.from_user.id
#     bot.sendMessage(uid, 'Откуда прокладывать маршрут? Можешь набрать адрес или отправить мне геолокацию',
#                     reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text='Отправить геолокацию', request_location=True,
#                                                                       one_time_keyboard=True)], ['Назад']]))
#     return FIRST


# def ask_arrival_point(bot, update):
#     log(INFO, update)
#     uid = update.message.from_user.id
#     message = update.message.text
#     msg = ''
#     if not message:
#         longitude = update.message.location.longitude
#         latitude = update.message.location.latitude
#         r = requests.get(YA_GEOCODER_URL, params={'geocode': '{},{}'.format(longitude, latitude),
#                                                   'format': 'json'
#                                                   })
#         arr = r.json()['response']['GeoObjectCollection']['featureMember']
#         if arr:
#             pos_name = arr[0]['GeoObject']['name']
#             message = pos_name
#             msg = 'Кажется, твой адрес <b>{}</b>.\nА куда направимся?'.format(pos_name)
#     elif message == 'Назад':
#         bot.sendMessage(uid, 'Выбери тип транспорта',
#                     reply_markup=ReplyKeyboardMarkup((start_keyboard), resize_keyboard=True))
#         return ConversationHandler.END
#     else:
#         msg = 'А куда направимся?'
#
#     bot.sendMessage(uid, msg, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
#     user_data[uid] = {'departure_point': message}
#     return SECOND


# def get_arrival_and_route(bot, update):
#     uid = update.message.from_user.id
#     message = update.message.text
#     departure_point = user_data.get(uid).get('departure_point')
#     params = {'origin': departure_point,
#               'destination': message}
#     resp = do_google_request(**params)
#     warnings = '\n'.join(x for x in resp['routes'][0]['warnings'])
#     duration = resp['routes'][0]['legs'][0]['duration']['text']
#     msg = '{}\n\nПуть займет примерно <b>{}</b>'.format(warnings, duration)
#     all_steps = []
#     steps = resp['routes'][0]['legs'][0]['steps']
#     for step in steps:
#         arr = []
#         point = step['html_instructions']
#         if point is None:
#             continue
#         dist = step['distance']['text']
#         travel_mode = step['travel_mode']
#         arr.append({'point': point,
#                     'distance': dist,
#                     'duration': duration,
#                     'travel_mode': travel_mode})
#         if step.get('steps'):
#             for s in step['steps']:
#                 point = s.get('html_instructions')
#                 if point is None:
#                     continue
#                 dist = s['distance']['text']
#                 duration = s['duration']['text']
#                 travel_mode = s['travel_mode']
#                 arr.append({'point': point,
#                             'distance': dist,
#                             'duration': duration,
#                             'travel_mode': travel_mode})
#         all_steps.extend(arr)
#     reply_markup = [InlineKeyboardButton(emojize(':squared_ok:'), callback_data='next')]
#     bot.sendMessage(uid, msg, reply_markup=InlineKeyboardMarkup([reply_markup]), parse_mode=ParseMode.HTML)
#     user_data[uid] = {'steps': all_steps,
#                       'state': -1}
#     return ConversationHandler.END


# def get_next_step(bot, update):
    # query = update.callback_query
    # uid = query.from_user.id
    # text = query.data
    # steps = user_data[uid]['steps']
    # new_reply_markup = [[InlineKeyboardButton(emojize(':black_right-pointing_double_triangle:'), callback_data='next')]]
    # if text == 'get_train':
    #     update = {'message': {'from_user': uid}, 'text': text}
    #     ask_departure_station(bot, update)
    #
    # if text == 'back':
    #     bot.sendMessage(uid, 'Выбери тип транспорта',
    #                 reply_markup=ReplyKeyboardMarkup((start_keyboard), resize_keyboard=True))
    #     return
    #
    # if user_data[uid]['state'] < len(steps)-1:
    #     if text == 'next':
    #         user_data[uid]['state'] += 1
    #     else:
    #         user_data[uid]['state'] -= 1
    # elif user_data[uid]['state'] == len(steps)-1 and text == 'previous':
    #     user_data[uid]['state'] -= 1
    #
    # uid_state = user_data[uid]['state']
    #
    # if uid_state >= 0 and uid_state < len(steps) - 1:
    #     new_reply_markup[0].insert(0, InlineKeyboardButton(emojize(':black_left-pointing_double_triangle:'), callback_data='previous'))
    # elif uid_state == len(steps)-1:
    #     new_reply_markup = [InlineKeyboardButton(emojize(':black_left-pointing_double_triangle:'), callback_data='previous')]
    #
    # point = steps[uid_state]['point']
    # is_train = re.findall('Пригородный электропоезд в направлении\:\s?(.+)', str(point), re.U|re.I)
    # if is_train:
    #     pass
    #     # new_reply_markup.append([InlineKeyboardButton(emojize(':station:'), callback_data='get_train')])
    # dist = steps[uid_state]['distance']
    # duration = steps[uid_state]['duration']
    # travel_mode = steps[uid_state]['travel_mode']
    # if travel_mode == 'WALKING':
    #     msg = '{}\nЭто примерно <i>{}</i>\nЗаймет <i>{}</i>'.format(point, dist, duration)
    # else:
    #     msg = '{}\nЭто займет примерно <i>{}</i>'.format(point, duration)
    # new_reply_markup.append([InlineKeyboardButton(emojize(':back_with_leftwards_arrow_above:'), callback_data='back')])
    # bot.editMessageText(text=msg, chat_id=uid, message_id=query.message.message_id,
    #                     parse_mode=ParseMode.HTML,
    #                     reply_markup=InlineKeyboardMarkup(new_reply_markup))


# route = ConversationHandler(
#     entry_points=[RegexHandler('^Маршрут', ask_departure_point)],
#     states={FIRST: [MessageHandler(Filters.text | Filters.location, ask_arrival_point)],
#             SECOND: [MessageHandler(Filters.text, get_arrival_and_route)]},
#     fallbacks=[CommandHandler('start', start)]
# )

# dp.add_handler(route)
# dp.add_handler(CallbackQueryHandler(get_next_step))