from flask import Flask, escape, request, Response
import psycopg2
import json
import datetime
import io
import csv


def db_connect(user="postgres", password="example", host="mad_database_1", port="5432", database='mad_dev'):
    connection = psycopg2.connect(user=user,
                                  password=password,
                                  host=host,
                                  port=port,
                                  database=database,
                                  )
    cursor = connection.cursor()
    return connection, cursor

app = Flask(__name__)

def get_data(commodity_id):
    try:
        connection, cursor = db_connect()

        cursor.execute('SELECT date, price FROM "mad"."prices" WHERE commodity_id = %s ORDER BY date', (commodity_id,));

        data = []
        while 1:
            row = cursor.fetchone()
            if row is None:
                break
            data.append(row)

        return data
    finally:
        cursor.close()
        connection.close()

def get_commodity_ids():
    '''returns (dict mapping IDs->name, dict mapping names->ID)'''
    try:
        connection, cursor = db_connect()

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
    finally:
        cursor.close()
        connection.close()

def get_all_data():
    data = {}
    try:
        connection, cursor = db_connect()

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
    finally:
        cursor.close()
        connection.close()

def date_to_epoch_ms(x):
    return int(datetime.datetime.combine(x, datetime.datetime.min.time()).timestamp() * 1000)

@app.route('/')
def hello():

    _, commodity_names = get_commodity_ids()
    data = []
    for commodity_name, commodity_id in commodity_names.items():
        price_data = get_data(commodity_id)
        data.append({
            'name': commodity_name,
            't': [date_to_epoch_ms(x) for (x, _) in price_data],
            'y': [float(x) for (_, x) in price_data],
            })

    return '''<!doctype html>
<html>

<head>
	<title>Line Chart Multiple Axes</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.bundle.js"></script>
	<style>
	canvas {
		-moz-user-select: none;
		-webkit-user-select: none;
		-ms-user-select: none;
	}
	</style>
</head>


<body>
<h1>Alex's Fruit tracker</h1>
raw data is available for <a href="/data">download</a><br/>
new data can be uploaded <a href="/upload">here</a><br/>

	<div style="width:75%;">
		<canvas id="canvas"></canvas>
	</div>
	<script>

    var shapes = ['triangle', 'cross', 'square', 'circle'];
    var colors = [
        'rgb(255, 99, 132)',
        'rgb(94, 172, 32)',
        'rgb(10, 40, 199)',
        'rgb(189, 189, 20)',
        ];

    function get_item_wrap(i, l) {
        i = i % l.length;
        return l[i]
    }

    var data = ''' + json.dumps(data) + ''';

    var datasets = [];

    for( var i = 0; i < data.length; i++ ) {
        var price_data = []
        for( var j = 0; j < data[i].y.length; j++ ) {
            price_data.push({
                x: new Date(data[i].t[j]),
                y: data[i].y[j]
            });
        }

        datasets.push({
            label: data[i].name,
            pointRadius: 10,
            lineTension: 0,
            pointStyle: get_item_wrap(i, shapes),
            borderColor: get_item_wrap(i, colors),
            fill: false,
            data: price_data
        });
    }

                var ctx = document.getElementById('canvas').getContext('2d');
    var chart = new Chart(ctx, {
    // The type of chart we want to create
    type: 'line',

    // The data for our dataset
    data: {
        datasets: datasets
    },

    // Configuration options go here
    options: {
        animation: false,
        responsive: true,
        legend: {
            position: 'bottom',
            labels: {
                usePointStyle: true
            }
        },
        scales: {
            xAxes: [{
                    type:       "time",
                    scaleLabel: {
                        display:     true,
                        labelString: 'Date'
                    }
                }],
            yAxes: [{
                    scaleLabel: {
                        display:     true,
                        labelString: 'Price (USD)'
                    }
                }]
        },
        title: {
            display: true,
            text: 'fruit prices'
        }
    }
});
	</script>
</body>

</html>'''


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

    try:
        connection, cursor = db_connect()

        for commodity_name, prices in data.items():
            commodity_id = commodity_names[commodity_name]
            assert len(dates) == len(prices)
            for date, price in zip(dates, prices):
                cursor.execute('INSERT INTO "mad"."prices" (commodity_id, date, price) VALUES (%s, %s, %s) ON CONFLICT (commodity_id, date) DO UPDATE SET price = excluded.price', (commodity_id, date, price));

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    return 'updated database'


if __name__ == '__main__':
   app.run()

