#!/usr/bin/env python
from flask import Flask, render_template, flash, request, jsonify, Markup
# added code to avoid Tkinter errors
import matplotlib
matplotlib.use('agg')
import io, base64, os
import pandas as pd
import numpy as np

# default traveler constants
DEFAULT_BUDGET = 10000
TRADING_DAYS_LOOP_BACK = 90
INDEX_SYMBOL = ['^DJI']
STOCK_SYMBOLS = ['BA','GS','UNH','MMM','HD','AAPL','MCD','IBM','CAT','TRV']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# global variables
stock_data_df = None

app = Flask(__name__)
 

def prepare_pivot_market_data_frame():
    # prep data
    # loop through each stock and load csv
    stock_data_list = []
    for stock in INDEX_SYMBOL + STOCK_SYMBOLS:
        src = os.path.join(BASE_DIR, stock + '.csv')
        tmp = pd.read_csv(src)
        tmp['Symbol'] = stock
        tmp = tmp[['Symbol', 'Date', 'Adj Close']]
        stock_data_list.append(tmp)

    stock_data = pd.concat(stock_data_list)

    stock_data = stock_data.pivot('Date','Symbol')
    stock_data.columns = stock_data.columns.droplevel()
    stock_data = stock_data.tail(90)

    return (stock_data)


@app.before_first_request
def startup():
    global stock_data_df

     # prepare pair trading data
    stock_data_df = prepare_pivot_market_data_frame()


@app.route("/", methods=['POST', 'GET'])
def get_pair_trade():
    if request.method == 'POST':
        selected_budget = request.form['selected_budget']
        # make sure the field isn't blank
        if selected_budget == '':
            selected_budget = 10000

        # calculate widest spread
        stock1 = '^DJI'
        last_distance_from_index = {}
        temp_series1 = stock_data_df[stock1].pct_change().cumsum()
        for stock2 in list(stock_data_df):
            # no need to process itself
            if (stock2 != stock1):
                temp_series2 = stock_data_df[stock2].pct_change().cumsum()
                # we are subtracting the stock minus the index, if stock is strong compared
                # to index, we assume a postive value
                diff = list(temp_series2 - temp_series1)
                last_distance_from_index[stock2] = diff[-1]

        weakest_symbol = min(last_distance_from_index.items(), key=lambda x: x[1])
        strongest_symbol = max(last_distance_from_index.items(), key=lambda x: x[1])

        # budget trade size
        short_symbol = strongest_symbol[0]
        short_last_close = stock_data_df[strongest_symbol[0]][-1]

        long_symbol = weakest_symbol[0]
        long_last_close = stock_data_df[weakest_symbol[0]][-1]

        return render_template('index.html',
            short_symbol = short_symbol,
            long_symbol = long_symbol,
            short_last_close = round(short_last_close,2),
            short_size = round((float(selected_budget) * 0.5) / short_last_close,2),
            long_last_close = round(long_last_close,2),
            long_size = round((float(selected_budget) * 0.5) / long_last_close,2),
            selected_budget = selected_budget)

    else:
        # set default passenger settings
        return render_template('index.html',
            short_symbol = "None",
            long_symbol = "None",
            short_last_close = 0,
            short_size = 0,
            long_last_close = 0,
            long_size = 0,
            selected_budget = DEFAULT_BUDGET)

if __name__=='__main__':
    app.run(debug=True)


