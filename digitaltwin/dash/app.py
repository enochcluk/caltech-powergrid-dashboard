from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px

import dash
import os

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.MINTY])


app.layout = dbc.Container([
    html.Div([
    html.Div(html.H3('Caltech Digital Twin'), style = {'width' : '50%', 'display':'inline-block'}),

    html.Div(
    html.Div(
        [
            html.Div(
                dcc.Link(
                    f"{page['name']}", href=page["relative_path"]
                ),  
                style = {'width' : '30%', 'display':'inline-block'}
            )
            for page in dash.page_registry.values() if page['name'] != ''
         ]
    ), style = {'width' : '50%', 'display':'inline-block'}),

	dash.page_container
])], fluid = True, class_name = "dbc")


if __name__ == '__main__':
    #app.run_server(debug=True)
	app.run(host='0.0.0.0', port = 8050, debug = True)