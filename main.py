import pandas as pd
import numpy as np
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Load the dataset
data = pd.read_csv('trend_indicators.csv')
data['Date'] = pd.to_datetime(data['Date'])

def getValue(index):
    if index >= len(data):
        return None
    row = data.iloc[index]
    return [row['Date'], row['Date'].timestamp(), row['Price'], row['Trend Indicator']]

def getBalanceAsset(index, balance_df):
    if index < 0 or index >= len(balance_df):
        return None
    return balance_df.iloc[index]

def rebalancePortfolio(index, target_btc_ratio, timestamp, usdtBalance, btcBalance, balance_df):
    value = getValue(index)
    if value is None or len(value) < 4:
        print(f"No data available for index {index}. Skipping.")
        return usdtBalance, btcBalance, balance_df

    currentBTCPrice = value[2]
    total_value = usdtBalance + (btcBalance * currentBTCPrice)
    target_btc_value = total_value * target_btc_ratio
    target_usdt_value = total_value * (1 - target_btc_ratio)

    btcBalance = target_btc_value / currentBTCPrice
    usdtBalance = target_usdt_value
    btcValue = btcBalance * currentBTCPrice
    finalValue = usdtBalance + btcValue

    new_entry = pd.DataFrame({
        'timestamp': [timestamp],
        'usdtBalance': [usdtBalance],
        'bitcoinBalance': [btcBalance],
        'bitcoinValue': [btcValue],
        'assetValue': [finalValue]
    })
    balance_df = pd.concat([balance_df, new_entry], ignore_index=True)

    return usdtBalance, btcBalance, balance_df

def updateBitcoinValue(index, balance_df):
    value = getValue(index)
    if value is None or len(value) < 4:
        print(f"No data available for index {index}. Skipping.")
        return balance_df

    balance = getBalanceAsset(index-1, balance_df)
    if balance is None or len(balance) < 5:
        print(f"No data available for index {index}. Skipping.")
        return balance_df

    currentBTCPrice = value[2]
    currentTimestamp = value[1]
    lastUSDTAmount = float(balance['usdtBalance'])
    lastBTCAmount = float(balance['bitcoinBalance'])
    currentBTCValue = lastBTCAmount * currentBTCPrice
    totalAmount = currentBTCValue + lastUSDTAmount

    new_entry = pd.DataFrame({
        'timestamp': [currentTimestamp],
        'usdtBalance': [lastUSDTAmount],
        'bitcoinBalance': [lastBTCAmount],
        'bitcoinValue': [currentBTCValue],
        'assetValue': [totalAmount]
    })
    balance_df = pd.concat([balance_df, new_entry], ignore_index=True)

    return balance_df

def strategy1(start_date, end_date, initial_balance):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter data by date range
    filtered_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
    balance_df = pd.DataFrame(columns=['timestamp', 'usdtBalance', 'bitcoinBalance', 'bitcoinValue', 'assetValue'])

    usdtBalance = initial_balance
    bitcoinBalance = 0.0

    if not filtered_data.empty:
        initial_value = getValue(filtered_data.index[0])
        timestamp = initial_value[1]
        initial_trend = initial_value[3]
        if initial_trend == 0:
            init_perc = 0.5
        elif initial_trend == 0.5:
            init_perc = 0.75
        elif initial_trend == -0.5:
            init_perc = 0.25
        elif initial_trend == 1:
            init_perc = 1
        elif initial_trend == -1:
            init_perc = 0
        usdtBalance, bitcoinBalance, balance_df = rebalancePortfolio(filtered_data.index[0], init_perc, timestamp, usdtBalance, bitcoinBalance, balance_df)

        for i in range(1, len(filtered_data)):
            valueNow = getValue(filtered_data.index[i])
            valueThen = getValue(filtered_data.index[i-1])
            currentTrend = valueNow[3]
            lastTrend = valueThen[3]
            if currentTrend == lastTrend:
                balance_df = updateBitcoinValue(filtered_data.index[i], balance_df)
            else:
                balanceLast = getBalanceAsset(len(balance_df) - 1, balance_df)
                usdtBalance = float(balanceLast['usdtBalance'])
                bitcoinBalance = float(balanceLast['bitcoinBalance'])
                currTimestamp = valueNow[1]
                if currentTrend == 0:
                    usdtBalance, bitcoinBalance, balance_df = rebalancePortfolio(filtered_data.index[i], 0.5, currTimestamp, usdtBalance, bitcoinBalance, balance_df)
                elif currentTrend == 0.5:
                    usdtBalance, bitcoinBalance, balance_df = rebalancePortfolio(filtered_data.index[i], 0.75, currTimestamp, usdtBalance, bitcoinBalance, balance_df)
                elif currentTrend == -0.5:
                    usdtBalance, bitcoinBalance, balance_df = rebalancePortfolio(filtered_data.index[i], 0.25, currTimestamp, usdtBalance, bitcoinBalance, balance_df)
                elif currentTrend == 1:
                    usdtBalance, bitcoinBalance, balance_df = rebalancePortfolio(filtered_data.index[i], 1, currTimestamp, usdtBalance, bitcoinBalance, balance_df)
                elif currentTrend == -1:
                    usdtBalance, bitcoinBalance, balance_df = rebalancePortfolio(filtered_data.index[i], 0, currTimestamp, usdtBalance, bitcoinBalance, balance_df)


    return balance_df

