import psycopg2
from functools import wraps

db_connection = None

def db_connect(user="postgres", password="example", host="mad_database_1", port="5432", database='mad_dev'):
    global db_connection
    if db_connection:
        try:
            cur = db_connection.cursor()
            cur.execute('SELECT 1')
            return db_connection, cur
        except psycopg2.OperationalError:
            db_connection = None

    db_connection = psycopg2.connect(user=user,
                                  password=password,
                                  host=host,
                                  port=port,
                                  database=database,
                                  )
    cursor = db_connection.cursor()
    return db_connection, cursor


class database(): 
    def __init__(self): 
         self.db, self.cur = db_connect()

    def __enter__(self): 
        return self.db, self.cur
      
    def __exit__(self, exc_type, exc_value, exc_traceback): 
        # only close the cursor; the connection is pooled
        self.cur.close()

