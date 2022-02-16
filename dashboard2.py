import streamlit as st
from models import Mapper
import plotly.express as px
import json
import geojson

favicon = 'static/fiera-favicon.jpeg'
logo = 'static/fiera-logo-full.jpg'
## Streamlit App
# Page config
st.set_page_config(page_title='FRE UK Drivetime Analysis', 
                   page_icon=favicon, 
                   initial_sidebar_state='auto',
                   menu_items={'Get help':'https://www.fierarealestate.co.uk/contact-us/',
                               'Report a bug':None,
                               'About':'Contact David Bender at Fiera Real Estate for support or more details.'})

# Header Image and title
st.image(logo, width=250)
st.header("**England and Wales Drivetime Analysis**")

# Set up sidebar

password_input = st.sidebar.text_input('Password')
address_input = st.sidebar.text_input('Input address here',value='Buckingham Palace')
travel_mode = st.sidebar.selectbox('Travel mode',options=['driving','walking','cycling'])
travel_time = st.sidebar.slider('Travel time (m)', min_value=5, max_value=60, value=20, step=1)
travel_time_seconds = travel_time * 60

search_button = st.sidebar.button('Search')

with st.expander('Style Options'):
    area_specificity = st.slider('Specificity of drive-time area',min_value=0, max_value=500, step=5, value=100)
    map_style_options = ['carto-positron', 'carto-darkmatter', 'open-street-map', 'white-bg', 'stamen-terrain', 
                     'stamen-toner', 'stamen-watercolor','basic', 'streets', 'outdoors', 'light', 'dark', 
                     'satellite', 'satellite-streets']
    map_styling = st.selectbox('Map style',options=map_style_options,)
    map_colors = st.selectbox('Data colors',options=['oranges','blues'])
    map_zoom = st.selectbox('Map zoom', options=[5,6,7,8,8,9,10,11,12,13,14,15],index=6)
    style_update_button = st.button('Update styles')

def payload():
    mapper = Mapper(address=address_input)
    drivetime_map, area_stats, price_data = mapper.build_map(mode=travel_mode,
                                                             minutes=travel_time,
                                                             generalize=area_specificity, 
                                                             zoom_level=map_zoom,
                                                             opacity=0.5,
                                                             map_style=map_styling,
                                                             color_scheme=map_colors)

    return drivetime_map, area_stats, price_data, mapper.prices_gdf

def build_metrics(area_stats, price_data, national_prices):
    def diff_to_national(area, national):
        diff = area - national
        return ( diff / national ) * 100

    median_price = price_data.AMOUNT.median()
    median_price_to_national = diff_to_national(median_price, national_prices.AMOUNT.median())

    mean_price = price_data.AMOUNT.mean()
    mean_price_to_national = diff_to_national(mean_price, national_prices.AMOUNT.mean())

    total_paid = price_data.AMOUNT.sum()
    total_paid_to_national = diff_to_national(total_paid, national_prices.AMOUNT.sum())

    area_median_age = area_stats.median_age.median()
    diff_area_age_to_uk = (area_median_age / 40.5)

    st.write(f'##### Details about area within **{travel_time}** mins **{travel_mode}** of **{address_input}**:')

    st.write(f'Approx. Population: **{area_stats.total_population.sum():,.0f}**\
              | Median Age: **{area_median_age:,.0f}** \
              | {diff_area_age_to_uk:.2%} of UK median age (40.5 years)')

    st.markdown('##### House Price paid (2019) details in drivetime area (compared to national average)')
    col1, col2, col3 = st.columns(3)
    col1.metric("Median", f'£{median_price:,.0f}', f'{median_price_to_national:+.2f}%')
    col2.metric("Mean", f'£{mean_price:,.0f}', f'{mean_price_to_national:+.2f}%')
    col3.metric("Total", f'£{total_paid:,.0f}', None)

def build_map(drivetime_map):
    st.plotly_chart(drivetime_map)

if search_button:
    drivetime_map, area_stats, price_data, national_prices = payload()
    build_metrics(area_stats, price_data, national_prices)
    build_map(drivetime_map)

if style_update_button:
    drivetime_map, area_stats, price_data, national_prices = payload()
    build_metrics(area_stats, price_data, national_prices)
    build_map(drivetime_map) 
