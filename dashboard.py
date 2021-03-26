import pandas as pd
import streamlit as st
import requests
import geopandas as gpd
from models.models import travel_time_payload, map_travel_boundaries, \
                          address_to_travel_map, geojson_to_geodataframe,\
                              geoapify_geocode
from pathlib import Path
import os

## Streamlit App
# Header Text
st.sidebar.title("**Geocoder2**")

# Sidebar
api_key = st.sidebar.text_input('Add Geoapify key here', value='abc123')
address_input = st.sidebar.text_input('Input address here',value='Buckingham Palace')
travel_mode = st.sidebar.selectbox('Travel mode',options=['walk','bicycle','transit','drive','truck'])
travel_time = st.sidebar.slider('Travel time (m)', min_value=1, max_value=60, value=20,step=1)
travel_time_seconds = travel_time * 60
search_button = st.sidebar.button('Search')

if search_button:
    # Ward boundaries and attributes
    ward_pop = pd.read_csv('data/wards/ward_population_projections_full_2019.csv').iloc[:,1:].drop(columns=['wd20nm'])
    wards_api = requests.get('https://opendata.arcgis.com/datasets/62bfaabbe3e24a359fc36b34d7fe8ac8_0.geojson')
    wards_shp = geojson_to_geodataframe(wards_api.json()).iloc[:,:4].drop(columns='objectid')
    gdf = wards_shp.merge(ward_pop, on='wd20cd', how='left')
    gdf = gdf[(gdf.country == 'England') | (gdf.country == 'Wales')]
    gdf = gdf.rename(columns={'wd20cd':'Ward Code','wd20nm':'Ward Name'})

    payload = address_to_travel_map(overlay_gdf=gdf, address=address_input, mode=travel_mode,range=travel_time_seconds,
                                weighted_columns=[('mean_age','total_population'),('median_age','total_population')],
                                show_map=False, zoom_level=10, api_key=api_key)

    data_payload = payload[0]
    starting_point = data_payload[0]
    isoline_gdf = data_payload[1]
    overlay_gdf = data_payload[2].drop(labels='geometry',axis=1)
    map_fig = payload[1]

    st.write(f'Total Population: {overlay_gdf.total_population.sum():,.0f}')
    st.write(f'Median Age (weighted): {overlay_gdf.weighted_median_age.sum():,.0f}')
    st.write(f'Average Age (weighted): {overlay_gdf.weighted_mean_age.sum():,.0f}')

    st.plotly_chart(map_fig)