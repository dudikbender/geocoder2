import geopandas as gpd
import requests
from requests.structures import CaseInsensitiveDict
from geojson import Feature, Point, FeatureCollection
import os
from dotenv import load_dotenv, find_dotenv
env_loc = find_dotenv('.env')
load_dotenv(env_loc)

class Geocoder():
    def __init__(self, address):
        self.address = address
        self.token = os.environ.get('MAPBOX_TOKEN')
        self.country_code = 'gb'
        self.crs = 4326

    def geocode_address(self, lat_lon: bool = True):
        url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{self.address}.json?access_token={self.token}' #&country={self.country_code}'
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
        url = f'https://api.mapbox.com/isochrone/v1/mapbox/{mode}/{lon},{lat}' #?polygons=true&contours_minutes={int(minutes)}&denoise={float(denoise)}&generalize={generalize}&access_token={self.token}'
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