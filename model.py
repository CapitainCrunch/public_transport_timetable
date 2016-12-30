from peewee import *
from datetime import datetime
from config import MYSQL_CONN

db = MySQLDatabase(**MYSQL_CONN)

def before_request_handler():
    db.connect()

def after_request_handler():
    db.close()

class BaseModel(Model):
    class Meta:
        database = db

class Users(BaseModel):
    id = PrimaryKeyField()
    telegram_id = IntegerField(unique=1)
    username = CharField(default=None)
    name = CharField()
    dt = DateTimeField(default=datetime.now())


class Stations(BaseModel):
    id = PrimaryKeyField()
    code = CharField(default=None)
    name = CharField(default=None)
    railway_type = CharField(default=None)
    dt = DateTimeField(default=datetime.now())


class Favourites(BaseModel):
    id = PrimaryKeyField()
    user = ForeignKeyField(Users, to_field='telegram_id')
    direction = CharField(default=None)
    dt = DateTimeField(default=datetime.now())


def init_db():
    tables = [Users, Stations, Favourites]
    for t in tables:
        if t.table_exists():
            t.drop_table()
        t.create_table()


def save_to_db(scheme_name, data):
    """
    Initialize table.
    Batch insert rows
    :param texts_stats:
    :return:
    """

    with db.atomic():
        scheme_name.insert_many(data).upsert().execute()
    return True


if __name__ == '__main__':
    init_db()
    print('Таблицы создал')