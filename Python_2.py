import streamlit as st
import plotly.express as px
import pandas as pd
import os
import warnings
import json
import requests
from streamlit_option_menu import option_menu
import streamlit_lottie as st_lottie
from streamlit_extras.colored_header import colored_header
from annotated_text import annotated_text
from streamlit.components.v1 import html
from ipyvizzu import Data, Config, Style
from ipyvizzustory import Story, Slide, Step
import pathlib
import shutil
import ssl
import geopandas as gpd
import pydeck as pdk

warnings.filterwarnings('ignore')

st.set_page_config(page_title="World Population Analysis", page_icon=":globe_with_meridians:",layout="wide")
st.title(" :globe_with_meridians: World Population Analysis")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>',unsafe_allow_html=True)

#######################
# Load data
merged_df = pd.read_excel("World Population.xlsx")

# Define the columns that you want to keep as id_vars
id_vars = ['country', 'continent']  # add other column names as needed

# Define the columns that you want to melt into rows
value_vars = ['1970', '1980', '1990', '2000', '2010', '2020', '2022', '2030', '2050']  # add other column names as needed

# Melt the DataFrame
df_reshaped = merged_df.melt(id_vars=id_vars, value_vars=value_vars, var_name='year', value_name='population')



#######################
# Plots

# Aggregate growth_rate by country
map_growth = df_reshaped.groupby('country')['year'].sum().reset_index()

# Rename columns
map_growth.rename(columns={'year': 'Population_2023'}, inplace=True)

# Load a world map shapefile
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Merge your data with the world map
map_growth_join = world.merge(map_growth, left_on='name', right_on='country', how='left')

# Convert GeoDataFrame to GeoJSON so it can be plotted on a map
map_growth_join['geometry'] = map_growth_join['geometry'].to_crs(epsg=4326).simplify(0.05).buffer(0.1)
json = map_growth_join.to_json()

# Create a map layer
layer = pdk.Layer(
    'GeoJsonLayer',
    json,
    opacity=0.8,
    stroked=False,
    filled=True,
    extruded=True,
    wireframe=True,
    get_elevation='properties.Population_2023 / 100',
    get_fill_color='[255, 255, properties.Population_2023 / 100]',
    get_line_color=[255, 255, 255],
)

# Set the viewport location
view_state = pdk.ViewState(latitude=37.7749295, longitude=-122.4194155, zoom=10, bearing=0, pitch=45)

################################
def make_choropleth(input_df, selected_year, selected_continent, selected_country, input_color_theme):
    # Filter the data based on the selected year, continent, and country
    if selected_year != 'All':
        input_df = input_df[input_df['year'] == selected_year]
    if selected_continent != 'All':
        input_df = input_df[input_df['continent'] == selected_continent]
    if selected_country != 'All':
        input_df = input_df[input_df['country'] == selected_country]
    if selected_continent == 'All':
        scope = 'world'  # Set scope to 'world' if all continents selected
    else:
        scope = selected_continent.lower()  # Convert continent to lowercase for matching valid options

    # Check if the filtered DataFrame is empty
    if input_df.empty:
        max_population = 0
    else:
        max_population = max(input_df.population)
    
    # Create the choropleth map only if there is data to plot
    if not input_df.empty:
            choropleth = px.choropleth(input_df,
                locations='country',
                color='population',
                locationmode="country names",
                color_continuous_scale=selected_color_theme,
                range_color=(0, max(input_df.population)),
                scope=scope,  # Set scope dynamically
                labels={'population': 'Population'}
                                  )
            choropleth.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(0, 0, 0, 0)',
                margin=dict(l=0, r=0, t=0, b=0),
                height= 280
            )
            return choropleth
    else:
        # Return None or an appropriate message if there is no data to plot
        st.error('No data available to plot for the selected options.')
        return None

#######################

# Horizontal menu
selected2 = option_menu(None, ["Home", "Dashboard", "Dataset"], 
    icons=['house', 'file-bar-graph', "list-task"], 
    menu_icon="cast", default_index=0, orientation="horizontal")

