import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from pandas import DataFrame

# Set page config at the very beginning
st.set_page_config(layout="wide", page_title="Geolocation Visualization App")

# Load the data
@st.cache_data
def load_data():
    data = pd.read_excel(r"C:\Users\hugo-gomes\Documents\Data Coleta.xlsx", sheet_name="DATA")
    data['DATA_BASE'] = pd.to_datetime(data['DATA_BASE'])
    data['DT_HR_EVENTO'] = pd.to_datetime(data['DT_HR_EVENTO'])
         # Calculate time difference between collections
    data['TIME_DIFF'] = data.groupby('MOTORISTA')['DT_HR_EVENTO'].diff().dt.total_seconds() / 60  # in minutes
    return data

# Load data
data = load_data()

# App title
st.title('Geolocation Visualization App')

# Sidebar filters
st.sidebar.header('Filters')
start_date = st.sidebar.date_input('Data de Início', value=min(data['DATA_BASE']), min_value=min(data['DATA_BASE']), max_value=max(data['DATA_BASE']))
end_date = st.sidebar.date_input('Data de Fim', value=max(data['DATA_BASE']), min_value=min(data['DATA_BASE']), max_value=max(data['DATA_BASE']))

selected_city = st.sidebar.multiselect('Selecione a Cidade', options=data['CIDADE'].unique(), default=data['CIDADE'].unique())
selected_driver = st.sidebar.multiselect('Selecione o Motorista', options=data['MOTORISTA'].unique(), default=data['MOTORISTA'].unique())
selected_veiculo = st.sidebar.multiselect('Selecione o Veículo', options=data['TIPO_VEICULO'].unique(), default=data['TIPO_VEICULO'].unique())
selected_periodo = st.sidebar.multiselect('Selecione o período', options=data['PERIODO_DIA'].unique(), default=data['PERIODO_DIA'].unique())

# Filter data
filtered_data = data[
    (data['DATA_BASE'] >= pd.to_datetime(start_date)) & (data['DATA_BASE'] <= pd.to_datetime(end_date)) &
    (data['CIDADE'].isin(selected_city)) &
    (data['MOTORISTA'].isin(selected_driver)) &
    (data['TIPO_VEICULO'].isin(selected_veiculo)) &
    (data['PERIODO_DIA'].isin(selected_periodo))
]

# Filter data
filtered_data_heat = data[
    (data['DATA_BASE'] >= pd.to_datetime(start_date)) & (data['DATA_BASE'] <= pd.to_datetime(end_date)) &
    (data['CIDADE'].isin(selected_city)) &
    (data['MOTORISTA'].isin(selected_driver)) &
    (data['TIPO_VEICULO'].isin(selected_veiculo)) &
    (data['PERIODO_DIA'].isin(selected_periodo))
]

# Define dynamic colors for drivers
# Create a dictionary to map drivers to colors
driver_colors = driver_colors = {
    'Jean-Rezende': 'red',
    'Gedean-Silva': 'green',
    'Gerson-Oliveira': 'blue',
    'Carlos-Donizeti': 'orange',
    'Marcelo-Donizeti': 'purple'
}

# Create two pages
pages = ["Heat Map", "Route Map"]
page = st.sidebar.radio("Select Page", pages)

if page == "Route Map":
    st.header('Route Map')
    
    def create_route_map(data):
        center_lat = data['LATITUDE'].mean()
        center_lon = data['LONGITUDE'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
        for _, row in data.sort_values('RANKING').iterrows():
            folium.Marker(
                location=[row['LATITUDE'], row['LONGITUDE']],
                popup=f"Rank: {row['RANKING']}<br>Driver: {row['MOTORISTA']}<br>City: {row['CIDADE']}<br>Time: {row['DT_HR_EVENTO']} <br>Fornecedor: {row['DESC_FORNECEDOR']}",
                icon=folium.DivIcon(html=f"<div style='background-color:{driver_colors[row['MOTORISTA']]};color:white;border-radius:50%;width:20px;height:20px;text-align:center;line-height:20px;'>{row['RANKING']}</div>")
            ).add_to(m)
            
        # Add lines connecting the points
        points = data.sort_values('RANKING')[['LATITUDE', 'LONGITUDE']].values.tolist()
        folium.PolyLine(points, color="blue", weight=2.5, opacity=0.8).add_to(m)
        return m
    
    route_map = create_route_map(filtered_data)
    folium_static(route_map, width=1200, height=600)

    # Display data table
    st.header('Data Table')
    st.dataframe(filtered_data)

elif page == "Heat Map":
    st.header('Heat Map')
    
    def create_heat_map(data):
        if data.empty:
            st.warning("No data available for the selected filters.")
            return None
        center_lat = data['LATITUDE'].mean()
        center_lon = data['LONGITUDE'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

        # Create a single heat map layer with all data points
        heat_data = data[['LATITUDE', 'LONGITUDE', 'RANKING']].values.tolist()
        HeatMap(heat_data, radius=15, blur=10, max_zoom=1, name="Heat Map").add_to(m)

        # Add markers for each driver with colors
        for _, row in data.iterrows():
            folium.CircleMarker(
                location=[row['LATITUDE'], row['LONGITUDE']],
                radius=5,
                popup=f"Driver: {row['MOTORISTA']}<br>City: {row['CIDADE']}<br>Time: {row['DT_HR_EVENTO']}",
                color=driver_colors[row['MOTORISTA']],
                fill=True,
                fillColor=driver_colors[row['MOTORISTA']],
                fill_opacity=0.6
            ).add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Add legend
        legend_html = """
        <div style="position: fixed; 
                    top: 10px; left: 10px; width: 150px; height: auto; 
                    border:2px solid grey; border-radius:5px; 
                    z-index:9999; font-size:14px; background:white;">
            <b>Driver Legend</b><br>
            <span style="color:red;">&#9679;</span> Jean-Rezende (SPRINTER)<br>
            <span style="color:green;">&#9679;</span> Gedean-Silva (SPRINTER)<br>
            <span style="color:blue;">&#9679;</span> Gerson-Oliveira (CAMINHAO)<br>
            <span style="color:orange;">&#9679;</span> Carlos-Donizeti (SPRINTER)<br>
            <span style="color:purple;">&#9679;</span> Marcelo-Donizeti (CAMINHAO)<br>
        </div>
        """
        
        # Create a div element for the legend
        folium.Marker(
            location=[center_lat + 0.3, center_lon + 0.6],
            icon=folium.DivIcon(html=legend_html)
        ).add_to(m)

        return m
    
    heat_map = create_heat_map(filtered_data_heat)
    if heat_map:
        folium_static(heat_map, width=1200, height=600)
    else:
        st.warning("Unable to create heat map due to insufficient data.")
        


# Heatmap of supplier visits by day of week
st.subheader('Supplier Visits by Day of Week')
filtered_data_heat['DAY_OF_WEEK'] = filtered_data_heat['DATA_BASE'].dt.day_name()
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
visits_by_day = filtered_data_heat.groupby(['DESC_FORNECEDOR', 'DAY_OF_WEEK']).size().unstack(fill_value=0)
visits_by_day = visits_by_day.reindex(columns=day_order)
fig = go.Figure(data=go.Heatmap(z=visits_by_day.values, x=visits_by_day.columns, y=visits_by_day.index, colorscale='YlOrRd'))
fig.update_layout(title='Supplier Visits by Day of Week', xaxis_title='Day of Week', yaxis_title='Supplier', height=800)
st.plotly_chart(fig, use_container_width=True)