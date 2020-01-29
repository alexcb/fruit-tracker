import psycopg2
import random
from datetime import timedelta, date

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def init_database(user="postgres", password="example", host="mad_database_1", port="5432", database='mad_dev'):
    # first create database
    connection = psycopg2.connect(user=user,
                                  password=password,
                                  host=host,
                                  port=port,
                                  )
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    cursor.execute(f'create database {database};');
    cursor.close()
    connection.close()
    del cursor
    del connection

    # reconnect to database
    connection = psycopg2.connect(user=user,
                                  password=password,
                                  host=host,
                                  port=port,
                                  database=database,
                                  )
    cursor = connection.cursor()

    cursor.execute('create schema mad;')

    cursor.execute(''' 
CREATE TABLE "mad"."commodity" (
    "id" SERIAL PRIMARY KEY NOT NULL,
    "name" varchar(255) UNIQUE NOT NULL
);
''')

    cursor.execute(''' 
CREATE TABLE "mad"."prices" (
    "id" BIGSERIAL PRIMARY KEY NOT NULL,
    "commodity_id" integer REFERENCES "mad"."commodity"(id),
    "price" NUMERIC(16, 2),
    "date" date,
    unique (commodity_id, date)
);
''')
    connection.commit()

    fruits = ('apple', 'orange', 'pear', 'quince')

    for fruit in fruits:
        cursor.execute('INSERT INTO "mad"."commodity" (name) VALUES (%s)', (fruit,));

    connection.commit()

    fruit_mapping = {}
    cursor.execute('SELECT id, name FROM "mad"."commodity"');
    while 1:
        row = cursor.fetchone()
        if row is None:
            break
        fruit_id, fruit_name = row
        fruit_mapping[fruit_name] = fruit_id

    prices = {x: 10*x+5 for x in fruit_mapping.values()}
    d = date(2015, 1, 1)
    for i in range(52*3):
        d += timedelta(7)
        for fruit_id in fruit_mapping.values():

            price = prices[fruit_id]
            price += random.randint(-10,10) / 5
            if price < fruit_id+1:
                price += 50
            prices[fruit_id] = price

            cursor.execute('INSERT INTO "mad"."prices" (commodity_id, price, date) VALUES (%s, %s, %s)', (fruit_id, price, d));

    connection.commit()

    cursor.close()
    connection.close()


if __name__ == '__main__':
    init_database()