if selected2 == "Home":
        
        
        colored_header(
            label="🧭 Overview",
            description="About World Population",
            color_name="light-blue-70",)
        left_column, right_column = st.columns(2)
        with left_column:
            annotated_text("The world population dataset provides detailed data on population counts, growth rates, fertility rates, and urbanization levels from 1970 to 2050. It offers insights into global demographic trends, allowing for analysis at national and global levels. This data can help politicians make informed decisions about resource distribution for infrastructure development, education, and healthcare. It also provides insights into population density, ensuring long-term resource management and infrastructure planning. The dataset goes beyond just statistics, offering a wealth of information to address global concerns and create a more affluent future for everyone.")

        with right_column:
            st.lottie("https://lottie.host/4ff32b59-3137-42c6-ae6f-6831e22604e7/AM5TmClSle.json")
        
        st.sidebar.write("# Welcome to Our Python 2 Project 👋")
        st.sidebar.write("""This project aims to create an interactive dashboard that visually presents and generates various analyses from our first Python module.""")
        
        st.sidebar.write("# Our Previous Projects")

        # Link 1: Rstudio Project
        link1 = "Rstudio [Project](https://drive.google.com/drive/u/0/folders/1-qxb59BRJ1NNmQvJi99cgOFCYWeJzBkm?lfhs=2)"
        st.sidebar.write(link1, unsafe_allow_html=True)

        # Link 2: Python 1 Project
        link2 = "Python 1 [Project](https://drive.google.com/drive/u/0/folders/1-qxb59BRJ1NNmQvJi99cgOFCYWeJzBkm?lfhs=2)"
        st.sidebar.write(link2, unsafe_allow_html=True)

    # Render the map
        r = pdk.Deck(layers=[layer], initial_view_state=view_state)
        st.pydeck_chart(r)

        pass

elif selected2 == "Dashboard":

# Sidebar
    with st.sidebar:
        st.title('World Population Analysis')

        year_list = sorted(list(df_reshaped.year.unique()), reverse=True)
        selected_year = st.selectbox('Select a year', year_list)
        
        valid_continents = ['Africa', 'Asia', 'Europe', 'North America', 'South America']

        # Filter continents excluding Oceania
        filtered_continents = list(set(df_reshaped.continent.unique()) & set(valid_continents))

        continent_list = ['All'] + sorted(filtered_continents)
        selected_continent = st.selectbox('Select a continent', continent_list)

        
        if selected_continent == 'All':
            df_selected_continent = df_reshaped
            country_list = ['All'] + sorted(list(df_reshaped.country.unique()))
        else:
            df_selected_continent = df_reshaped[df_reshaped.continent == selected_continent]
            country_list = ['All'] + sorted(list(df_selected_continent.country.unique()))
        
        selected_country = st.selectbox('Select a country', country_list)
        
        color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
        selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

# Header design
    colored_header(
            label="📊 Dashboard",
            description="You can manipulate the dashboard by adjust the sidebar data 👈",
            color_name="orange-70",)
    col = st.columns((1.3, 4.7, 2), gap='medium')    

    # World Map
    with col[0]:

        def format_population(population):
            # Convert population to millions and round to one decimal place
            population_in_millions = round(population / 1_000_000, 1)
            # Return formatted string
            return f"{population_in_millions}M"

        # Main
        # Filter data for selected year
        current_year_data = df_reshaped[(df_reshaped['year'] == selected_year) & (df_reshaped['continent'] == selected_continent if selected_continent != 'All' else True) & (df_reshaped['country'] == selected_country if selected_country != 'All' else True)]
        current_year_population = current_year_data['population'].sum()

        # Find the previous year with available data
        year_list = sorted(list(df_reshaped.year.unique()))
        previous_year_index = year_list.index(selected_year) - 1
        previous_year = year_list[previous_year_index] if previous_year_index >= 0 else None

        # Filter data for previous year
        if previous_year:
            previous_year_data = df_reshaped[(df_reshaped['year'] == previous_year) & (df_reshaped['continent'] == selected_continent if selected_continent != 'All' else True) & (df_reshaped['country'] == selected_country if selected_country != 'All' else True)]
            previous_year_population = previous_year_data['population'].sum()
        else:
            previous_year_population = 0

        # Calculate the difference
        population_difference = current_year_population - previous_year_population

        # Calculate the percentage change
        if previous_year_population > 0:
            percentage_change = (population_difference / previous_year_population) * 100
        else:
            percentage_change = 0

        # Format the numbers
        current_year_population_formatted = format_population(current_year_population)
        previous_year_population_formatted = format_population(previous_year_population)
        population_difference_formatted = format_population(population_difference)

        st.subheader(f"Change from {previous_year} to {selected_year}")
        
        # Display the metric
        st.metric(label=f"In People", value=current_year_population_formatted, delta=population_difference_formatted)
        st.metric(label=f"In Percentage", value=f"{percentage_change:.2f}%", delta="")

    with col[1]:
        # Code for Plot section
        st.subheader('World Population Map')

        # Create a container for the map
        with st.container():
            # Call the make_choropleth function with the selected options
            choropleth = make_choropleth(df_reshaped, selected_year, selected_continent, selected_country, selected_color_theme)

            # Display the interactive choropleth map in the app
            if choropleth is not None:
                st.plotly_chart(choropleth)

    with col[2]:  
        # Filter the data based on the selected year, continent, and country
        if selected_year != 'All':
            df_selected_year = df_reshaped[df_reshaped['year'] == selected_year]
        else:
            df_selected_year = df_reshaped

        if selected_continent != 'All':
            df_selected_continent = df_selected_year[df_selected_year['continent'] == selected_continent]
        else:
            df_selected_continent = df_selected_year

        if selected_country != 'All':
            df_selected_country = df_selected_continent[df_selected_continent['country'] == selected_country]
        else:
            df_selected_country = df_selected_continent

        # Sort the filtered data by population in descending order
        df_selected_country = df_selected_country.sort_values(by="population", ascending=False)

        # Display the DataFrame as a table
        st.dataframe(df_selected_country[['country', 'year', 'population']],
                    column_order=("country", "population"),
                    hide_index=True,
                    width=None,
                    column_config={
                        "country": st.column_config.TextColumn(
                            "Country",
                        ),
                        "population": st.column_config.ProgressColumn(
                            "Population",
                            format="%f",
                            min_value=0,
                            max_value=max(df_selected_country.population),
                        )
                    }
)

