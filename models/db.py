import pandas as pd
import json
import geopandas as gpd
import requests
import os
from dotenv import load_dotenv, find_dotenv
env_loc = find_dotenv('.env')
load_dotenv(env_loc)

class Supabase():
    def __init__(self):
        self.url = os.environ.get('SUPABASE_URL')
        self.api_key = os.environ.get('SUPABASE_KEY')
        self.headers = {'apikey':f'{self.api_key}',
                        'Authorization':f'Bearer {self.api_key}'}

    def get_table(self, table_name: str, **kwargs):
        url = f'{self.url}/{table_name}'
        response = requests.get(url=url, headers=self.headers, params=kwargs)
        return response.json()

    def get_users(self, **kwargs):
        return self.get_table('users', **kwargs)

    def get_searches(self, **kwargs):
        return self.get_table('searches', **kwargs)

    def check_user(self, email: str):
        users = self.get_users()
        user_list = pd.DataFrame(users)['email'].tolist()
        if email in user_list:
            for i in users:
                if i['email'] == email:
                    return i
        return False

    def add_row(self, table_name: str, **kwargs):
        url = f'{self.url}/{table_name}'
        headers = self.headers
        headers['Content-Type'] = 'application/json'
        headers['Prefer'] = 'return=representation'
        request = requests.post(url=url, headers=headers, json=kwargs)
        return request

def import_hex_geojson():
    with open('data/prices-paid-hex.geojson') as json_file:
        data = json.load(json_file)
    
    d = pd.DataFrame(data['features'])

    mean = []
    median = []
    total = []
    count = []

    for x in d['properties']:
        mean.append(x[0]['mean_price'])
        median.append(x[1]['median_price'])
        total.append(x[2]['total_paid'])
        count.append(x[3]['count'])
        
    d['mean_price'] = mean
    d['median_price'] = median
    d['total_paid'] = total
    d['count'] = count

    df = d.drop(columns=['properties','type'])

    return df #gpd.GeoDataFrame(df, geometry='geometry').set_crs(4326)