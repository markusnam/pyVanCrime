from dash import dash, html, dcc, dash_table, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import altair as alt

# read data
df = pd.read_csv("../data/raw/crimedata_csv_AllNeighbourhoods_AllYears.csv")

# data wrangling - drop na, remove the latest year (not full year in general), remove x=0 and y=0
max_year = df['YEAR'].max()
query_str = 'YEAR < ' + str(max_year) + ' & X != 0 & Y != 0'
df = df.dropna().query(query_str)

# get year range
min_year = df['YEAR'].min()
max_year = df['YEAR'].max()

# setup dashboard layout
# app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app = dash.Dash(external_stylesheets=[dbc.themes.SOLAR])
server = app.server

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                html.H1(html.Mark('pyVanCrime - Vancouver Crime Data')),
                html.H1(id = 'year-range')
            ]
        ),
        dbc.Row(
            html.Hr()
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5(html.U('Select Year Range:')),
                        dcc.RangeSlider(
                            id='year-slider',
                            min=min_year,
                            max=max_year,
                            value=[
                                min_year,
                                max_year
                            ],
                            marks={
                                str(min_year): str(min_year),
                                str(max_year): str(max_year)
                            },
                            allowCross=False,
                            tooltip={'placement': 'bottom', 'always_visible': True},
                            step=1
                        ),
                        html.Br(),
                        html.Br(),
                        html.H5(html.U('Select Neighbourhood')),
                        dcc.Dropdown(
                            id = 'nhood-dropdown',
                            options = [{'label': n, 'value': n} for n in np.sort(df['NEIGHBOURHOOD'].unique())],
                            value = [],
                            multi = True,
                            searchable = True,
                            placeholder = 'Select Neighbourhood(s)',
                            style={'color': 'black'}
                        ),
                        html.Button('Select All', id='select-all'),
                        html.Hr(),
                        dcc.Store(id='memory-output')
                    ],
                    width = 2
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H5('Average Month Count'),
                                        html.Iframe(
                                            id='month-plot',
                                            style={
                                                "border-width": "0",
                                                "width": "140%",
                                                "height": "360px"
                                            }
                                        )
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        html.H5('Average Weekday Count'),
                                        html.Iframe(
                                            id='weekday-plot',
                                            style={
                                                "border-width": "0",
                                                "width": "140%",
                                                "height": "360px"
                                            }
                                        )
                                    ]
                                )
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H5('Total Count by Crime Type',
                                                style={'text-align': 'center'}),
                                        dash_table.DataTable(
                                            id='type-table',
                                            columns=[
                                                {'name': 'TYPE', 'id': 'TYPE'},
                                                {'name': 'COUNT', 'id': 'COUNT'}
                                            ],
                                            style_table={
                                                'width': '50%',
                                                'margin-left': 'auto',
                                                'margin-right': 'auto'
                                            },
                                            style_header={
                                                'backgroundColor': 'lightgrey',
                                                'fontWeight': 'bold'
                                            }
                                        )
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        html.H5('Total Count by Neighbourhood',
                                                style={'text-align': 'center'}),
                                        dash_table.DataTable(
                                            id='nhood-table',
                                            columns=[
                                                {'name': 'NEIGHBOURHOOD', 'id': 'NEIGHBOURHOOD'},
                                                {'name': 'COUNT', 'id': 'COUNT'}
                                            ],
                                            style_table={
                                                'width': '50%',
                                                'margin-left': 'auto',
                                                'margin-right': 'auto'
                                            },
                                            style_header={
                                                'backgroundColor': 'lightgrey',
                                                'fontWeight': 'bold'
                                            }
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ],
    fluid=True
)


@app.callback(
    Output('memory-output', 'data'),
    Input('year-slider', 'value'),
    Input('nhood-dropdown', 'value'),
    priority=1
)
def update_data(year, nhood):
    query_str = ('YEAR >= ' + str(year[0]) +
                ' & YEAR <= ' + str(year[1]) +
                ' & NEIGHBOURHOOD in ' + '@nhood'
    )
    df_selected = df.query(query_str).copy()
    
    return df_selected.to_json()

