import sqlite3
import pandas as pd
from pandas import json_normalize
from pathlib import Path

db_file = Path('../geocoder2/data/database.db')

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def create_connection():
    connection = sqlite3.connect(db_file)
    connection.row_factory = dict_factory
    return connection

# Estable database connection
def sql_to_df(table_name: str, connection: object):
    request = connection.execute(f'SELECT * FROM {table_name}')
    rows = request.fetchall()
    df = json_normalize(rows)
    return df

def sql_query(query: str, connection: object):
    request = connection.execute(query)
    rows = request.fetchall()
    df = json_normalize(rows)
    return df