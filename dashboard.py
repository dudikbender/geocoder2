import streamlit as st
from models import Mapper, Supabase
import plotly.express as px
import json
import geojson
import os
from dotenv import find_dotenv, load_dotenv
load_dotenv()

# Static
app_password = os.environ.get('APP_PASSWORD')
db = Supabase()
favicon = 'static/fiera-favicon.jpeg'
logo = 'static/fiera-logo-full.jpg'
## Streamlit App
# Page config
st.set_page_config(page_title='FRE UK Travel Time Analysis', 
                   page_icon=favicon, 
                   initial_sidebar_state='auto',
                   menu_items={'Get help':'https://www.fierarealestate.co.uk/contact-us/',
                               'Report a bug':None,
                               'About':'Contact David Bender at Fiera Real Estate for support or more details.'})

# Header Image and title
st.image(logo, width=250)
st.header("**England and Wales Travel Time Analysis**")

# Set up sidebar
email_input = st.sidebar.text_input('Email')
password_input = st.sidebar.text_input('Password')
address_input = st.sidebar.text_input('Input address here',value='Emirates Stadium, N7 7AJ')
travel_mode = st.sidebar.selectbox('Travel mode',options=['driving','walking','cycling'])
travel_time = st.sidebar.slider('Travel time (m)', min_value=5, max_value=60, value=20, step=5)

search_button = st.sidebar.button('Search')

with st.expander('Style Options'):
    map_style_options = ['carto-positron', 'carto-darkmatter', 'open-street-map', 'white-bg', 'stamen-terrain', 
                     'stamen-toner', 'stamen-watercolor','basic', 'streets', 'outdoors', 'light', 'dark', 
                     'satellite', 'satellite-streets']
    map_colour_options = ['oranges','blues', 'purples', 'teal', 'bluered', 'viridis', 'sunset', 'dense']
    map_styling = st.selectbox('Map style',options=map_style_options,index=0)
    map_colours = st.selectbox('Data colors',options=map_colour_options, index=0)
    map_opacity = st.selectbox('Area opacity', options=[0.25, 0.5, 0.75, 1], index=1)
    map_zoom = st.slider('Map zoom', min_value=0.2, max_value=1.0, step=0.1, value=0.5)
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
    drivetime_map, area_stats, price_data = mapper.build_map(mode=travel_mode,
                                                             minutes=travel_time,
                                                             generalize=area_specificity, 
                                                             zoom_level=map_zoom,
                                                             opacity=map_opacity,
                                                             map_style=map_styling,
                                                             color_scheme=map_colours)

    return drivetime_map, area_stats, price_data, mapper.prices_gdf

def build_metrics(area_stats, price_data, national_prices):
    def diff_to_national(area, national):
        diff = area - national
        return ( diff / national ) * 100

    median_price = price_data.AMOUNT.median()
    median_price_to_national = diff_to_national(median_price, national_prices.AMOUNT.median())

    mean_price = price_data.AMOUNT.mean()
    mean_price_to_national = diff_to_national(mean_price, national_prices.AMOUNT.mean())

    total_paid_millions = price_data.AMOUNT.sum() / 1000000

    area_median_age = area_stats.median_age.median()
    diff_area_age_to_uk = (area_median_age / 40.5)

    st.markdown(f'##### Within **{travel_time}** mins **{travel_mode}** of **{address_input}**:\n')

    st.markdown('###### Population details within area')
    pop_col1, pop_col2, pop_col3 = st.columns(3)
    pop_col1.metric('Approx. Population',f'{area_stats.total_population.sum():,.0f}', None)
    pop_col2.metric('Median Age', f'{area_median_age:,.0f}')
    pop_col3.metric('UK National median age', '40.5', None)

    st.markdown('###### House Prices paid (2019)\n(compared to national average)')
    col1, col2, col3 = st.columns(3)
    col1.metric("Median Price", f'£{median_price:,.0f}', f'{median_price_to_national:+.2f}%')
    col2.metric("Average Price", f'£{mean_price:,.0f}', f'{mean_price_to_national:+.2f}%')
    col3.metric("Total Volume (£)", f'£{total_paid_millions:,.0f}M', None)

def build_map(drivetime_map):
    st.plotly_chart(drivetime_map)

def execute_visuals(spinner_text: str = 'Building your analysis'):
    with st.spinner(f'**{spinner_text}...**'):
        drivetime_map, area_stats, price_data, national_prices = payload()
        build_metrics(area_stats, price_data, national_prices)
        build_map(drivetime_map)

if search_button:
    if confirm_user():
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
        execute_visuals()
    else:
        st.error('''**Sorry, you do not have permission to use the app.** 
                    Please check the email and password, or contact Fiera Real Estate UK for access.''')

if style_update_button:
    if confirm_user():
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
        execute_visuals(spinner_text='Styling your visuals')
    else:
        st.error('''**Sorry, you do not have permission to use the app.**
                Please check the email and password, or contact Fiera Real Estate UK for access.''')
