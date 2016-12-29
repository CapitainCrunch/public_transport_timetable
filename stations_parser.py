__author__ = 'evstrat'
__email__ = 'evstrat.bg@gmail.com'

import re
from model import save_to_db, Stations

url = 'http://www.proexpress.ru'
base_url = 'https://rasp.yandex.ru/city/213/direction?direction=msk'
data = []
columns = ['code', 'name', 'railway_type']
urls = []

directions = {
              'Белорусское': 'bel',
              'Горьковское': 'gor',
              'Казанское': 'kaz',
              'Киевское': 'kiv',
              'Курское': 'kur',
              'Ленинградское': 'len',
              'МЦК: Московское центральное кольцо (МКЖД)': 'mkzd',
              'Павелецкое': 'pav',
              'Рижское': 'riz',
              'Савёловское': 'sav',
              'Ярославское': 'yar',
              'Кольцевое': 'kol'
              }

html_code = '<a class="b-link" href="/station/9601663?type=suburban&amp;direction=msk_bel&amp;span=schedule">Ильинское</a>'



def station_info(data):
    url, direction = data
    content = open(url, encoding='utf8').read()
    data = re.findall('<a class="b-link" href="/station/(\d+)\?type=suburban&amp;direction=msk_....?&amp;span=schedule">(.*?)</a>', content)
    to_save = []
    for code, name in data:
        if 'img' not in name:
            to_save.append(dict(zip(columns, [code, name.replace('ё', 'е'), direction])))
    save_to_db(Stations, to_save)

for k, v in directions.items():
    print(k + ' gogogo')
    station_info(('pages/{}.html'.format(v), k))
    print('ok with ' + k)
