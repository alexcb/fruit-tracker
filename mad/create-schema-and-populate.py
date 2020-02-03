#!/usr/bin/python3
import psycopg2
import random
from datetime import timedelta, date

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from webapp.auth import create_user
from webapp.commodity import create_new_commodity


def init_database(user="postgres", password="example", host="mad_database_1", port="5432", database='mad_dev'):
    print('creating db')
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

    print('creating schema')
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
CREATE TABLE "mad"."users" (
    "id" SERIAL PRIMARY KEY NOT NULL,
    "email" varchar(255) UNIQUE NOT NULL,
    "salt" varchar(255) NOT NULL,
    "password" varchar(255) NOT NULL,
    "active" BOOLEAN NOT NULL,
    "admin" BOOLEAN NOT NULL
);
''')

    cursor.execute(''' 
CREATE TABLE "mad"."sessions" (
    "sid" varchar(255) PRIMARY KEY NOT NULL,
    "user_id" integer REFERENCES "mad"."users"(id),
    "created" timestamp without time zone,
    "last_active" timestamp without time zone,
    unique (user_id)
);
''')

    cursor.execute(''' 
CREATE TABLE "mad"."commodity" (
    "id" SERIAL PRIMARY KEY NOT NULL,
    "name" varchar(255) UNIQUE NOT NULL
);
''')

    cursor.execute(''' 
CREATE TABLE "mad"."commodity_attributes" (
    "id" SERIAL PRIMARY KEY NOT NULL,
    "commodity_id" integer REFERENCES "mad"."commodity"(id),
    "attribute_key" varchar(255) NOT NULL,
    "attribute_value" varchar(255) NOT NULL,
    unique (commodity_id, attribute_key)
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

    create_user(cursor, 'admin', 'admin', True)
    create_user(cursor, 'user', 'user', False)

    fruits = [
        ('apple',       {'sweet': 'medium', 'medium': 'fresh'}),
        ('orange',      {'sweet': 'high',   'medium': 'fresh'}),
        ('pear',        {'sweet': 'high',   'medium': 'fresh'}),
        ('quince',      {'sweet': 'low',    'medium': 'fresh'}),
        ('apple (dry)', {'sweet': 'medium', 'medium': 'dry'}),
        ('apple (juice)', {'sweet': 'high', 'medium': 'juice'}),
        ]

    fruit_mapping = {}
    for (fruit, attributes) in fruits:
        fruit_mapping[fruit] = create_new_commodity(cursor, fruit, attributes)

    connection.commit()

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
