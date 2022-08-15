import time
import dash
from dash import Dash, dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import geojson
import shapely.wkt
import math
from datetime import date



colorscales = px.colors.named_colorscales()
dash.register_page(__name__, name='Power Unbalance', path ='/power_unbalance')


directory_base = '../'

with open(directory_base + '/master_buildings.geojson') as f:  #TODO filepath to your own directories
    gj = geojson.load(f)
download_directory = directory_base + '/bms_csv_data/cleaned_data/'

df = pd.read_csv(directory_base + '/caltech_building_master_list.csv', encoding = 'latin-1')
data = pd.read_csv(directory_base + '/bms_inventory.csv', encoding = 'latin-1') 

#choose a random meter just to get the date range
meters = data[(data['Building String'] == 'hameetman') & (data['Meter Name'].str.contains('EM') == True)]
meter = meters.iloc[0]['Meter Name'] #TODO chooses the first meter from a building (aggregation/summing details still unclear)
measurement = 'kW'
jace = str(data[data['Meter Name'] == meter]['Jace'].values[0])
filename = download_directory + meter + '/' + jace + '_' + meter + '_' + measurement + '.csv'
df1 = pd.read_csv(filename)


layout = html.Div([ 

        # left side (map)

        html.Div([
            
            dcc.Graph(
                id='map1',
                clickData = {'points': [{'location': 'Beckman Behavioral Biology'}]},
                figure =  px.choropleth_mapbox(center={"lon":-118.1252736595467, "lat": 34.1377288162599 },mapbox_style="carto-positron", zoom=15 ,
                            color_continuous_scale='rdylgn_r', width = 600, height = 600)
            ),

            html.Div([
                html.Div(
                    dcc.DatePickerRange(
                        min_date_allowed = df1['t'].iloc[0],
                        max_date_allowed = df1['t'].iloc[-1],
                        start_date = date(2022,4,3),
                        end_date = date(2022,4,10),
                        id='date-picker1',
                        ), style={'width': '49%' ,'display': 'inline-block'}),

                html.Div(
                    dcc.RadioItems(['Voltage','Current','Power'], value = 'Power', id = 'imbalance_measurement', inline = True, labelStyle= {'margin-right': '5%'}), style={'width': '49%','display': 'inline-block'})
            ])

        ], style={'width': '40%', 'display': 'inline-block', 'verticalAlign' : 'top'}),

        # right side (series)
        html.Div([
            html.H6('Power Unbalance', id = 'right-side-title'),

            #how to make more series data visible?
            html.Div([
            html.Div(dcc.Graph(id='PWP1-series'), style = {'width':'33%', 'display':'inline-block'}),
            html.Div(dcc.Graph(id='PWP2-series'), style = {'width':'33%', 'display':'inline-block'}),
            html.Div(dcc.Graph(id='PWP3-series'), style = {'width':'33%', 'display':'inline-block'})
            ]),

             html.Div(
                    dcc.RadioItems(['PWP-1', 'PWP-2','PWP-3'], value = 'PWP-1', id = 'PWP-meter', inline = True, labelStyle= {'margin-right': '26%'}), style={'padding-left':'0%' , 'padding-right':'0%'}),
            html.Hr(),
            html.H6('PWP-1 Power', id = 'PWP-meter-series-title'),
            html.Div(dcc.Graph(id='PWP-meter-series'), style={'margin-bottom':'1000'}),
            html.H6('Beckman Behavioral Biology', id = 'building-series-title'),
            html.Div(dcc.Graph(id='building-series'))

          
        ], style={'width': '59%',  'display': 'inline-block' 
       , 'maxHeight': '700px', "overflow": "scroll"
        })

        
])
def PWP_style(fig):
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    fig.update_xaxes(linecolor='black', gridcolor='rgba(0,0,0,0)')
    fig.update_yaxes(linecolor='black', gridcolor='rgba(0,0,0,0)')
    fig.update_coloraxes(showscale=False)
    return fig

def time_series_style(fig):
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    fig.update_xaxes(linecolor='black', gridcolor='rgba(0,0,0,0.2)')
    fig.update_yaxes(linecolor='black', gridcolor='rgba(0,0,0,0.2)')
    return fig

def df_size(building_string, start_date, end_date):
    meters = data[(data['Building String'] == building_string) & (data['Meter Name'].str.contains('EM') == True)]
    meter = meters.iloc[0]['Meter Name']
    jace = str(data[data['Meter Name'] == meter]['Jace'].values[0])
    filename = download_directory + meter + '/' + jace + '_' + meter + '_kW.csv'
    df1 = pd.read_csv(filename)
    mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
    df1 = df1.loc[mask] 
    return len(df1)

