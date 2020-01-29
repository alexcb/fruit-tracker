from flask import Flask, escape, request
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

@app.route('/other')
def other():
    return '''
    <!doctype html>
<html>

<head>
    <title>Line Chart</title>
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
<div style="width:75%;">
    <canvas id="canvas"></canvas>
</div>
<script>
    var timeFormat = 'DD/MM/YYYY';

    var config = {
        type:    'line',
        data:    {
            datasets: [
                {
                    label: "US Dates",
                    data: [{
                        x: "04/01/2014", y: 175
                    }, {
                        x: "10/01/2014", y: 175
                    }, {
                        x: "04/01/2015", y: 178
                    }, {
                        x: "10/01/2015", y: 178
                    }],
                    fill: false,
                    borderColor: 'red'
                },
                {
                    label: "UK Dates",
                    data:  [{
                        x: "01/04/2014", y: 175
                    }, {
                        x: "01/10/2014", y: 175
                    }, {
                        x: "01/04/2015", y: 178
                    }, {
                        x: "01/10/2015", y: 178
                    }],
                    fill:  false,
                    borderColor: 'blue'
                }
            ]
        },
        options: {
            responsive: true,
            title:      {
                display: true,
                text:    "Chart.js Time Scale"
            },
            scales:     {
                xAxes: [{
                    type:       "time",
                    time:       {
                        format: timeFormat,
                        tooltipFormat: 'll'
                    },
                    scaleLabel: {
                        display:     true,
                        labelString: 'Date'
                    }
                }],
                yAxes: [{
                    scaleLabel: {
                        display:     true,
                        labelString: 'value'
                    }
                }]
            }
        }
    };

    window.onload = function () {
        var ctx       = document.getElementById("canvas").getContext("2d");
        window.myLine = new Chart(ctx, config);
    };

</script>

</body>

</html>'''

@app.route('/')
def hello():
    data = get_data(1)
    data_t = json.dumps([date_to_epoch_ms(x) for (x, _) in data])
    data_y1 = json.dumps([float(x) for (_, x) in data])

    data = get_data(2)
    data_y2 = json.dumps([float(x) for (_, x) in data])

    data = get_data(3)
    data_y3 = json.dumps([float(x) for (_, x) in data])
    
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
	<div style="width:75%;">
		<canvas id="canvas"></canvas>
	</div>
	<script>
                var data_t = ''' + data_t + ''';
                var data_y1 = ''' + data_y1 + ''';
                var data_y2 = ''' + data_y2 + ''';
                var data_y3 = ''' + data_y3 + ''';

                var data1 = [];
                var data2 = [];
                var data3 = [];

                for( var i = 0; i < data_t.length; i++ ) {
                    data1.push({
                        x: new Date(data_t[i]),
                        y: data_y1[i]
                        });
                    data2.push({
                        x: new Date(data_t[i]),
                        y: data_y2[i]
                        });
                    data3.push({
                        x: new Date(data_t[i]),
                        y: data_y3[i]
                        });
                }

                var ctx = document.getElementById('canvas').getContext('2d');
    var chart = new Chart(ctx, {
    // The type of chart we want to create
    type: 'line',

    // The data for our dataset
    data: {
        datasets: [
            {
                label: 'apples',
                pointStyle: 'triangle',
                pointRadius: 10,
                lineTension: 0,
                borderColor: 'rgb(255, 99, 132)',
                fill: false,
                data: data1
            },
            {
                label: 'pears',
                pointStyle: 'cross',
                pointRadius: 10,
                lineTension: 0,
                borderColor: 'rgb(66, 170, 102)',
                fill: false,
                data: data2
            },
            {
                label: 'quince',
                pointStyle: 'square',
                pointRadius: 10,
                lineTension: 0,
                borderColor: 'rgb(100, 123, 197)',
                fill: false,
                data: data3
            }
        ]
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
    return output.getvalue()

@app.route('/upload')
def upload():
    return '''
<html>
<body>
Upload prices from csv file (raw data can be accessed <a href="/data">here</a>)<br/>
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