################################################################
    colored_header(
            label="📜Population Story Tellings",
            description="This is comprehensive information of the world population - Press the next button to see the animation",
            color_name="yellow-70",)

    width=1000
    height=600

    # initialize chart
    data = Data()
    df = pd.read_csv('worldpop.csv', dtype={'Year': str})
    data.add_data_frame(df)
    #@title Create the story

    regions = df['Region'].unique()

    sel_region = st.selectbox(
        'Select region',
        list(regions))

    skip_intro = st.checkbox(
        'Skip intro slides', value=False
    )

    df_region = df[df['Region'] == sel_region]

    pop_max = int(df_region[df_region['Category'] == 'Population'][['Medium','High','Low']].max().T.max()*1.1)

    df_future = df_region[df_region['Period'] == 'Future']

    df_futureCategories = df_future[df_future['Category']!='Population'][['Category','Medium','High','Low']];

    df_future_sum = df_futureCategories.groupby('Category').sum().T

    other_max = df_future_sum.max().max() * 1.1
    other_min = df_future_sum.max().max() * -1.1 

    region_palette = ['#FE7B00FF','#FEBF25FF','#55A4F3FF','#91BF3BFF','#E73849FF','#948DEDFF']
    region_palette_str = ' '.join(region_palette)

    region_color = region_palette[list(regions).index(sel_region)]

    category_palette = ['#FF8080FF', '#808080FF', region_color.replace('FF','20'), '#60A0FFFF', '#80A080FF']
    category_palette_str = ' '.join(category_palette)

    # Define the style of the charts in the story
    style = {
            'legend' : {'width' : '13em'},
            'plot': {
                'yAxis': {
                    'label': {
                        'fontSize': '1em',
                        'numberFormat' : 'prefixed',
                        'numberScale':'shortScaleSymbolUS'
                    },
                    'title': {'color': '#ffffff00'},
                },
                'marker' :{ 
                    'label' :{ 
                        'numberFormat' : 'prefixed',
                        'maxFractionDigits' : '1',
                        'numberScale':'shortScaleSymbolUS',
                    }
                },
                'xAxis': {
                    'label': {
                        'angle': '2.5',
                        'fontSize': '1em',
                        'paddingRight': '0em',
                        'paddingTop': '1em',
                        'numberFormat' : 'grouped',
                    },
                    'title': {'color': '#ffffff00'},
                },
            },
        }

    story = Story(data=data)
    story.set_size(width, height)

    # Add the first slide, containing a single animation step 
    # that sets the initial chart.

    if skip_intro:
        style['plot']['marker']['colorPalette'] = region_palette_str
    else:
        slide1 = Slide(
            Step(
                Data.filter("record.Period === 'Past' && record.Category === 'Population'"),
                Config(
                    {
                        'x':'Year',
                        'y': 'Medium',
                        'label': 'Medium',
                        'title': 'The Population of the World 1950-2020',
                    }
                ),
                Style(style)
            )
        )
        # Add the slide to the story
        story.add_slide(slide1)

        # Show components side-by-side
        slide2 = Slide(
            Step(
                Config(
                    {
                        'y': ['Medium','Region'],
                        'color': 'Region',
                        'label': None,
                        'title': 'The Population of Regions 1950-2020',
                    }
                ),
                Style({ 'plot.marker.colorPalette': region_palette_str })
            )
        )
        story.add_slide(slide2)

        # Show components side-by-side
        slide3 = Slide()
        slide3.add_step(    
            Step(
                Data.filter("record.Category === 'Population'"),
                Config(
                    {
                        'y': ['Medium','Region'],
                        'color': 'Region',
                #     'lightness': 'Period',
                #     'x': ['Year','Period'],
                        'title': 'The Population of Regions 1950-2100',
                    }
                )
        ))

        slide3.add_step(    
            Step(
                Config(
                    {
                    'geometry':'area'
                    }
                )
        ))

        story.add_slide(slide3)

        slide4 = Slide(
            Step(
                Config(
                    {
                        'split': True
                    },
                ),
                Style({'plot' : {'yAxis' :{ 'label' :{ 'color' : '#99999900'}}}})
            )
        )
        story.add_slide(slide4)

        slide5 = Slide(
            Step(
                Config.percentageArea(
                    {
                        'x':'Year',
                        'y':'Medium',
                        'stackedBy':'Region',
                        'title': 'The Population of Regions 1950-2100 (%)'
                    }
                ),
                Style({'plot' : {'yAxis' :{ 'label' :{ 'color' : '#999999FF'}}}})
            )
        )
        story.add_slide(slide5)


    slide6 = Slide()
    slide6.add_step(    
        Step(
            Config.stackedArea(
                {
                    'x':'Year',
                    'y':'Medium',
                    'stackedBy':'Region',
                }
            ),
        Style(style) #,{'plot.marker.colorPalette': region_palette_str}
    ))

    slide6.add_step(    
        Step(
            Data.filter(f'record.Category === "Population" && record.Region === "{sel_region}"'),
            Config({
                    'title': 'The Population of '+sel_region+' 1950-2100',
                    'channels':{'y':{
                        'range':{'max':pop_max}
                    }}
            }),
        ))

    story.add_slide(slide6)

    slide7 = Slide(
        Step(
            Config(
                {
                    'y':'High',
                    'title': 'High prediction for '+sel_region
                }
            )
        )
    )
    story.add_slide(slide7)

    slide8 = Slide(
        Step(
            Config(
                {
                    'y':'Low',
                    'title': 'Low prediction for '+sel_region
                }
            )
        )
    )
    story.add_slide(slide8)

    slide9 = Slide(
        Step(
            Config(
                {
                    'y':'Medium',
                    'title': 'Medium prediction for '+sel_region
                }
            )
        )
    )
    story.add_slide(slide9)

    slide10 = Slide()

    slide10.add_step(
        Step(
            Config({
                'y':['Medium','Category'],
                'title': 'Adding Sources of Gain and Loss to the Mix '
            }),
        )
    )

    slide10.add_step(
        Step(
            Data.filter(f'record.Region === "{sel_region}" && (record.Category === "Population" || record.Category === "Migration+" || record.Category === "Births")'),
            Config(
                {
                    'color': ['Category']
                }),
            Style({ 'plot.marker.colorPalette': category_palette_str })
        )
    )

    slide10.add_step(
        Step(
            Data.filter(f'record.Region === "{sel_region}"'),
        )
    )
    story.add_slide(slide10)

    slide11 = Slide()

    slide11.add_step(
        Step(
            Config(
                {
                    'geometry':'rectangle',
                }
            )
        )
    )

    slide11.add_step(
        Step(
            Data.filter(f'record.Period === "Future" && record.Region === "{sel_region}"'),
            Config(
                {
                    'title': 'Zoom to the future'
                }
            )
        )
    )

    slide11.add_step(
        Step(
            Data.filter(f'record.Period === "Future" && record.Region === "{sel_region}" && record.Category !== "Population"'),
            Config(
                {
                    'channels':{
                        'x':{'set':['Medium','Year'],'range':{'max':other_max,'min':other_min}},
                        'y':{'set': 'Category', 'range':{'max':'auto'}},
                    },
                    'title': 'Sources of Population Gain and Loss - Medium Scenario'
                },
            ),
            Style({'plot' : {'marker' :{ 'label' :{ 'maxFractionDigits' : '1'}}}})

        )
    )

    slide11.add_step(
        Step(
            Config(
                {
                    'x':'Medium',
                    'label':'Medium',
                }
            )
        )
    )


    story.add_slide(slide11)

    slide12 = Slide(
        Step(
            Config(
                {
                    'x':'High',
                    'label': 'High',
                    'title': 'Sources of Population Gain and Loss - High Scenario'
                }
            )
        )
    )
    story.add_slide(slide12)

    slide13 = Slide(
        Step(
            Config(
                {
                    'x':'Low',
                    'label': 'Low',
                    'title': 'Sources of Population Gain and Loss - Low Scenario'
                }
            )
        )
    )
    story.add_slide(slide13)

    # Switch on the tooltip that appears when the user hovers the mouse over a chart element.
    story.set_feature('tooltip', True)
    
    html(story._repr_html_(), width=width, height=height)




