import flask
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
from covid_chart import create_covid_layout, register_covid_callbacks
from influenza_chart import create_influenza_layout, register_influenza_callbacks
from rsv_chart import create_rsv_layout, register_rsv_callbacks
from covid_map_chart import create_covid_map_layout, register_covid_map_callbacks

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # html.Div([
    #     html.A("COVID Admissions Dashboard | ", href="/covid"),
    #     html.A("Influenza Time Series Prediction | ", href="/influenza"),
    #     html.A("RSV Time Series Prediction", href="/rsv"),
    # ], style={'padding': '20px'}),
    html.Div(id='page-content', style={'padding': '20px'})
])

# --- Callback to render the appropriate page ---
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/covid':
        return create_covid_layout()
    elif pathname == '/influenza':
        return create_influenza_layout()
    elif pathname=='/rsv':
        return create_rsv_layout()
    elif pathname=='/covidmap':
        return create_covid_map_layout()
    else:
        return html.Div("Welcome to the Dashboard Home. Please select a chart from the navigation.")

# --- Register callbacks for both dashboards ---
register_covid_callbacks(app)
register_influenza_callbacks(app)
register_rsv_callbacks(app)
register_covid_map_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=False)