@app.callback(
    Output('month-plot', 'srcDoc'),
    Input('memory-output', 'data')
)
def update_month_plot(data):
    df_selected = pd.read_json(data)

    if len(df_selected) == 0:
        chart = (
            alt.Chart().mark_text(
                text='Please select Neighbourhood(s).',
                fontSize=24
            ).encode(
                color=alt.value('red')
            ).properties(
                width=450,
                height=250
            )
        )
    
    else:
        date_index = pd.to_datetime(df_selected[['YEAR', 'MONTH', 'DAY']])
        df_selected.loc[:, 'MONTH_ABBR'] = date_index.dt.strftime('%b')

        df_plot = pd.DataFrame(df_selected.groupby(['MONTH', 'MONTH_ABBR']).size(),
                            columns=['COUNT']).reset_index()
        
        chart = (
            alt.Chart(df_plot).mark_bar().encode(
                alt.X("MONTH_ABBR",
                    sort=alt.EncodingSortField('MONTH'),
                    title="Month"),
                alt.Y("COUNT",
                    title="Number of Crimes"),
                tooltip=['COUNT']
            ).properties(
                width=450,
                height=250
            )
        )
    return chart.to_html()

@app.callback(
    Output('weekday-plot', 'srcDoc'),
    Input('memory-output', 'data')
)
def update_weekday_plot(data):
    df_selected = pd.read_json(data)

    if len(df_selected) == 0:
        chart = (
            alt.Chart().mark_text(
                text='Please select Neighbourhood(s).',
                fontSize=24
            ).encode(
                color=alt.value('red')
            ).properties(
                width=450,
                height=250
            )
        )
    
    else:
        date_index = pd.to_datetime(df_selected[['YEAR', 'MONTH', 'DAY']])
        df_selected.loc[:, 'WEEKDAY'] = date_index.dt.strftime('%w')
        df_selected.loc[:, 'WEEKDAY_ABBR'] = date_index.dt.strftime('%a')

        df_plot = pd.DataFrame(df_selected.groupby(['WEEKDAY', 'WEEKDAY_ABBR']).size(),
                            columns=['COUNT']).reset_index()
        
        area = (
            alt.Chart(df_plot).mark_area().encode(
                alt.X("WEEKDAY_ABBR",
                    sort=alt.EncodingSortField('WEEKDAY'),
                    title="Day"),
                alt.Y("COUNT",
                    title="Number of Crimes"),
                color=alt.value('green'),
                tooltip=['COUNT']
            ).properties(
                width=450,
                height=250
            )
        )

        points = (
            alt.Chart(df_plot).mark_point(size=80).encode(
                alt.X("WEEKDAY_ABBR",
                    sort=alt.EncodingSortField('WEEKDAY'),
                    title="Day"),
                alt.Y("COUNT",
                    title="Number of Crimes"),
                fill=alt.value('red'),
                tooltip=['COUNT']
            ).properties(
                width=450,
                height=250
            )
        )

        chart = area + points

    return chart.to_html()

@app.callback(Output('type-table', 'data'),
              Input('memory-output', 'data'))
def on_data_set_type_table(data):
    df_selected = pd.read_json(data)
    
    if len(df_selected) == 0:
        type_df = pd.DataFrame(columns=['TYPE', 'COUNT'])
    else:
        type_df = pd.DataFrame(df_selected.groupby('TYPE').size(),
                     columns=['COUNT']).sort_values(['COUNT', 'TYPE'], ascending=False).reset_index()
        type_df['COUNT'] = type_df['COUNT'].apply(lambda x: '{:,.0f}'.format(x))

    return type_df.to_dict('records')

@app.callback(Output('nhood-table', 'data'),
              Input('memory-output', 'data'))
def on_data_set_nhood_table(data):
    df_selected = pd.read_json(data)
    
    if len(df_selected) == 0:
        nhood_df = pd.DataFrame(columns=['NEIGHBOURHOOD', 'COUNT'])
    else:
        nhood_df = pd.DataFrame(df_selected.groupby('NEIGHBOURHOOD').size(),
                     columns=['COUNT']).sort_values(['COUNT', 'NEIGHBOURHOOD'], ascending=False).reset_index()
        nhood_df['COUNT'] = nhood_df['COUNT'].apply(lambda x: '{:,.0f}'.format(x))

    return nhood_df.to_dict('records')

@app.callback(
    Output('year-range', 'children'),
    Input('year-slider', 'value')
)
def update_year_range(year):    
    return '(from ' + str(year[0]) + ' to ' + str(year[1]) + ')'

@app.callback(
    Output('nhood-dropdown', 'value'),
    Input('select-all', 'n_clicks')
)
def update_dropdown_value(select_clicks):
    if select_clicks is not None and select_clicks > 0:
        return df['NEIGHBOURHOOD'].unique()
    else:
        return dash.no_update
    return 

if __name__ == '__main__':
    app.run_server(debug=True)
