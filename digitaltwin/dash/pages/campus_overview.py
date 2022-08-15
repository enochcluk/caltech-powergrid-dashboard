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
dash.register_page(__name__, name='Campus Overview' , path = '/campus_overview')

directory_base = '../'

with open(directory_base + '/master_buildings.geojson') as f:  #TODO filepath to your own directories
    gj = geojson.load(f)
download_directory = directory_base + '/bms_csv_data/cleaned_data/'

df = pd.read_csv(directory_base + '/caltech_building_master_list.csv')
data = pd.read_csv(directory_base + '/bms_inventory.csv') 
has_match = df[df['Building String'].notnull()]
no_match = df[df['Building String'].isnull()]


#choose a random meter just to get the date range
meters = data[(data['Building String'] == 'hameetman') & (data['Meter Name'].str.contains('EM') == True)]
meter = meters.iloc[0]['Meter Name'] #TODO chooses the first meter from a building (aggregation/summing details still unclear)
measurement = 'kW'
jace = str(data[data['Meter Name'] == meter]['Jace'].values[0])
filename = download_directory  + meter + '/' + jace + '_' + meter + '_' + measurement + '.csv'
df1 = pd.read_csv(filename)


layout = html.Div([ 

        html.Div([
            
            dcc.Graph(
                id='map',
                clickData = {'points': [{'location': 'Beckman Behavioral Biology'}]}
            ),

            html.Div([
                html.Div(
                    dcc.DatePickerRange(
                        min_date_allowed = df1['t'].iloc[0],
                        max_date_allowed = df1['t'].iloc[-1],
                        start_date = date(2022,4,3),
                        end_date = date(2022,4,10),
                        id='date-picker',
                        ), style={'width': '49%' ,'display': 'inline-block'}),

                html.Div(
                    dcc.RadioItems(['kW Usage', 'Meter Outages'], 'kW Usage', id = 'map-view', inline = True), style={'width': '49%','display': 'inline-block'})
            ])

        ], style={'width': '40%', 'display': 'inline-block'}),
      
        html.Div([ #how to make more series data visible?

        	#html.H5('Campus Overview'),
          #  html.Div(dcc.Graph(id='time-series'), style = {'width':'33%', 'height' : 250, 'display':'inline-block', 'margin': {'l': 0, 'b': 0, 't': 0, 'r': 0}}),
          #  html.Div(dcc.Graph(id='time-series1'), style = {'width':'33%', 'height' : 250, 'display':'inline-block', 'margin': {'l': 0, 'b': 0, 't': 0, 'r': 0}}),
          #  html.Div(dcc.Graph(id='time-series2'), style = {'width':'33%', 'height' : 250, 'display':'inline-block', 'margin': {'l': 0, 'b': 0, 't': 0, 'r': 0}}),
          #  html.Div(dcc.Graph(id='time-series3'), style = {'width':'33%', 'height' : 250, 'display':'inline-block', 'margin': {'l': 0, 'b': 0, 't': 0, 'r': 0}}),
          #  html.Div(dcc.Graph(id='time-series4'), style = {'width':'33%', 'height' : 250, 'display':'inline-block', 'margin': {'l': 0, 'b': 0, 't': 0, 'r': 0}}),
          dcc.Graph(id='time-series'),
          dcc.Graph(id='time-series1'),
          dcc.Graph(id='time-series2'),
          dcc.Graph(id='time-series3'),
          dcc.Graph(id='time-series4')
        ], style={'width': '59%', 'float':'right', 'maxHeight': '600px', 'display': 'inline-block' ,"overflow": "scroll"}),

        
])

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

