import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import os


file_path = "../datasets/germ_watch_data/germwatch_covid_hospitalizations_20241029_140153.csv"
covid_df = pd.read_csv(file_path)


covid_df_filtered = covid_df[["EMPI","COLLECTED_DTS","ORGANIZATION_NM", "CHILDRENS_HOSPITAL"]]
covid_df_filtered.rename(columns={"COLLECTED_DTS": "DATE"}, inplace=True)
covid_df_filtered['DATE'] = pd.to_datetime(covid_df_filtered['DATE'])
covid_df_filtered["ADMISSIONS"] = covid_df_filtered.groupby(["DATE", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"])["EMPI"].transform('count')
covid_df_filtered.set_index('DATE',inplace=True)

org_options = [{'label': org, 'value': org} for org in covid_df_filtered['ORGANIZATION_NM'].unique()]
org_options.insert(0, {'label': 'All', 'value': 'All'})

hospital_options = [{'label': str(hosp), 'value': hosp} for hosp in covid_df_filtered['CHILDRENS_HOSPITAL'].unique()]
hospital_options.insert(0, {'label': 'All', 'value': 'All'})

time_options = [{'label':time_format,'value':time_format[0]} for time_format in ['Week','Yearly']]
time_options.insert(0, {'label': 'Month', 'value': 'M'})

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Monthly Admissions Dashboard", style={'textAlign': 'center'}),

    # Dropdown for Organization Name
    html.Label("Select Organization:"),
    dcc.Dropdown(id='org_filter', options=org_options, value='All', clearable=False),

    # Dropdown for Children's Hospital
    html.Label("Children's Hospital Filter:"),
    dcc.Dropdown(id='hospital_filter', options=hospital_options, value='All', clearable=False),
    
    # Dropdown for granularity
    html.Label("Timeframe Filter:"),
    dcc.Dropdown(id='time_filter', options=time_options, value='M', clearable=False),

    # Graph
    dcc.Graph(id='admissions_graph')
])


@app.callback(
    Output('admissions_graph', 'figure'),
    [Input('time_filter','value'),
        Input('org_filter', 'value'),
     Input('hospital_filter', 'value')]
)
def update_graph(selected_time, selected_org, selected_hospital):
    covid_df_filtered_copy = covid_df_filtered.copy()
    filtered_df = (
        covid_df_filtered_copy
        .groupby([pd.Grouper(freq=selected_time), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL'])
        .agg({'ADMISSIONS': 'sum'})
        .reset_index()
    )

    # Apply filters
    if selected_org != 'All':
        filtered_df = filtered_df[filtered_df['ORGANIZATION_NM'] == selected_org]
    if selected_hospital != 'All':
        filtered_df = filtered_df[filtered_df['CHILDRENS_HOSPITAL'] == selected_hospital]

    # Create the plot
    fig = px.line(
        filtered_df,
        x='DATE',
        y='ADMISSIONS',
        color='ORGANIZATION_NM',
        line_group='CHILDRENS_HOSPITAL',
        markers=True,
        title="Monthly Admissions Over Time"
    )
    fig.update_xaxes(type='category')  # Keeps months formatted properly

    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
