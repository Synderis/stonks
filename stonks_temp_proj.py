# import dash
# from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np

# import pandas_ta as ta
import requests

# dash.register_page(__name__, path="/idek")


def create_dropdown(option, id_value):

    return html.Div(
        [
            html.H4(
                " ".join(id_value.replace("-", " ").split(" ")[:-1]),
                style={"padding": "0px 30px 0px 30px"},
            ),
            dcc.Dropdown(option, id=id_value, value=option[0]),
        ],
        style={"padding": "0px 30px 0px 30px"},
    )


layout = html.Div(
    [
        html.Div(
            [
                create_dropdown(["btcusd", "ethusd", "xrpusd"], "coin-select"),
                create_dropdown(["60", "3600", "86400"], "timeframe-select"),
                create_dropdown(["20", "50", "100"], "num-bars-select"),
            ],
            style={
                "display": "flex",
                "margin": "auto",
                "width": "800px",
                # "justify-content": "space-around",
            },
        ),
        html.Div(
            [
                dcc.RangeSlider(0, 20, 1, value=[0, 20], id="range-slider"),
            ],
            id="range-slider-container",
            style={"width": "800px", "margin": "auto", "padding-top": "30px"},
        ),
        dcc.Graph(
            id="candles",
            figure={
                "data": [go.Candlestick(x=[], open=[], high=[], low=[], close=[])],
                "layout": go.Layout(template="plotly_dark"),
            },
        ),
        # dcc.Graph(id="indicator"),
        dcc.Interval(id="interval", interval=2000),
        dcc.Store(id="ohlc-data"),
    ]
)


@callback(
    Output("ohlc-data", "data"),
    Input("coin-select", "value"),
    Input("timeframe-select", "value"),
    Input("num-bars-select", "value"),
)
def fetch_ohlc_data(coin_pair, timeframe, num_bars):
    # Ensure the timeframe is 60 seconds
    timeframe = "60"

    url = f"https://www.bitstamp.net/api/v2/ohlc/{coin_pair}/"
    params = {
        "step": timeframe,
        "limit": int(num_bars) + 14,
    }
    print(requests.get(url, params=params).json())
    data = requests.get(url, params=params).json()["data"]["ohlc"]
    data = pd.DataFrame(data)
    # print(data.timestamp)
    # print(data.timestamp.dtype)
    data["timestamp"] = pd.to_numeric(data["timestamp"], errors="coerce")

    # Convert Unix timestamps to datetime
    data["timestamp"] = pd.to_datetime(data["timestamp"], unit="s")
    data["timestamp"] = data["timestamp"].dt.tz_localize("UTC")

    # Convert to EST (Eastern Standard Time)
    data["timestamp"] = data["timestamp"].dt.tz_convert("America/New_York")

    return data.to_dict("records")


@callback(
    Output("candles", "extendData"),
    Input("ohlc-data", "data"),
    Input("range-slider", "value"),
)
def extend_candles(ohlc_data, range_values):
    if not ohlc_data:
        return None  # No update if there is no data

    data = pd.DataFrame(ohlc_data)

    # Ensure range_values are within bounds
    max_index = len(data)
    start_index = min(range_values[0], max_index - 1)
    end_index = min(range_values[1], max_index)

    data = data.iloc[start_index:end_index]

    # Extend data only if there are new data points to add
    if data.empty:
        return None

    return (
        {
            "x": [data.timestamp],
            "open": [data.open],
            "high": [data.high],
            "low": [data.low],
            "close": [data.close],
        },
        [0],  # Trace index
        len(data),  # Max points, if needed
    )
