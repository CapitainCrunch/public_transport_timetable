__author__ = 'evstrat'
__email__ = 'evstrat.bg@gmail.com'

import requests
import re
from model import save_to_db, Stations

base_url = 'http://www.proexpress.ru/stations/?gg&DorogaID=17&page='
data = []
for i in range(0, 631, 30):
    columns = ['code', 'name']
    r = requests.get(base_url+str(i))
    content = r.content.decode('cp1251')
    # codes = re.findall('<td style="text-align: center">(\d+)</td', content, re.M)
    station_names = re.findall('<a href="/station/(\d+)/">(.*?)</a>', content)
    for s in station_names:
        res = dict(zip(columns, s))
        data.append(res)
save_to_db(Stations, data)