elif selected2 == "Dataset":
        colored_header(
            label="World Population Dataset",
            description="Select the boxes below to see our Dataset👇",
            color_name="light-blue-70",)
        # Display the DataFrame as a table in the app
        choice = st.selectbox('Please select the datasets you want to learn about:',('Main dataset','Reshaped dataset - Dashboard Data','Additional dataset - Population Story Tellings Data'))
        st.caption(f"You selected: {choice}")   
        if choice == 'Main dataset':
            st.dataframe(merged_df)
            st.markdown(
        """
    **Explanation about the variables with in the data set**
    1. :orange[**country:**] The name of the country.
    2. :orange[**year:**] The year of the data point, ranging from 1970 to 2050. 
    3. :orange[**continent:**] The continent of the country.
    4. :orange[**population:**] The population of the country in the selected year.
    5. :orange[**growth rate:**] The annual population growth rate of the country. 
    6. :orange[**popl_rank:**] The global rank of the country based on its population. 
    7. :orange[**yr_change:**] The change in population from 2022 to 2023.
    8. :orange[**net_change:**] The net change in population from the previous year. 
    9. :orange[**dens:**] The population density (population per square kilometer). 
    10. :orange[**land_area:**] The total land area of the country in square kilometers. 
    11. :orange[**migr:**] The net migration (immigration minus emigration) in the given year. 
    12. :orange[**fert:**] The fertility rate of the country.
    13. :orange[**medage:**] The median age of the population.

        **Note: The average age in a population is generally calculated as the median, which measures the age above which is found one-half the population and below which is the other half  (Volansky, 2010).**

        """)
        if choice == 'Reshaped dataset - Dashboard Data':
            col = st.columns((1.3, 2.5), gap='medium')    

        # World Map
            with col[0]:

                st.dataframe(df_reshaped)

            with col[1]:
                st.write("*This is a dataset that has been customized and processed to function independently interactive dashboard. The original data of this dataframe is taken from merged_df and processed through long format data to obtain more detailed info for each country, thereby increasing customization and interaction.*")    
                
                st.write("**VARIABLES:**")
                st.markdown("1. :blue[**Country:**] Names of 215 countries in the world")
                st.markdown("2. :blue[**Continent:**] Names of the continent that each country belongs to")
                st.markdown("3. :blue[**Year:**] The year of the data point, ranging from 1970 to 2050")
                st.markdown("4. :blue[**Population:**] The population of the country in the selected year and country")

        if choice =='Additional dataset - Population Story Tellings Data':
            col = st.columns((1.3, 2.5), gap='medium')    

        # World Map
            with col[0]:
                worldpop = pd.read_csv('worldpop.csv')
                st.dataframe(worldpop)

            with col[1]:
                st.write("*This carefully selected dataset was included for two reasons relevant to our research project. First and foremost, it aims to provide keen readers with a detailed and nuanced summary of key data on the world's population. By consolidating statistical data on demographic trends, migration patterns, birth and death rates, this dataset contributes to a deeper understanding of the population environment complexities that humanity faces. Second, a more comprehensive set of global population statistics is needed to create the series of charts in Population Story Tellings section. This episode takes us on a fascinating journey through the complex story of global population dynamics, as we piece together the facts.*")    

                st.write("**VARIABLES:**")
                st.markdown("1. :blue[**Year:**] The year of the data point, ranging from 1950 to 2100.")
                st.markdown("2. :blue[**Region:**] Names of the continents.")
                st.markdown("3. :blue[**Period:**] The detail status of years which filters the Past (Confirmed Data) or Future (Conjectured Data).")
                st.markdown("4. :blue[**Category:**] Includes population categories such as the number of births, deaths, immigration, emigration and total population over the years of each continent.")
                st.markdown("5. :blue[**Low, Medium, High:**] Three levels of population conjecture in the above categories.")


        pass