def PWP_Amps(meter, start_date, end_date):
    jace = str(data[data['Meter Name'] == meter]['Jace'].values[0])
    amplist = []
    for char in 'ABC': #downloads respective amps data and add traces to the graph
        filename = download_directory  + meter + '/' + jace + '_' + meter + '_Amps' + char + '.csv'
        df1 = pd.read_csv(filename)
        mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
        df1 = df1.loc[mask]
        amplist.append(df1['v'].mean())
    fig = px.bar(x=['A','B','C'], y=amplist,  color = amplist, color_continuous_scale = 'rdylgn_r', width = 150, height = 150)
    fig.update_layout(
       # title= meter + ' Amps',
         yaxis_title= 'Amps', xaxis_title = None, margin=dict(l=0, r=0, t=0, b=0))
         

    return PWP_style(fig)

def PWP_Volts(meter, start_date, end_date):

    jace = str(data[data['Meter Name'] == meter]['Jace'].values[0])
    voltslist = []
    for chars in ['AB' , 'BC' , 'CA']: #download respective Volts data and add traces to the graph
        try:
            filename = download_directory  + meter + '/' + jace + '_' + meter + '_Volts' + chars + '.csv'
            df1 = pd.read_csv(filename)
            mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
            df1 = df1.loc[mask]
            voltslist.append(df1['v'].mean())
        except:
            pass

    fig = px.bar(x=['A','B','C'], y=voltslist , color = voltslist, color_continuous_scale = 'rdylgn_r', width = 150, height = 150)
    fig.update_layout(
        #title= meter + ' Volts',
         yaxis_title= 'Volts', xaxis_title = None, margin=dict(l=5, r=5, t=5, b=5))


    return PWP_style(fig)

def PWP_Power(meter, start_date, end_date):
    powlist = []
    filename = directory_base + 'unbalances/' + meter + '/' + meter + '_powerPhases.csv'        
    df1 = pd.read_csv(filename)
    mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
    df1 = df1.loc[mask]
    for string in ['kvaA','kvaB','kvaC']: #downloads respective amps data and add traces to the graph
        powlist.append(df1[string].mean())
    fig = px.bar(x=['kvaA','kvaB','kvaC'], y=powlist,  color = powlist, color_continuous_scale = 'rdylgn_r', width = 150, height = 150)
    fig.update_layout(
       # title= meter + ' Amps',
         yaxis_title= 'Power', xaxis_title = None, margin=dict(l=0, r=0, t=0, b=0))
    return PWP_style(fig)
         

#EM_SUB3_2
#E171 is EM_SUB3_3
#E209 is EM_SUB4_52U

@callback( 
    Output('PWP1-series', 'figure'),
    Output('PWP2-series', 'figure'),
    Output('PWP3-series', 'figure'),
    Output('right-side-title', 'children'),

    Input('date-picker1', 'start_date'),
    Input('date-picker1', 'end_date'),
    Input('imbalance_measurement', 'value')
)

def update_PWP_meter_series(start_date, end_date, measurement):
    
    if measurement == 'Voltage':
        return PWP_Volts('EM_SUB3_2', start_date, end_date),  PWP_Volts('EM_SUB3_3', start_date, end_date), PWP_Volts('EM_SUB4_52U', start_date, end_date), "Voltage Unbalance"
    elif measurement == 'Current':
        return PWP_Amps('EM_SUB3_2', start_date, end_date),  PWP_Amps('EM_SUB3_3', start_date, end_date), PWP_Amps('EM_SUB4_52U', start_date, end_date), "Current Unbalance"
    else: 
        return PWP_Power('EM_SUB3_2', start_date, end_date),  PWP_Power('EM_SUB3_3', start_date, end_date), PWP_Power('EM_SUB4_52U', start_date, end_date), "Power Unbalance"

#--------------------------------------------------------------------------------------#
@callback( 
    Output('PWP-meter-series', 'figure'),
    Output('PWP-meter-series-title', 'children'),

    Input('PWP-meter', 'value'),
    Input('date-picker1', 'start_date'),
    Input('date-picker1', 'end_date'),
    Input('imbalance_measurement', 'value')
)