def create_time_series_kW(building_string, start_date, end_date):

    meters = data[(data['Building String'] == building_string) & (data['Meter Name'].str.contains('EM') == True)]
    print(meters, building_string)
    building_name = meters.iloc[0]['Single Line Building Name']
    
    size = df_size(building_string, start_date, end_date)
  
       
    kW = [0 for i in range(size)]
    kVar = [0 for i in range(size)]
    kVA = [0 for i in range(size)]

    for meter in meters['Meter Name']:   
        jace = str(data[data['Meter Name'] == meter]['Jace'].values[0])
        filename = download_directory  + meter + '/' + jace + '_' + meter + '_kW.csv'
        filename1 = download_directory  + meter + '/' + jace + '_' + meter + '_kVar.csv'
        df1 = pd.read_csv(filename)
        df2 = pd.read_csv(filename1)
        mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
        df1 = df1.loc[mask] 
        mask = (df2['t'] > start_date) & (df2['t'] <= end_date)
        df2 = df2.loc[mask] 

        for i in range(size):
            if df1.iloc[i]['v'] != -1: #meter is stale
                kW[i] += df1.iloc[i]['v']    
            if df2.iloc[i]['v'] != -1:
                kVar[i] += df2.iloc[i]['v'] 
               
            if df1.iloc[i]['v'] != -1 and df2.iloc[i]['v'] != -1:
                kVA[i] +=  (df1.iloc[i]['v']**2 + df2.iloc[i]['v']**2)**0.5
            
    df1['kW_sums'] = kW
    df1['kVar_sums'] = kVar
    df1['kVA_sums'] = kVA


    fig_kW = px.line(df1, x="t", y="kW_sums")
    fig_kW.update_layout(title= building_name + ' kW Usage', xaxis_title='Time', yaxis_title= 'kW')

    fig_kVar = px.line(df1, x="t", y="kVar_sums")
    fig_kVar.update_layout(title= building_name + ' kVar', xaxis_title='Time', yaxis_title= 'kVar')

    fig_kVA = px.line(df1, x="t", y="kVA_sums")
    fig_kVA.update_layout(title= building_name + ' kVA', xaxis_title='Time', yaxis_title= 'kVA')


    return time_series_style(fig_kW),time_series_style(fig_kVar), time_series_style(fig_kVA)

def create_time_series_Amps(name, building_string, start_date, end_date):
    fig = go.Figure()
    for char in 'ABC': #downloads respective amps data and add traces to the graph
        filename = directory_base + 'buildings_aggregated/' + building_string + '/' + building_string + '_Amps' + char + '_sum.csv'
        df1 = pd.read_csv(filename)
        mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
        df1 = df1.loc[mask] 
        fig = fig.add_trace(go.Scatter(x = df1["t"], y = df1["v"], name = "Amps" + char))

    fig.update_layout(title= name + ' Amps', xaxis_title='Time', yaxis_title= 'Amps')
    return time_series_style(fig)

def create_time_series_Volts(name, building_string, start_date, end_date):
    fig = go.Figure()
    for chars in ['AB' , 'BC' , 'CA']: #download respective Volts data and add traces to the graph
        try:
            filename = directory_base + 'buildings_aggregated/' + building_string + '/' + building_string + '_Volts' + chars + '_ave.csv'
            df1 = pd.read_csv(filename)
            mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
            df1 = df1.loc[mask]
            fig = fig.add_trace(go.Scatter(x = df1["t"], y = df1["v"], name = "Volts" + chars)) 
        except:
            pass

    fig.update_layout(title= name + ' Volts', xaxis_title='Time', yaxis_title= 'Volts')

    return time_series_style(fig)


