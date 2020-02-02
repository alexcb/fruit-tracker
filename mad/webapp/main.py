import flask
from flask import Flask, escape, request, Response, redirect, url_for, make_response
import psycopg2
import json
import datetime
import io
import csv
import tenjin
from tenjin.helpers import *
from tenjin.html import *


from functools import wraps


from .database import database
from .auth import auth_user, validate_sid, create_new_session


app = Flask(__name__)

engine = tenjin.Engine(path=['templates'])

@app.before_request
def before_request():
    sid = request.cookies.get('sid')
    app.logger.info(f'hello: {sid}')

    with database() as (connection, cursor):
        flask.g.user_email, flask.g.user_admin = validate_sid(cursor, sid)
        app.logger.info(f'sid {sid}; user {flask.g.user_email} {flask.g.user_admin}')


@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


def get_data(commodity_id):
    with database() as (connection, cursor):
        cursor.execute('SELECT date, price FROM "mad"."prices" WHERE commodity_id = %s ORDER BY date', (commodity_id,));

        data = []
        while 1:
            row = cursor.fetchone()
            if row is None:
                break
            data.append(row)

        return data

def get_commodity_ids_and_attributes():
    with database() as (connection, cursor):
        cursor.execute('SELECT c.id, c.name, ca.attribute_key, ca.attribute_value FROM mad.commodity_attributes ca LEFT JOIN mad.commodity c ON (ca.commodity_id = c.id)');

        commodities = {}
        while 1:
            row = cursor.fetchone()
            if row is None:
                break
            commodity_id, commodity_name, k, v = row

            if commodity_id not in commodities:
                commodities[commodity_id] = {
                    'name': commodity_name,
                    'attributes': {},
                    }
            assert commodities[commodity_id]['name'] == commodity_name
            commodities[commodity_id]['attributes'][k] = v

        return commodities

def get_commodity_ids():
    '''returns (dict mapping IDs->name, dict mapping names->ID)'''

    with database() as (connection, cursor):
        cursor.execute('SELECT id, name FROM "mad"."commodity"');

        commodity_ids = {}
        commodity_names = {}
        while 1:
            row = cursor.fetchone()
            if row is None:
                break
            commodity_id, commodity_name = row
            commodity_ids[commodity_id] = commodity_name
            commodity_names[commodity_name] = commodity_id

        return commodity_ids, commodity_names

def get_all_data():
    with database() as (connection, cursor):
        data = {}

        cursor.execute('SELECT c.name, p.date, p.price FROM "mad"."prices" p LEFT JOIN "mad"."commodity" c ON (p.commodity_id = c.id)');

        data = {}
        dates = set()
        while 1:
            row = cursor.fetchone()
            if row is None:
                break
            commodity_name, date, price = row
            if commodity_name not in data:
                data[commodity_name] = {}
            data[commodity_name][date] = price
            dates.add(date)

        return data, sorted(dates)

def date_to_epoch_ms(x):
    return int(datetime.datetime.combine(x, datetime.datetime.min.time()).timestamp() * 1000)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not flask.g.user_email:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET'])
def login_form():
    context = {
        'sid': flask.g.user_email,
        }
    return engine.render('login.pyhtml', context)

@app.route('/login', methods=['POST'])
def login_handler():
    email = request.form.get('email', '')
    password = request.form.get('password', '')

    with database() as (connection, cursor):
        user_id, success = auth_user(cursor, email, password)

        if not success:
            app.logger.info('login failed')

            # TODO display page with error
            response = make_response(redirect('/login'))
            response.set_cookie('sid', '', expires=0)
            return response

        sid = create_new_session(cursor, user_id)
        connection.commit()

    app.logger.info('login success')

    response = make_response(redirect('/'))
    response.set_cookie('sid', sid)
    return response

@app.route('/logout')
def logout_handler():
    global logged_in_user
    logged_in_user = None
    response = make_response(redirect('/'))
    response.set_cookie('sid', '', expires=0)
    return response

@app.route('/')
@login_required
def hello():

    commodities = get_commodity_ids_and_attributes()

    _, commodity_names = get_commodity_ids()
    data = []
    for commodity_name, commodity_id in commodity_names.items():
        price_data = get_data(commodity_id)
        data.append({
            'name': commodity_name,
            't': [date_to_epoch_ms(x) for (x, _) in price_data],
            'y': [float(x) for (_, x) in price_data],
            })

    context = {
        'user_email': flask.g.user_email,
        'is_admin': flask.g.user_admin,
        'data': json.dumps(data),
        'commodities': json.dumps(commodities),
        }
    return engine.render('dashboard.pyhtml', context)


@app.route('/data')
def data():
    data, dates = get_all_data()
    keys = sorted(data.keys())
    rows = [
        ['commodity'] + dates
            ]
    for k in keys:
        row = [k]
        for date in dates:
            price = data[k].get(date)
            row.append(price)
        rows.append(row)

    # change to csv
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    for row in rows:
        writer.writerow(row)
    csv_data = output.getvalue()

    return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition":
                     "attachment; filename=fruit_prices.csv"})

@app.route('/upload')
def upload():
    return '''
<html>
<body>

<i>This page allows an admin to update the data based on a previously <a href="/data">downloaded</a> CSV file.</i>

<br/> <br/>

<form method="post" action="/upload2" enctype="multipart/form-data">
  <input type="file" name="csvdata" accept=".csv"><br/>
  <input type="submit" value="Upload">
</form>
</body>
</html>
    '''

@app.route('/upload2', methods=['POST'])
def upload_handler():
    commodity_ids, commodity_names = get_commodity_ids()
    raw_data = request.files['csvdata'].read().decode('utf8')
    reader = csv.reader(io.StringIO(raw_data))
    dates = []
    data = {}
    for i, row in enumerate(reader):
        if i == 0:
            for j, cell in enumerate(row):
                if j == 0:
                    if cell != 'commodity':
                        return 'csv file invalid; first row cell should be "commodity"'
                else:
                    try:
                        date = datetime.datetime.strptime(cell, "%Y-%m-%d")
                    except:
                        return f'csv file invalid; failed to parse date "{cell}" in row 0 cell {j}'
                    dates.append(date)
        else:
            commodity_name = row[0]
            if commodity_name not in commodity_names:
                return f'unknown commodity "{commodity_name}" in row {i}'
            prices = row[1:]
            for j, price in enumerate(prices):
                try:
                    if price == "":
                        prices[j] = None
                    else:
                        prices[j] = float(price)
                except:
                    return f'failed to parse price in row {i} coll {j} with value "{price}"'
            data[commodity_name] = prices

    with database() as (connection, cursor):
        for commodity_name, prices in data.items():
            commodity_id = commodity_names[commodity_name]
            assert len(dates) == len(prices)
            for date, price in zip(dates, prices):
                cursor.execute('INSERT INTO "mad"."prices" (commodity_id, date, price) VALUES (%s, %s, %s) ON CONFLICT (commodity_id, date) DO UPDATE SET price = excluded.price', (commodity_id, date, price));

        connection.commit()

    return 'updated database'


if __name__ == '__main__':
   app.run()