def update_PWP_timeseries(PWPmeter, start_date, end_date, measurement):
    if PWPmeter == 'PWP-1':
        meter = 'EM_SUB3_2'
    elif PWPmeter == 'PWP-2':
        meter = 'EM_SUB3_3'
    else:
        meter = 'EM_SUB4_52U'
         #EM_SUB3_2, #E171 is EM_SUB3_3,#E209 is EM_SUB4_52U
   
    if measurement == 'Voltage':
        return create_time_series_Volts(meter, start_date, end_date), PWPmeter + ' Voltage'
    elif measurement == 'Current':
        return create_time_series_Amps(meter, start_date, end_date), PWPmeter + ' Current'
    else:
        return create_time_series_Power(meter, start_date, end_date),PWPmeter + ' Power'

def create_time_series_Amps(meter, start_date, end_date):
    jace = str(data[data['Meter Name'] == meter]['Jace'].values[0])
    fig = go.Figure()
    for char in 'ABC': #downloads respective amps data and add traces to the graph
        filename = download_directory + meter + '/' + jace + '_' + meter + '_Amps' + char + '.csv'
        df1 = pd.read_csv(filename)
        mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
        df1 = df1.loc[mask]
        fig = fig.add_trace(go.Scatter(x = df1["t"], y = df1["v"], name = "Amps" + char))

    fig.update_layout(title= '', xaxis_title=None, yaxis_title= 'Amps', margin=dict(l=20, r=20, t=20, b=20), height = 200)
    return time_series_style(fig)

def create_time_series_Volts(meter, start_date, end_date):

   
    jace = str(data[data['Meter Name'] == meter]['Jace'].values[0])
    fig = go.Figure()

    for chars in ['AB' , 'BC' , 'CA']: #download respective Volts data and add traces to the graph
        try:
            filename = download_directory  + meter + '/' + jace + '_' + meter + '_Volts' + chars + '.csv'
            df1 = pd.read_csv(filename)
            mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
            df1 = df1.loc[mask]
            fig = fig.add_trace(go.Scatter(x = df1["t"], y = df1["v"], name = "Volts" + chars)) 
        except:
            pass

    fig.update_layout(title='', xaxis_title= None, yaxis_title= 'Volts',margin=dict(l=20, r=20, t=20, b=20), height = 200)

    return time_series_style(fig)

def create_time_series_Power(meter, start_date, end_date):
    fig = go.Figure()
    filename = directory_base + 'unbalances/' + meter + '/' + meter + '_powerPhases.csv'        
    df1 = pd.read_csv(filename)
    mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
    df1 = df1.loc[mask]
    for string in ['kvaA','kvaB','kvaC']: #downloads respective amps data and add traces to the graph
        fig = fig.add_trace(go.Scatter(x = df1["t"], y = df1[string], name = string)) 
    fig.update_layout(title='', xaxis_title= None, yaxis_title= 'VoltAmps',margin=dict(l=20, r=20, t=20, b=20), height = 200)

   
    return time_series_style(fig)

@callback(
   
    Output('building-series', 'figure'),
    Output('building-series-title', 'children'),

    Input('map1', 'clickData'),
    Input('date-picker1', 'start_date'),
    Input('date-picker1', 'end_date'),
    Input('imbalance_measurement', 'value')

)

def update_building_timeseries(clickData, start_date, end_date, measurement):
    name = clickData['points'][0]['location']
    building_string = df[df['name'] == name]['Building String'].values[0]
    meters = data[(data['Building String'] == building_string) & (data['Meter Name'].str.contains('EM') == True)]
    meter = meters.iloc[0]['Meter Name']

    if measurement == 'Power':
        return create_time_series_Power(meter, start_date, end_date), name + ' Power'
    elif measurement == 'Current':
        return create_time_series_Amps(meter, start_date, end_date), name + ' Current'
    else:
        return create_time_series_Volts(meter, start_date, end_date) , name + ' Voltage'

#--------------------------------------------------------------------------------------------#
def update_power_imbalance(df, start_date, end_date):
    '''Loops through all building and updates the power imbalance column of the df, to be used for map coloring'''
    power = []
    for building in df['name'].values:
        try:
            building_string = df[df['name'] == building]['Building String'].values[0]

            meters = data[(data['Building String'] == building_string) & (data['Meter Name'].str.contains('EM') == True)]
            meter = meters.iloc[0]['Meter Name']#TODO chooses the first meter from a building (aggregation/summing details still unclear)
            filename = directory_base + 'unbalances/' + meter + '/' + meter + '_powerUnbalance.csv'
            df1 = pd.read_csv(filename)
            mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
            df1 = df1.loc[mask]  #downloads the information for kW within the start and end date
            if df1['pu'].mean() >= 0:
                power.append(df1['pu'].mean())
            else:
                power.append(-0.01)
        except:
            power.append(-0.01)
    df['Power Unbalance'] = power

