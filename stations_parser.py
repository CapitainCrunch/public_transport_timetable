__author__ = 'evstrat'
__email__ = 'evstrat.bg@gmail.com'

import requests
import re
from model import save_to_db, Stations
from multiprocessing import Pool

url = 'http://www.proexpress.ru'
base_url = 'http://www.proexpress.ru/stations/?gg&DorogaID=17&page='
data = []
columns = ['code', 'name', 'short_name', 'railway_type', 'railway_office', 'region', 'node']
urls = []

def station_info(url):
    r = requests.get(url)
    content = r.content.decode('cp1251')
    f = re.findall('<td class="stationRowData.*?">(.*?)</td>', content)
    f[3] = re.search('[А-я]+', f[3]).group(0)
    res = dict(zip(columns, f))
    print(res)
    save_to_db(Stations, [res])

for i in range(0, 631, 30):
    r = requests.get(base_url+str(i))
    content = r.content.decode('cp1251')
    # codes = re.findall('<td style="text-align: center">(\d+)</td', content, re.M)
    station_names = re.findall('<a href="(/station/\d+)/">.*?</a>', content)
    for s in station_names:
        urls.append(url+s)


print('cmon pool')

pool = Pool()
results = pool.map(station_info, urls)
