import pandas as pd
import numpy as np
import json
import streamlit as st
import requests
import geopandas as gpd
from models import address_to_travel_map, geojson_to_geodataframe, travel_time_prices_paid_table, get_isoline_from_address
import os
from dotenv import find_dotenv, load_dotenv

env_loc = find_dotenv('.env')
load_dotenv(env_loc)

geoapify_key = os.environ.get('GEOAPIFY_KEY')

## Streamlit App
# Header Text
st.title("**Geocoder2**")

# Sidebar
# api_key = st.sidebar.text_input('Add Geoapify key here', value='abc123') # Swap this out with environment variable, if preferred
address_input = st.sidebar.text_input('Input address here',value='Buckingham Palace')
#st.write(get_isoline_from_address(geoapify_key,address_input))

travel_mode = st.sidebar.selectbox('Travel mode',options=['drive','walk','bicycle','transit','truck'])
travel_time = st.sidebar.slider('Travel time (m)', min_value=1, max_value=60, value=20,step=1)
travel_time_seconds = travel_time * 60
search_button = st.sidebar.button('Search')

# Ward boundaries and attributes
ward_pop = pd.read_csv('data/wards/ward_population_projections_full_2019.csv').iloc[:,1:].drop(columns=['wd20nm'])
wards_api = requests.get('https://opendata.arcgis.com/datasets/62bfaabbe3e24a359fc36b34d7fe8ac8_0.geojson')
wards_shp = geojson_to_geodataframe(wards_api.json()).iloc[:,:4]
gdf = wards_shp.merge(ward_pop, on='wd20cd', how='left')
gdf = gdf[(gdf.country == 'England') | (gdf.country == 'Wales')]
gdf = gdf.rename(columns={'wd20cd':'Ward Code','wd20nm':'Ward Name'})

# UK Prices paid data
prices = pd.read_csv('data/prices_paid_2019.csv')
prices_gdf = gpd.GeoDataFrame(prices, geometry=gpd.points_from_xy(prices.longitude, prices.latitude, crs=4326))



if search_button:
    payload = address_to_travel_map(api_key=geoapify_key, overlay_location=gdf, address=address_input, mode=travel_mode,
                                    range=travel_time_seconds, weighted_columns=[('mean_age','total_population'),('median_age','total_population')],
                                    show_map=False, zoom_level=10)

    data_payload = payload[0]
    starting_point = data_payload[0]
    isoline_gdf = data_payload[1]
    overlay_gdf = data_payload[2].drop(labels='geometry',axis=1)
    map_fig = payload[1]
    prices_paid_table = travel_time_prices_paid_table(isoline_gdf, prices_gdf)
    median_price = prices_paid_table.AMOUNT.median()
    mean_price = prices_paid_table.AMOUNT.mean()
    total_paid = prices_paid_table.AMOUNT.sum()

    area_median_age = overlay_gdf.weighted_median_age.sum()
    diff_area_age_to_uk = (area_median_age / 40.5)
    st.write(f'Details about area within **{travel_time}** mins **{travel_mode}** of **{address_input}**:')
    st.write(f'Approx. Population: **{overlay_gdf.total_population.sum():,.0f}**\
              | Median Age: **{area_median_age:,.0f}** \
              | {diff_area_age_to_uk:.2%} of UK median age (40.5 years)')

    st.markdown('#### 2019 Prices Paid')
    st.write(f'Median - Area: **£{median_price:,.0f}**\
              | Nationally: **£{prices_gdf.AMOUNT.median():,.0f}**')
    st.write(f'Average - Area: **£{mean_price:,.0f}**\
              | Nationally: **£{prices_gdf.AMOUNT.mean():,.0f}**')
    st.write(f'Activity - Area: **{len(prices_paid_table):,.0f}**\
              | Nationally: **{len(prices_gdf):,.0f}**')

    st.plotly_chart(map_fig)