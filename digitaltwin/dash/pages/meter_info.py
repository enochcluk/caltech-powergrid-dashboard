# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import dash
from dash import Dash, dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd
import geojson
import math
from datetime import date

dash.register_page(__name__,name='Meter Level Data', path = '/meter_info')


directory_base = '..'

data = pd.read_csv(directory_base+ '/bms_inventory.csv') #TODO filepath to your own directory
download_directory = directory_base + '/'

df = pd.read_csv(directory_base + "/geo.csv")




layout = html.Div([
    #html.H4(children='Meter Info'),

    html.H6(children='Building', style = {'margin-bottom': '10px'}),
    dcc.Dropdown(data['Single Line Building Name'].unique(), id = 'building-dropdown', value = 'Cahill' ,style = {'margin-bottom': '10px'}),

    html.H6(children='Meter',  style = {'margin-bottom': '10px'}),
    dcc.Dropdown(data['Meter Name'], id = 'meter-dropdown', value = 'EM_17_B1_A', style = {'margin-bottom': '10px'}),

    html.H6(children='Measurement',  style = {'margin-bottom': '10px'}),
    dcc.Dropdown(#['kW', 'kVar', 'kVA','AmpsA','AmpsB','AmpsC','VoltsAB','VoltsBC','VoltsCA','Frequency','PowerFactor'],
     id = 'measurement-dropdown', value = 'kW',style = {'margin-bottom': '10px'}),

    dcc.Graph(
        id='graph'
    ) 
])

   


@callback(
    Output('meter-dropdown', 'options'),
    Input('building-dropdown', 'value'))
def set_meter_options(building):
    '''Updates the meter dropdown based on building selected'''
    return data[data['Single Line Building Name'] == building]['Meter Name']

@callback(
    Output('measurement-dropdown', 'options'),
    Input('meter-dropdown', 'value'),
    Input('building-dropdown', 'value'))

def set_meter_options(meter,building):
    measurement_list = data[(data['Single Line Building Name'] == building) & (data['Meter Name'] == meter)]['Measurements'].values[0]
    return measurement_list.strip('][').split(', ')


@callback(
    Output('graph', 'figure'),
    Input('meter-dropdown', 'value'),
    Input('measurement-dropdown', 'value')
    )

def update_figure(meter, measurement):
    measurement = measurement.strip('\'')
    jace = str(data[data['Meter Name'] == meter]['Jace'].values[0])
    filename = download_directory + 'bms_csv_data/cleaned_data' + meter + '/' + jace + '_' + meter + '_' + measurement + '.csv'
    df1 = pd.read_csv(filename)
    fig = px.line(df1, x="t", y="v")
    fig.update_layout(title= meter + ' ' + measurement, xaxis_title='Time', yaxis_title= measurement, transition_duration=500 , paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0.2)')

    return fig
