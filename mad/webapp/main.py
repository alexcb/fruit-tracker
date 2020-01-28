from flask import Flask, escape, request
import psycopg2


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

def get_data():
    try:
        connection, cursor = db_connect()

        commodity_id = 2

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

@app.route('/')
def hello():
    data = get_data()
	#<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.3/Chart.min.js"></script>
    return '''<!doctype html>
<html>

<head>
	<title>Line Chart Multiple Axes</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@2.8.0"></script>
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
                var ctx = document.getElementById('canvas').getContext('2d');
var chart = new Chart(ctx, {
    // The type of chart we want to create
    type: 'line',

    // The data for our dataset
    data: {
        labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July'],
        datasets: [{
            label: 'apples',
            pointStyle: 'triangle',
            pointRadius: 10,
            lineTension: 0,
            borderColor: 'rgb(255, 99, 132)',
            fill: false,
            data: [0, 10, 5, 2, 20, 30, 45]
        },
       {
            label: 'pears',
            pointStyle: 'circle',
            pointRadius: 10,
            lineTension: 0,
            borderColor: 'rgb(93, 255, 132)',
            fill: false,
            data: [3, 10, 9, 1, 21, 10, 25]
        } ]
    },

    // Configuration options go here
    options: {
        responsive: true,
        legend: {
            position: 'bottom',
            labels: {
                usePointStyle: true
            }
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

