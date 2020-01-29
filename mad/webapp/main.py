from flask import Flask, escape, request
import psycopg2
import json
import datetime


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

        cursor.execute('SELECT date, price FROM "mad"."prices" WHERE commodity_id = %s', (commodity_id,));

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
                        labelString: 'value'
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



if __name__ == '__main__':
   app.run()