def strategy2(start_date, end_date, initial_balance):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter data by date range
    filtered_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
    balance_df = pd.DataFrame(columns=['timestamp', 'usdtBalance', 'bitcoinBalance', 'bitcoinValue', 'assetValue'])

    usdtBalance = initial_balance
    bitcoinBalance = 0.0

    if not filtered_data.empty:
        initial_value = getValue(filtered_data.index[0])
        timestamp = initial_value[1]
        initial_trend = initial_value[3]
        if initial_trend in [0, -0.5, 0.5]:
            init_perc = 0.5
        elif initial_trend == 1:
            init_perc = 1
        elif initial_trend == -1:
            init_perc = 0
        usdtBalance, bitcoinBalance, balance_df = rebalancePortfolio(filtered_data.index[0], init_perc, timestamp, usdtBalance, bitcoinBalance, balance_df)

        for i in range(3, len(filtered_data)):
            valueNow = getValue(filtered_data.index[i])
            valueThen = getValue(filtered_data.index[i-1])
            currentTrend = valueNow[3]
            lastTrend = valueThen[3]
            if currentTrend == lastTrend:
                balance_df = updateBitcoinValue(filtered_data.index[i], balance_df)
            else:
                balanceLast = getBalanceAsset(len(balance_df) - 1, balance_df)
                usdtBalance = float(balanceLast['usdtBalance'])
                bitcoinBalance = float(balanceLast['bitcoinBalance'])
                currTimestamp = valueNow[1]
                if currentTrend in [0, -0.5, 0.5]:
                    usdtBalance, bitcoinBalance, balance_df = rebalancePortfolio(filtered_data.index[i], 0.5, currTimestamp, usdtBalance, bitcoinBalance, balance_df)
                elif currentTrend == 1:
                    usdtBalance, bitcoinBalance, balance_df = rebalancePortfolio(filtered_data.index[i], 1, currTimestamp, usdtBalance, bitcoinBalance, balance_df)
                elif currentTrend == -1:
                    usdtBalance, bitcoinBalance, balance_df = rebalancePortfolio(filtered_data.index[i], 0, currTimestamp, usdtBalance, bitcoinBalance, balance_df)


    return balance_df

def calculate_drawdown(balance_df):
    balance_df['assetValue'] = balance_df['assetValue'].astype(float)
    peak = balance_df['assetValue'].expanding(min_periods=1).max()
    drawdown = balance_df['assetValue'] - peak
    drawdown_percentage = drawdown / peak * 100
    max_drawdown = drawdown.min()
    max_drawdown_percentage = drawdown_percentage.min()

    return max_drawdown, max_drawdown_percentage

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("EWMA Backtesting"),
    
    html.Div([
        html.Label("Select Start Date"),
        dcc.DatePickerSingle(
            id='start-date-picker',
            min_date_allowed=data['Date'].min(),
            max_date_allowed=data['Date'].max(),
            initial_visible_month=data['Date'].min(),
            date=data['Date'].min()
        ),
    ]),
    
    html.Div([
        html.Label("Select End Date"),
        dcc.DatePickerSingle(
            id='end-date-picker',
            min_date_allowed=data['Date'].min(),
            max_date_allowed=data['Date'].max(),
            initial_visible_month=data['Date'].max(),
            date=data['Date'].max()
        ),
    ]),
    
    html.Div([
        html.Label("Initial Amount (USDT)"),
        dcc.Input(id='initial-amount', type='number', value=10000)
    ]),
    
    html.Div([
        html.Label("Select Strategy"),
        dcc.Dropdown(
            id='strategy-dropdown',
            options=[
                {'label': 'NOBI Adjustment', 'value': 'strategy1'},
                {'label': 'Original Coindesk', 'value': 'strategy2'}
            ],
            value='strategy1'
        )
    ]),
    
    html.Button('Run Strategy', id='run-button', n_clicks=0),
    
    dcc.Graph(id='portfolio-value-graph'),
    
    html.H2("Transaction Details"),
    dash_table.DataTable(
        id='transaction-table',
        columns=[
            {'name': 'Timestamp', 'id': 'timestamp'},
            {'name': 'USDT Balance', 'id': 'usdtBalance'},
            {'name': 'Bitcoin Balance', 'id': 'bitcoinBalance'},
            {'name': 'Bitcoin Value', 'id': 'bitcoinValue'},
            {'name': 'Asset Value', 'id': 'assetValue'}
        ],
        data=[],
        page_size=10
    ),
    
    html.H2("Drawdown Details"),
    html.Div(id='drawdown-details')
])

@app.callback(
    Output('portfolio-value-graph', 'figure'),
    Output('transaction-table', 'data'),
    Output('drawdown-details', 'children'),
    Input('run-button', 'n_clicks'),
    Input('start-date-picker', 'date'),
    Input('end-date-picker', 'date'),
    Input('initial-amount', 'value'),
    Input('strategy-dropdown', 'value')
)
def update_graph(n_clicks, start_date, end_date, initial_amount, strategy):
    if n_clicks > 0:
        if strategy == 'strategy1':
            balance_df = strategy1(start_date, end_date, initial_amount)
        else:
            balance_df = strategy2(start_date, end_date, initial_amount)

        if balance_df.empty:
            return go.Figure(), [], "No transactions occurred during this period."

        balance_df['timestamp'] = pd.to_datetime(balance_df['timestamp'], unit='s')
        fig = px.line(balance_df, x='timestamp', y='assetValue', title='Portfolio Growth Over Time')
        fig.update_xaxes(title='Date')
        fig.update_yaxes(title='Portfolio Value (USDT)')

        table_data = balance_df.to_dict('records')
        
        max_drawdown, max_drawdown_percentage = calculate_drawdown(balance_df)
        drawdown_text = f"Max Drawdown: {max_drawdown:.2f} USDT ({max_drawdown_percentage:.2f}%)"

        return fig, table_data, drawdown_text

    return go.Figure(), [], ""

if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0")