def update_current_imbalance(df, start_date, end_date):
    '''Loops through all building and updates the current imbalance column of the df, to be used for map coloring'''
    current = []
    for building in df['name'].values:
        try:
            building_string = df[df['name'] == building]['Building String'].values[0]   
            meters = data[(data['Building String'] == building_string) & (data['Meter Name'].str.contains('EM') == True)]
            meter = meters.iloc[0]['Meter Name']#TODO chooses the first meter from a building (aggregation/summing details still unclear)
            filename = directory_base + 'unbalances/' + meter + '/' + meter + '_currentUnbalance.csv'
            df1 = pd.read_csv(filename)
            mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
            df1 = df1.loc[mask]  #downloads the information for kW within the start and end date
            if df1['cu'].mean() >= 0:
                current.append(df1['cu'].mean())
            else:
                current.append(-0.01)
        except:
            current.append(-0.01)
    df['Current Unbalance'] = current

def update_voltage_imbalance(df, start_date, end_date):
    '''Loops through all building and updates the voltage imbalance of the df, to be used for map coloring'''
    voltage = []
    for building in df['name'].values:
        try:
            building_string = df[df['name'] == building]['Building String'].values[0]   
            meters = data[(data['Building String'] == building_string) & (data['Meter Name'].str.contains('EM') == True)]
            meter = meters.iloc[0]['Meter Name']#TODO chooses the first meter from a building (aggregation/summing details still unclear)
            filename = directory_base + 'unbalances/' + meter + '/' + meter + '_voltageUnbalance.csv'
            df1 = pd.read_csv(filename)
            mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
            df1 = df1.loc[mask]  #downloads the information for kW within the start and end date
            if df1['vu'].mean() >= 0:
                voltage.append(df1['vu'].mean())
            else:
                voltage.append(-0.01)
        except:
            voltage.append(-0.01)
    df['Voltage Unbalance'] = voltage

@callback(
    Output('map1', 'figure'),
    Input('date-picker1', 'start_date'),
    Input('date-picker1', 'end_date'),
    Input('imbalance_measurement', 'value'),
)

def update_map(start_date, end_date, map_pick):
    
    if map_pick == 'Voltage':
        update_voltage_imbalance(df,start_date, end_date)
        fig = px.choropleth_mapbox(df, geojson = gj, 
            color = "Voltage Unbalance", labels={'name': 'Building Name'}, range_color=[0,1],
            locations= "name", featureidkey = "properties.name",
            center={"lon":-118.1252736595467, "lat": 34.1377288162599 },mapbox_style="carto-positron", zoom=15,
            width = 550, height = 600, color_continuous_scale=[(0, "gray"), (0.00001, "green"), (0.5,"yellow"), (1, "red")])
        fig.update_geos(fitbounds="locations", visible=True)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0} , paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    elif map_pick == 'Current':
        update_current_imbalance(df,start_date, end_date)
        fig = px.choropleth_mapbox(df, geojson = gj, 
            color = "Current Unbalance", labels={'name': 'Building Name'},
            locations= "name", featureidkey = "properties.name",
            center={"lon":-118.1252736595467, "lat": 34.1377288162599 },mapbox_style="carto-positron", zoom=15,
            width = 550, height = 600, color_continuous_scale=[(0, "gray"), (0.00001, "green"), (0.5,"yellow"), (1, "red")])
        fig.update_geos(fitbounds="locations", visible=True)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0} , paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    else:
        update_power_imbalance(df,start_date, end_date)
        fig = px.choropleth_mapbox(df, geojson = gj, 
            color = "Power Unbalance", labels={'name': 'Building Name'},
            locations= "name", featureidkey = "properties.name",
            center={"lon":-118.1252736595467, "lat": 34.1377288162599 },mapbox_style="carto-positron", zoom=15 ,
            width = 550, height = 600, color_continuous_scale=[(0, "gray"), (0.00001, "green"), (0.5,"yellow"), (1, "red")])
        fig.update_geos(fitbounds="locations", visible=True)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0} , paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                
    
    return fig
 
