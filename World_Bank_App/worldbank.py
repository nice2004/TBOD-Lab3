from dash import Dash, html, dcc, Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
from pandas_datareader import wb
import datetime as dt

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

indicators = {
    "IT.NET.USER.ZS": "Individuals using the Internet (% of population)",
    "SG.GEN.PARL.ZS": "Proportion of seats held by women in national parliaments (%)",
    "SH.DYN.MORT": "Mortality rate, under-5 (per 1,000 live births)",
}

# get country name and ISO id for mapping on choropleth
countries = wb.get_countries()
countries["capitalCity"].replace({"": None}, inplace=True)
countries.dropna(subset=["capitalCity"], inplace=True)
countries = countries[["name", "iso3c"]]
countries = countries[countries["name"] != "Kosovo"]
countries = countries[countries["name"] != "Korea, Dem. People's Rep."]
countries = countries.rename(columns={"name": "country"})


def update_wb_data():
    # Retrieve specific world bank data from API
    df = wb.download(
        indicator=(list(indicators)), country=countries["iso3c"], start=2005, end=2016
    )
    df = df.reset_index()
    df.year = df.year.astype(int)

    # Add country ISO3 id to main df
    df = pd.merge(df, countries, on="country")
    df = df.rename(columns=indicators)

    return df


app.layout = dbc.Container(
    [
    dbc.Row(
        dbc.Col(
            [
                html.H1(
                    "Comparison of World Bank Country Data",
                    style={"textAlign": "center"},
                ),
                html.H2(

                    id="time",
                    style={'textAlign': 'center'}
                ),
                dcc.Graph(id="my-choropleth", figure={}),
            ],
            width=12,
        )
    ),
    dbc.Col(
        [
            dbc.Label(
                "output-text",
                id='text',
                className="fw-bold",
                style={"fontSize": 20},
            ),
        ],
        width=4,
    ),
    dbc.Row([
        dbc.Col(
            [
                dbc.Label(
                    "Select Data Set:",
                    className="fw-bold",
                    style={"textDecoration": "underline", "fontSize": 20},
                ),
                dcc.Dropdown(
                    id="i-dropdown",
                    options=[{"label": i, "value": i} for i in indicators.values()],
                    value=list(indicators.values())[0],
                    className="three columns",
                ),
            ],
            width=5,
        ),

        dbc.Col(
            [
                dbc.Label(
                    "Select Years:",
                    className="fw-bold",
                    style={"textDecoration": "underline", "fontSize": 20},
                ),
                dcc.RangeSlider(
                    id="years-range",
                    min=2005,
                    max=2016,
                    step=1,
                    value=[2005, 2006],
                    marks={
                        2005: "2005",
                        2006: "'06",
                        2007: "'07",
                        2008: "'08",
                        2009: "'09",
                        2010: "'10",
                        2011: "'11",
                        2012: "'12",
                        2013: "'13",
                        2014: "'14",
                        2015: "'15",
                        2016: "2016",
                    },
                ),
            ]
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button(
                    id="my-button",
                    children="Submit",
                    n_clicks=0,
                    color="primary",

                ),
                width=12,
                className="fw-bold d-flex justify-content-end"
            ),
        ),

        dcc.Store(id="storage", storage_type="session", data={}),
        dcc.Interval(id="timer", interval=1000 * 10, n_intervals=0),
    ],
    )
        ]
)


@app.callback(Output("storage", "data"),
              Input("timer", "n_intervals"))
def store_data(n_time):
    dataframe = update_wb_data()
    last_fetched = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_frame = dataframe.to_dict("records")
    return {'records': data_frame, 'last_fetched': last_fetched}


@app.callback(
    Output("time", "children"),
    Input("storage", "data"),
)
def update_time(data_storage):
    if 'last_fetched' in data_storage:
        return f'Last Time and Date fetched {data_storage["last_fetched"]}'


# @app.callback(Output('years-range', 'value'),
#               Input("my-button", "n_clicks"),
#               State("years-range", "value"))
# def increment(years_range, n_clicks):
#     if n_clicks > 0:
#         years_range += 1


@app.callback(
    Output("text", "children"),
    Input("my-button", "n_clicks"),
)
def update_output(n_clicks):
    if n_clicks > 0:
        # slider += 1
        return f'Button clicked {n_clicks} times'
    else:
        return ''


@app.callback(
    Output("my-choropleth", "figure"),
    Input("my-button", "n_clicks"),
    Input("storage", "data"),
    State("years-range", "value"),
    State("i-dropdown", "value"),
)
def update_graph(n_clicks, stored_dataframe, years_chosen, indct_chosen):
    dff = pd.DataFrame.from_records(stored_dataframe["records"])
    print(n_clicks)

    if years_chosen[0] != years_chosen[1]:
        dff = dff[dff.year.between(years_chosen[0], years_chosen[1])]
        dff = dff.groupby(["iso3c", "country"])[indct_chosen].mean()
        dff = dff.reset_index()

        fig = px.choropleth(
            data_frame=dff,
            title='number of submits'[n_clicks],
            locations="iso3c",
            color=indct_chosen,
            scope="world",
            hover_data={"iso3c": False, "country": True},
            labels={
                indicators["SG.GEN.PARL.ZS"]: "% parliament women",
                indicators["IT.NET.USER.ZS"]: "pop % using internet",
                indicators['SH.DYN.MORT']: 'Mortality rate, under-5 (per 1,000 live births)',
            },
        )
        fig.update_layout(
            geo={"projection": {"type": "natural earth"}},
            margin=dict(l=50, r=50, t=50, b=50),
        )
        return fig

    if years_chosen[0] == years_chosen[1]:
        dff = dff[dff["year"].isin(years_chosen)]
        fig = px.choropleth(
            data_frame=dff,
            locations="iso3c",
            color=indct_chosen,
            scope="world",
            hover_data={"iso3c": False, "country": True},
            labels={
                indicators["SG.GEN.PARL.ZS"]: "% parliament women",
                indicators["IT.NET.USER.ZS"]: "pop % using internet",
                indicators['SH.DYN.MORT']: 'Mortality rate, under-5 (per 1,000 live births)',
            },
        )
        fig.update_layout(
            geo={"projection": {"type": "natural earth"}},
            margin=dict(l=50, r=50, t=50, b=50),
        )
        return fig


if __name__ == "__main__":
    app.run_server(debug=True)
