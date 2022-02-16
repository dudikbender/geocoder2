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
    area_specificity = st.slider('Specificty of drive-time area',min_value=0, max_value=500, step=5, value=100)
    map_style_options = ['carto-positron', 'carto-darkmatter', 'open-street-map', 'white-bg', 'stamen-terrain', 
                     'stamen-toner', 'stamen-watercolor','basic', 'streets', 'outdoors', 'light', 'dark', 
                     'satellite', 'satellite-streets']
    map_styling = st.selectbox('Map style',options=map_style_options,)
    map_colors = st.selectbox('Data colors',options=['oranges','blues'])
    map_zoom = st.selectbox('Map zoom', options=[5,6,7,8,8,9,10,11,12,13,14,15],index=6)
    style_update_button = st.button('Update styles')

def build_map():
    mapper = Mapper(address=address_input)

    drivetime_map, area_stats = mapper.build_map(mode=travel_mode,
                                    minutes=travel_time,
                                    generalize=area_specificity, 
                                    zoom_level=10,
                                    opacity=0.5,
                                    map_style=map_styling,
                                    color_scheme='oranges')
    st.dataframe(area_stats)    
    """ median_price = area_stats.amount.median()
    mean_price = area_stats.AMOUNT.mean()
    total_paid = area_stats.AMOUNT.sum()"""

    area_median_age = area_stats.median_age.sum()
    diff_area_age_to_uk = (area_median_age / 40.5)
    st.write(f'Details about area within **{travel_time}** mins **{travel_mode}** of **{address_input}**:')
    st.write(f'Approx. Population: **{area_stats.total_population.sum():,.0f}**\
              | Median Age: **{area_median_age:,.0f}** \
              | {diff_area_age_to_uk:.2%} of UK median age (40.5 years)')

    """ st.markdown('#### 2019 Prices Paid')
    st.write(f'Median - Area: **£{median_price:,.0f}**\
              | Nationally: **£{prices_gdf.AMOUNT.median():,.0f}**')
    st.write(f'Average - Area: **£{mean_price:,.0f}**\
              | Nationally: **£{prices_gdf.AMOUNT.mean():,.0f}**')
    st.write(f'Activity - Area: **{len(prices_paid_table):,.0f}**\
              | Nationally: **{len(prices_gdf):,.0f}**') """

    st.plotly_chart(drivetime_map)

if search_button:
    build_map()
    
