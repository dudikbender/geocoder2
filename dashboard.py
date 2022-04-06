import streamlit as st
import pandas as pd
import geopandas as gpd
from models import Mapper, Supabase, PricesPaid
from models.state_management import set_state, write_state, clear_state
import plotly.express as px
import json
import geojson
from datetime import datetime
import os
from dotenv import find_dotenv, load_dotenv
load_dotenv()

# Static
app_password = os.environ.get('APP_PASSWORD')
db = Supabase()
favicon = 'static/fiera-favicon.jpeg'
logo = 'static/fiera-logo-2.png'

## Streamlit App
# Page config
st.set_page_config(page_title='FRE UK Travel Time Analysis', 
                   page_icon=favicon, 
                   initial_sidebar_state='auto',
                   menu_items={'Get help':'https://www.fierarealestate.co.uk/contact-us/',
                               'Report a bug':None,
                               'About':'Contact David Bender at Fiera Real Estate for support or more details.'})
pd.options.display.float_format = '{:,}'.format

# Header Image and title
st.image(logo, width=200)
st.header("**England and Wales Travel Time Analysis**")

# Instantiate the Prices Paid data as H3 GeoDataFrame
@st.cache
def import_prices_df():
    prices_df = pd.read_csv('data/prices-paid-hex.csv')
    return prices_df

@st.cache
def import_hex():
    prices_geo = PricesPaid().to_h3()
    return prices_geo

prices_df = import_prices_df()
prices_geo = import_hex()
all_wards_pop = Mapper.wards_pop().rename(columns={'wd20cd':'Ward Code','wd20nm':'Ward Name'})
avg_ward_pop = all_wards_pop.total_population.mean()

# Set up sidebar
email_input = st.sidebar.text_input('Email')
password_input = st.sidebar.text_input('Password', type='password')
address_input = st.sidebar.text_input('Input address here',value='3 Old Burlington Street, London, W1S 3AE')
travel_mode = st.sidebar.selectbox('Travel mode',options=['driving','walking','cycling'])
travel_time = st.sidebar.slider('Travel time (m)', min_value=10, max_value=60, value=20, step=5)
search_button = st.sidebar.button('Search')

# Styling Options
with st.expander('Style Options'):
    map_style_options = ['carto-positron', 'carto-darkmatter', 'open-street-map', 'white-bg', 'stamen-terrain', 
                     'stamen-toner', 'stamen-watercolor','basic', 'streets', 'outdoors', 'light', 'dark', 
                     'satellite', 'satellite-streets']
    map_colour_options = ['oranges','blues', 'purples', 'teal', 'bluered', 'viridis', 'sunset', 'dense']
    map_styling = st.selectbox('Map style',options=map_style_options,index=0)
    map_colours = st.selectbox('Data colors',options=map_colour_options, index=0)
    map_zoom = st.selectbox('Starting map zoom', options=[8, 9, 10, 11, 12, 13, 14], index=2)
    map_opacity = st.slider('Area opacity', min_value=0.2, max_value=1.0, step=0.1, value=0.5)
    area_specificity = st.slider('Specificity of drive-time area',min_value=10, max_value=200, step=10, value=20)
    style_update_button = st.button('Update styles')

def confirm_user():
    user = db.check_user(email=email_input)
    if not user:
        return False
    elif user['password'] != password_input:
        return False
    else:
        return True

def payload():
    mapper = Mapper(address=address_input)
    drivetime_map, area_stats, drivetime_area = mapper.build_map(mode=travel_mode,
                                                             minutes=travel_time,
                                                             generalize=area_specificity, 
                                                             zoom_level=map_zoom,
                                                             opacity=map_opacity,
                                                             map_style=map_styling,
                                                             color_scheme=map_colours)

    return drivetime_map, area_stats, drivetime_area

def overlay_drivetime_with_prices(drivetime_area):
    overlay = gpd.overlay(drivetime_area, prices_geo)
    return overlay

