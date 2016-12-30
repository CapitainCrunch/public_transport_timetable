import pymysql
from config import MYSQL_CONN

class MySQLSelect():
    def __init__(self, sql):
        self.sql = sql

    def fetch_all(self):
        connection = pymysql.connect(**MYSQL_CONN)
        cur = connection.cursor()
        cur.execute(self.sql)
        result = cur.fetchall()
        connection.close()
        return result

    def fetch_one(self):
        connection = pymysql.connect(**MYSQL_CONN)
        cur = connection.cursor()
        cur.execute(self.sql)
        connection.close()
        result = cur.fetchone()
        return result