@callback(
    Output('time-series', 'figure'),
    Output('time-series1','figure'),
    Output('time-series2', 'figure'),
    Output('time-series3','figure'),
    Output('time-series4', 'figure'),

    Input('map', 'clickData'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date')

)

def update_shown_timeseries(clickData, start_date, end_date):
    name = clickData['points'][0]['location']
    building_string = df[df['name'] == name]['Building String'].values[0]
    one, two, three = create_time_series_kW(building_string, start_date, end_date)
    return one, two, three, create_time_series_Amps(name, building_string, start_date, end_date), create_time_series_Volts(name, building_string, start_date, end_date)

def update_kW(df, start_date, end_date):
    '''Loops through all building and updates the kW column of the df, to be used for map coloring'''

    kW = []
    for building in df['name'].values:
        try:
            building_string = df[df['name'] == building]['Building String'].values[0]   
            meters = data[(data['Building String'] == building_string) & (data['Meter Name'].str.contains('EM') == True)]
            meter = meters.iloc[0]['Meter Name']#TODO chooses the first meter from a building (aggregation/summing details still unclear)
            measurement = 'kW'
            jace = str(data[data['Meter Name'] == meter]['Jace'].values[0])
            filename = download_directory + meter + '/' + jace + '_' + meter + '_' + measurement + '.csv'
            df1 = pd.read_csv(filename)
            mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
            df1 = df1.loc[mask]  #downloads the information for kW within the start and end date
            if df1['v'].mean() == 0:
                kW.append(0)
            elif df1['v'].mean() > 0:
                kW.append(math.log10(df1['v'].mean())) #appends kW mean within time range to the df
            else:
                kW.append(-0.1)
        except:
            kW.append(-0.1)
    df['kW (log)'] = kW

def update_outages(df, start_date, end_date):
    '''Loops through all building and updates the outage percentage column of the df, to be used for map coloring'''
    tic = time.perf_counter()
    outage_pct = []
    for building in df['name'].values:
        
        building_string = df[df['name'] == building]['Building String'].values[0] 
      
        if type(building_string) != str:
            print(building + "string is probably nan")
            outage_pct.append(-0.1)
            continue
        
        filename = directory_base + 'buildings_aggregated/' + building_string + '/' + building_string + '_EM_outages.csv'
        try:
            df1 = pd.read_csv(filename)
        except:
            print(building)
            outage_pct.append(-0.1)
            continue
        
        mask = (df1['t'] > start_date) & (df1['t'] <= end_date)
        df1 = df1.loc[mask] #downloads the information for kW within the start and end date
        if df1['outage percent'].mean() >= 0:
            outage_pct.append(1 - df1['outage percent'].mean())
        else:
            print("wtf"+ str(df1['outage percent'].mean()))
            outage_pct.append(-0.5)
          
       
    df['Outage Percentage'] = outage_pct
    toc = time.perf_counter()
    print(toc-tic)




@callback(
    Output('map', 'figure'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date'),
    Input('map-view', 'value'),
)

def update_map(start_date, end_date, map_pick):
    
    if map_pick == 'kW Usage': 
        update_kW(df,start_date, end_date)
        fig = px.choropleth_mapbox(df, geojson = gj, 
            color = df["kW (log)"],
            locations= "name", featureidkey = "properties.name", width = 600, height = 600, 
            center={"lon":-118.1252736595467, "lat": 34.1377288162599 },
            mapbox_style="carto-positron", zoom=15,color_continuous_scale=[(0, "gray"), (0.00001, "green"), (0.5,"yellow"), (1, "red")])
            

        fig.update_geos(fitbounds="locations", visible=True)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0} , paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig.update_layout(coloraxis_colorbar=dict(title="Kilowatt Usage (log)",tickvals=[1,2,3,4],ticktext=["10", "100", "1K", "10K"]))
    else: 
        update_outages(df,start_date, end_date)
        fig = px.choropleth_mapbox(df, geojson = gj, range_color=(-0.1,1),
            color = df["Outage Percentage"], custom_data= ['No Data' for i in range(len(df)) if df['Building String'].iloc[i] == ""],
            locations= "name", featureidkey = "properties.name", width = 600, height = 600,
            center={"lon":-118.1252736595467, "lat": 34.1377288162599 }, hover_data=["name"],
            mapbox_style="carto-positron", zoom=15, color_continuous_scale=[(0, "gray"), (0.00001, "green"), (0.5,"yellow"), (1, "red")])
        fig.update_layout(coloraxis_colorbar=dict(title="Meter Outage Percentage",tickvals=[0,0.5,1]))

        
       


        '''  fig.add_trace(px.choropleth_mapbox(no_match, geojson = gj, 
            color = no_match["Building String"],
            locations= "name", featureidkey = "properties.name", width = 600, height = 600,
            center={"lon":-118.1252736595467, "lat": 34.1377288162599 },mapbox_style="carto-positron", zoom=15,color_continuous_scale= 'rdylgn_r'
            ))
            '''

        fig.update_geos(fitbounds="locations", visible=True)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0} , paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
   

    
    return fig

