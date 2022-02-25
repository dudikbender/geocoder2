import pandas as pd
import requests
import json
import geopandas as gpd
import plotly.express as px
from geojson import Feature, FeatureCollection, Point
from shapely import wkt
import os
from dotenv import find_dotenv, load_dotenv

from .geocoding import Geocoder
load_dotenv()

mapbox_token = os.environ.get('MAPBOX_TOKEN')
px.set_mapbox_access_token(mapbox_token)

class Mapper(Geocoder):
    def __init__(self, 
                 address: str):
        super().__init__(address=address)
        """ prices = pd.read_csv('data/prices_paid_2019.csv')
        self.prices_gdf = gpd.GeoDataFrame(prices, geometry=gpd.points_from_xy(prices.longitude, prices.latitude, crs=4326))
 """
    @staticmethod
    def wards_pop():
        ward_pop = pd.read_csv('data/wards/ward_population_projections_full_2019.csv').iloc[:,1:]
        return ward_pop.drop(columns=['wd20nm'])

    def wards_shp(self):
        data = requests.get('https://opendata.arcgis.com/datasets/62bfaabbe3e24a359fc36b34d7fe8ac8_0.geojson')
        collection = FeatureCollection(data.json())
        ward_shp = gpd.GeoDataFrame.from_features(collection['features']).set_crs(epsg=self.crs)
        return ward_shp.iloc[:, :4]

    def wards(self):
        wards_pop = self.wards_pop()
        wards_shp = self.wards_shp()
        gdf = wards_shp.merge(wards_pop, on='wd20cd', how='left')
        gdf = gdf[(gdf.country == 'England') | (gdf.country == 'Wales')]
        wards_df = gdf.rename(columns={'wd20cd':'Ward Code','wd20nm':'Ward Name'})
        return wards_df

    def overlay(self,
                mode: str,
                minutes: int,
                denoise: float,
                generalize: int):
        isochrone = self.isochrone(mode=mode,
                                   minutes=minutes,
                                   denoise=denoise,
                                   generalize=generalize)
        drivetime_area = isochrone[0]
        address_coords = isochrone[1]
        wards = self.wards()
        overlay = gpd.overlay(drivetime_area, wards, how='intersection')
        return overlay, address_coords

    def build_map(self, 
                  mode: str = 'driving',
                  minutes: int = 30,
                  denoise: float = 1,
                  generalize: int = 50,
                  zoom_level: int = 10,
                  opacity: float = 0.5,
                  map_style: str = 'carto-positron',
                  color_scheme: str = 'oranges'):
        drivetime_area, address_coords = self.overlay(mode, minutes, denoise, generalize)
        lat, lon = address_coords[1], address_coords[0]

        drivetime_data = pd.DataFrame(drivetime_area.drop(columns='geometry', axis=1))
        drivetime_geojson = json.loads(drivetime_area.to_json())

        fig = px.choropleth_mapbox(drivetime_data, 
                                   geojson=drivetime_geojson, 
                                   color="total_population",
                                   locations="Ward Code",
                                   featureidkey="properties.Ward Code",
                                   center={"lat": lat, "lon":lon},
                                   hover_data=['Ward Name'],
                                   mapbox_style=map_style,
                                   zoom=zoom_level,
                                   opacity=opacity,
                                   color_continuous_scale=color_scheme)

        centre_point = px.scatter_mapbox(lat=[lat],
                                         lon=[lon])
                
        fig.add_trace(centre_point.data[0]).update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        return fig, drivetime_data, drivetime_area