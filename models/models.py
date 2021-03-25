import pandas as pd
from pandas import json_normalize
import geopandas as gpd
import os
import requests
from requests.structures import CaseInsensitiveDict
from geojson import Feature, Point, FeatureCollection
from dotenv import find_dotenv, load_dotenv
from pathlib import Path
from typing import List
import json
import plotly.express as px
env_loc = find_dotenv('.env')
load_dotenv(env_loc)

geoapify_key = os.environ.get('GEOAPIFY_KEY')

def geoapify_geocode(address_text: str = 'Finsbury Park Station', country: str = 'uk'):
    url = f'https://api.geoapify.com/v1/geocode/search?text={address_text}&apiKey={geoapify_key}&filter=countrycode:{country}'
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    response = requests.get(url, headers=headers)
    return response.json()

def geojson_to_geodataframe(geojson: dict, crs: int = 4326):
    collection = FeatureCollection(geojson)
    gdf = gpd.GeoDataFrame.from_features(collection['features']).set_crs(epsg=crs)
    return gdf

def address_to_geodataframe(address_text: str = 'Finsbury Park Station', country: str = 'gb', crs: int = 4326):
    geojson = geoapify_geocode(address_text=address_text, country=country)
    gdf = geojson_to_geodataframe(geojson, crs=crs)
    return gdf

def get_isoline(lat: float, lon: float, type: str = 'time', mode: str = 'walk', range: int = 1000):
    url = f'https://api.geoapify.com/v1/isoline?lat={lat}&lon={lon}&type={type}&mode={mode}&range={range}&apiKey={geoapify_key}'
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    response = requests.get(url, headers=headers)
    return response.json()

def get_isoline_from_address(address: str, country: str = 'gb', crs: int = 4326, mode: str = 'drive',
                            traveltime_seconds: int = 1800):
    '''
    Parameters:
    address (str) - 
    country (str) - 
    crs (int) - 
    mode (str) - 
    traveltime_seconds (int) - 
    ___________
    Returns:
    point geodataframe:
    polygon geodataframe:
    '''
    gdf = address_to_geodataframe(address_text=address, country=country, crs=crs).iloc[0]
    lat, lon = gdf['lat'], gdf['lon']
    iso = get_isoline(lat=lat, lon=lon, mode=mode, range=traveltime_seconds)
    isoline_gdf = geojson_to_geodataframe(iso)
    return gdf, isoline_gdf


def travel_time_payload(overlay_gdf: object, address: str, mode: str = 'walk', range: int = 1000,
                       weighted_columns: List = None):
    point_df, travel_df = get_isoline_from_address(address, mode=mode, traveltime_seconds=range)
    overlay_df = gpd.overlay(travel_df, overlay_gdf, how='intersection')
    # Add weighted measure columns
    if weighted_columns:
        for col in weighted_columns:
            overlay_df[f'weighted_{col[0]}'] = (overlay_df[col[1]] / overlay_df[col[1]].sum()) * overlay_df[col[0]]
    return point_df, travel_df, overlay_df

def map_travel_boundaries(payload, zoom_level: int = 10, show: bool = False):
    df = payload[2].drop(labels='geometry',axis=1)
    geojson = json.loads(payload[2].to_json())
    lat = payload[0]['lat']
    lon = payload[0]['lon']

    fig = px.choropleth_mapbox(df, geojson=geojson, color="total_population",
                               locations="Ward Code", featureidkey="properties.Ward Code",
                               center={"lat": lat, "lon":lon},
                               hover_data=['Ward Name'],
                               mapbox_style="carto-positron", zoom=zoom_level,opacity=0.5)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    if show:
        fig.show()
        return fig
    else:
        return fig
    
def address_to_travel_map(overlay_gdf: object, address: str, mode: str = 'drive', range: int = 1000,
                       weighted_columns: List = None, show_map: bool = True, zoom_level: int = 10):
    payload = travel_time_payload(overlay_gdf=overlay_gdf, address=address, mode=mode, range=range,
                                 weighted_columns=weighted_columns)
    fig = map_travel_boundaries(payload=payload, zoom_level=zoom_level, show=show_map)
    return payload, fig