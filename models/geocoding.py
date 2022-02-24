import pandas as pd
import geopandas as gpd
import h3
import requests
from requests.structures import CaseInsensitiveDict
from geojson import Feature, Point, FeatureCollection
from shapely.geometry import Polygon
import plotly.express as px
import os
from dotenv import load_dotenv, find_dotenv
env_loc = find_dotenv('.env')
load_dotenv(env_loc)

class Geocoder():
    def __init__(self, address):
        '''Requires address string for England or Wales.'''
        self.address = address
        self.token = os.environ.get('MAPBOX_TOKEN')
        self.country_code = 'gb'
        self.crs = 4326

    def geocode_address(self, lat_lon: bool = True):
        url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{self.address}.json?access_token={self.token}&country={self.country_code}'
        headers ={'Accept':'application/json'}
        response = requests.get(url, headers=headers)
        if not lat_lon:
            return response.json()
        collection = FeatureCollection(response.json())
        gdf = gpd.GeoDataFrame.from_features(collection['features']).set_crs(epsg=self.crs).iloc[0]
        lon, lat = gdf['geometry'].x, gdf['geometry'].y
        return lon, lat
        
    def isochrone(self,
                  mode: str,
                  minutes: int,
                  denoise: float = 1,
                  generalize: int = 50):
        lon_lat = self.geocode_address(lat_lon=True)
        lon, lat = lon_lat
        url = f'https://api.mapbox.com/isochrone/v1/mapbox/{mode}/{lon},{lat}'
        headers = {'Accept':"application/json"}
        params = {'polygons':'true',
                  'contours_minutes':minutes,
                  'denoise':denoise,
                  'generalize':generalize,
                  'access_token':self.token}
        if generalize is None:
            params.pop('generalize')
        geojson = requests.get(url, headers=headers, params=params).json()
        collection = FeatureCollection(geojson)
        isochrone = gpd.GeoDataFrame.from_features(collection['features']).set_crs(epsg=self.crs)
        return isochrone, lon_lat

class PricesPaid():
    def __init__(self):
        df = pd.read_csv('data/prices_paid_2019.csv')
        data_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, 
                                                                         df.latitude)).reset_index()
        three_sigma_amount = data_gdf['AMOUNT'].mean() + (3 * data_gdf['AMOUNT'].std() )
        self.gdf = data_gdf[data_gdf['AMOUNT'] < three_sigma_amount]
        self.crs = 4326

    @staticmethod
    def geo_to_h3(row, H3_resolution = 5):
        return h3.geo_to_h3(lat=row.latitude,lng=row.longitude, resolution = H3_resolution)

    @staticmethod
    def add_geometry(row):
        points = h3.h3_to_geo_boundary(row['H3_cell'], True)
        return Polygon(points)

    @staticmethod
    def hexagons_dataframe_to_geojson(df_hex,
                                      hex_id_field,
                                      geometry_field,
                                      value_fields,
                                      file_output = None):

        list_features = []
        for i, row in df_hex.iterrows():
            feature = Feature(geometry = row[geometry_field],
                            id = row[hex_id_field],
                            properties = [ {f'{x}':row[x]} for x in value_fields ])
            list_features.append(feature)
        feat_collection = FeatureCollection(list_features)
        if file_output is not None:
            with open(file_output, "w") as f:
                json.dump(feat_collection, f)
        else :
            return feat_collection

    def to_h3(self, count_cutoff: int = 10, return_geo_df: bool = True):
        self.gdf['H3_cell'] = self.gdf.apply(self.geo_to_h3, axis=1)
        h3_df = self.gdf.groupby('H3_cell').agg({'AMOUNT':['mean','median','sum'],'index':['count']}).reset_index()
        h3_df.columns = ['H3_cell','mean_price','median_price','total_paid','count']
        h3_df['geometry'] = h3_df.apply(self.add_geometry, axis=1)
        h3_df = h3_df.loc[h3_df['count'] > count_cutoff]
        if return_geo_df:
            return gpd.GeoDataFrame(h3_df, geometry='geometry').set_crs(self.crs)
        return h3_df

    def to_geojson(self):
        h3_df = self.to_h3()
        geojson = self.hexagons_dataframe_to_geojson(h3_df,
                                                     hex_id_field='H3_cell',
                                                     value_fields=['mean_price','median_price','total_paid','count'],
                                                     geometry_field='geometry')
        return geojson

    def plotly_map(self):
        df = self.to_h3(return_geo_df=False)
        geojson = self.to_geojson()
        fig = (px.choropleth_mapbox(df, 
                                    geojson=geojson, 
                                    locations='H3_cell', 
                                    color='mean_price',
                                    color_continuous_scale="reds",
                                    range_color=(0, df['mean_price'].max()),
                                    mapbox_style='carto-positron',
                                    zoom=5,
                                    center = {"lat": 51.5014, "lon": -0.1419},
                                    opacity=0.7,
                                    labels={'average':'RE prices paid'}))
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        return fig