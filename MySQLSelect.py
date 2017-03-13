import pymysql
from config import MYSQL_CONN


class MySQLSelect(object):
    def __init__(self, sql):
        self.connection = pymysql.connect(**MYSQL_CONN)
        self.cursor = self.connection.cursor()
        self.sql = sql

    def execute(self):
        self.cursor.execute(self.sql)
        self.connection.commit()
        self.connection.close()

    def fetchall(self):
        self.cursor.execute(self.sql)
        self.connection.close()
        return self.cursor.fetchall()

    def fetchone(self):
        self.cursor.execute(self.sql)
        self.connection.close()
        return self.cursor.fetchone()