def build_metrics(area_stats, price_data, national_prices):
    def diff_to_national(area, national):
        diff = area - national
        return ( diff / national ) * 100

    median_price = price_data['median_price'].mean()
    median_price_to_national = diff_to_national(median_price, national_prices['median_price'].mean())

    mean_price = price_data['mean_price'].mean()
    mean_price_to_national = diff_to_national(mean_price, national_prices['mean_price'].mean())

    total_paid_millions = price_data['total_paid'].sum() / 1000000

    area_median_age = area_stats.median_age.median()
    diff_area_age_to_uk = (area_median_age / 40.5)

    st.markdown(f'##### Within **{travel_time}** mins **{travel_mode}** of **{address_input}**:\n')

    st.markdown('###### Population details within area')
    pop_col1, pop_col2, pop_col3 = st.columns(3)
    pop_col1.metric('Approx. Population',f'{area_stats.total_population.sum():,.0f}', None)
    pop_col2.metric('Median Age', f'{area_median_age:,.0f}')
    pop_col3.metric('UK National median age', '40.5', None)

    st.markdown('###### House Prices paid (2019)')
    col1, col2 = st.columns(2)
    col1.metric("Median Price (relative to national)", f'£{median_price:,.0f}', f'{median_price_to_national:.2f}%')
    col2.metric("Average Price (relative to national)", f'£{mean_price:,.0f}', f'{mean_price_to_national:.2f}%')
    #col3.metric("Total Volume (£)", f'£{total_paid_millions:,.0f}M', None)

def build_map(drivetime_map):
    st.plotly_chart(drivetime_map)

def data_download(area_stats: pd.DataFrame):
    df = area_stats[['Ward Name', 'total_population', 'mean_age','median_age']]
    df.columns = ['Ward','Population','Average Age','Median Age']
    df = df.sort_values('Population', ascending=False).reset_index(drop=True)
    df['Pop. to Average Ward'] = df['Population'].apply(lambda x: ((x - avg_ward_pop) / x) * 100).apply(lambda x: f'{x:+.1f}%')
    formatted_pop = []
    for x in df['Population']:
        formatted = f'{int(x):,.0f}'
        formatted_pop.append(formatted)
    df['Population'] = formatted_pop
    df['Median Age'] = df['Median Age'].astype(int)
    df['Ward Average'] = avg_ward_pop
    df = df[['Ward','Population','Average Age','Median Age','Pop. to Average Ward']]
    csv = df.to_csv().encode('utf-8')
    st.download_button(label="Download ward data as CSV",
                        data=csv,
                        file_name=f'drive_time_analysis - {address_input}.csv',
                        mime='text/csv')
    st.dataframe(df)

def execute_visuals(spinner_text: str = 'Building your analysis'):
    with st.spinner(f'**{spinner_text}...**'):
        start_time = datetime.now()
        drivetime_map, area_stats, drivetime_area = payload()
        price_data = overlay_drivetime_with_prices(drivetime_area)

        build_metrics(area_stats, price_data, prices_df)
        build_map(drivetime_map)
        total_run_time = datetime.now() - start_time
        st.write(f'Results in: **{total_run_time.total_seconds():.3f}s**')
        return area_stats

if search_button:
    if confirm_user():
        set_state(email_input, password_input)
        try:
            db.add_row(table_name='searches',
                   user=email_input,
                   address=address_input,
                   mode=travel_mode,
                   range=travel_time,
                   map_style=map_styling,
                   map_colours=map_colours)
        except:
            pass
        st.balloons()
        area_stats = execute_visuals()
        data_download(area_stats)
    else:
        st.error('''**Sorry, you do not have permission to use the app.** 
                    Please check the email and password, or contact Fiera Real Estate UK for access.''')

if style_update_button:
    if confirm_user():
        set_state(email_input, password_input)
        try:
            db.add_row(table_name='searches',
                   user=email_input,
                   address=address_input,
                   mode=travel_mode,
                   range=travel_time,
                   map_style=map_styling,
                   map_colours=map_colours)
        except:
            pass
        st.balloons()
        area_stats = execute_visuals(spinner_text='Styling your visuals')
        data_download(area_stats)
    else:
        st.error('''**Sorry, you do not have permission to use the app.**
                Please check the email and password, or contact Fiera Real Estate UK for access.''')
