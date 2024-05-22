import pandas as pd
import numpy as np 
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from matplotlib import pyplot as plt
import seaborn as sns

#Lambdas and NFS
lambdas = [0.5, 0.757858283, 0.870550563, 0.933032992, 0.965936329, 0.982820599]
nfs = [1.0000, 1.0000, 1.0000, 1.0000, 1.0020, 1.0462]

data = pd.read_csv('btc_his.csv')
data['Date'] = pd.to_datetime(data['Date'])
data = data.sort_values(by='Date').reset_index(drop=True)
data['Price'] = data['Price'].str.replace(',', '').astype(float)

def calculate_ewma(prices, lambdas, nf):
    ewma_results = []
    for i in range(len(prices)):
        ewma_results.append((1 - lambdas) * pow(lambdas, i) * float(prices.iloc[i]) * nf)
    return sum(ewma_results)

def sign(x):
    return 1 if x >= 0 else -1

def calculate_trend_indicator(data, lambdas, nfs):
    MA1 = calculate_ewma(data, lambdas[0], nfs[0])  # 1 day
    MA2_5 = calculate_ewma(data, lambdas[1], nfs[1])  # 2.5 days
    MA5 = calculate_ewma(data, lambdas[2], nfs[2])  # 5 days
    MA10 = calculate_ewma(data, lambdas[3], nfs[3])  # 10 days
    MA20 = calculate_ewma(data, lambdas[4], nfs[4])  # 20 days
    MA40 = calculate_ewma(data, lambdas[5], nfs[5])  # 40 days
    MAP1 = sign(MA1 - MA5)
    MAP2 = sign(MA2_5 - MA10)
    MAP3 = sign(MA5 - MA20)
    MAP4 = sign(MA10 - MA40)

    # Debug: print intermediate values
    print(f'MA1: {MA1}, MA2_5: {MA2_5}, MA5: {MA5}, MA10: {MA10}, MA20: {MA20}, MA40: {MA40}')
    print(f'MAP1: {MAP1}, MAP2: {MAP2}, MAP3: {MAP3}, MAP4: {MAP4}')

    result = MAP1 + MAP2 + MAP3 + MAP4
    return result / 4

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Trading Simulator"),
    html.Label("Start Date"),
    dcc.DatePickerSingle(id='start-date', date=data['Date'].min(), display_format='YYYY-MM-DD'),
    html.Label("End Date"),
    dcc.DatePickerSingle(id='end-date', date=data['Date'].max(), display_format='YYYY-MM-DD'),
    html.Label("Amount"),
    dcc.Input(id='amount', type='number', value=1000),
    dcc.Graph(id='portfolio-value'),
])

# Define callback to update plot
@app.callback(
    Output('portfolio-value', 'figure'),
    [Input('start-date', 'date'), Input('end-date', 'date'), Input('amount', 'value')]
)
def update_plot(start_date, end_date, amount):
    # Filter data based on selected date range
    filtered_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)].copy()

    # Calculate trend indicators
    trend_indicators = []
    for i in range(180, len(filtered_data)):
        current_data = filtered_data['Price'][:i]
        current_data = current_data[::-1]
        trend_indicator = calculate_trend_indicator(current_data, lambdas, nfs)
        trend_indicators.append(trend_indicator)

    # Create a new DataFrame for the results
    results = filtered_data[['Date', 'Price']][180:].copy()
    results['Trend Indicator'] = trend_indicators

    # Plot portfolio value over time
    plt.figure(figsize=(10, 5))
    plt.plot(results['Date'], results['Price'] * amount, label='Portfolio Value')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title('Portfolio Value Over Time')
    plt.legend()
    plt.tight_layout()

    return plt.gcf()


if __name__ == '__main__':
    app.run_server(debug=True)
