#!/usr/bin/env python
from flask import Flask, render_template, request, jsonify, Markup
# added code to avoid Tkinter errors
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import io, base64, os
import pandas as pd

# Default financial constants
DEFAULT_BUDGET = 10000
TRADING_DAYS_LOOP_BACK = 90
INDEX_SYMBOL = ['^DJI']
STOCK_SYMBOLS = ['BA','GS','UNH','MMM','HD','AAPL','MCD','IBM','CAT','TRV']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Global variables
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
    stock_data.index = pd.to_datetime(stock_data.index)
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
        short_market_data = stock_data_df[short_symbol].pct_change().cumsum()

        long_symbol = weakest_symbol[0]
        long_last_close = stock_data_df[weakest_symbol[0]][-1]
        long_market_data = stock_data_df[long_symbol].pct_change().cumsum()

        if request.form['submit'] == 'calculate_trade':
            return render_template('index.html',
                short_symbol = short_symbol,
                long_symbol = long_symbol,
                short_last_close = round(short_last_close,2),
                short_size = round((float(selected_budget) * 0.5) / short_last_close,2),
                long_last_close = round(long_last_close,2),
                long_size = round((float(selected_budget) * 0.5) / long_last_close,2),
                selected_budget = selected_budget)
        else:
            # build three charts

            # WEAK SYMBOL - GO LONG
            fig, ax = plt.subplots()
            ax.plot(temp_series1.index, long_market_data)
            plt.suptitle('Overly Bearish - Buy: ' + weakest_symbol[0])

            # rotate dates
            myLocator = mticker.MultipleLocator(2)
            ax.xaxis.set_major_locator(myLocator)
            fig.autofmt_xdate()

            # fix label to only show first and last date
            labels = ['' for item in ax.get_xticklabels()]
            labels[1] = temp_series1.index[0]

            labels[-2] = temp_series1.index[-1]
            ax.set_xticklabels(labels)

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()

            chart1_plot = Markup('<img style="padding:1px; border:1px solid #021a40; width: 80%; height: 300px" src="data:image/png;base64,{}">'.format(plot_url))

            # STRONG SYMBOL - GO SHORT
            fig, ax = plt.subplots()
            ax.plot(temp_series2.index, short_market_data)
            plt.suptitle('Overly Bullish - Sell: ' + strongest_symbol[0])

            # rotate dates
            myLocator = mticker.MultipleLocator(2)
            ax.xaxis.set_major_locator(myLocator)
            fig.autofmt_xdate()

            # fix label to only show first and last date
            labels = ['' for item in ax.get_xticklabels()]
            labels[1] = temp_series2.index[0]

            labels[-2] = temp_series2.index[-1]
            ax.set_xticklabels(labels)

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()

            chart2_plot = Markup('<img style="padding:1px; border:1px solid #021a40; width: 80%; height: 300px" src="data:image/png;base64,{}">'.format(plot_url))

            # DIFFERENCE PLOT
            fig, ax = plt.subplots()
            ax.plot(temp_series2.index, diff)
            # add zero line
            ax.axhline(y=0, color='green', linestyle='-')
            plt.suptitle(strongest_symbol[0] + " Minus " + weakest_symbol[0] + '\n(Overly Bullish Minus Overly Bearish)')

            # rotate dates
            myLocator = mticker.MultipleLocator(2)
            ax.xaxis.set_major_locator(myLocator)
            fig.autofmt_xdate()

            # fix label to only show first and last date
            labels = ['' for item in ax.get_xticklabels()]
            labels[1] = temp_series2.index[0]

            labels[-2] = temp_series2.index[-1]
            ax.set_xticklabels(labels)

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()

            chart_diff_plot = Markup('<img style="padding:1px; border:1px solid #021a40; width: 80%; height: 300px" src="data:image/png;base64,{}">'.format(plot_url))


            return render_template('charts.html',
                chart1_plot = chart1_plot,
                chart2_plot = chart2_plot,
                chart_diff_plot = chart_diff_plot,
                short_symbol = short_symbol,
                long_symbol = long_symbol,
                short_last_close = round(short_last_close,2),
                short_size = round((float(selected_budget) * 0.5) / short_last_close,2),
                long_last_close = round(long_last_close,2),
                long_size = round((float(selected_budget) * 0.5) / long_last_close,2),
                selected_budget = selected_budget)

    else:
        # First time visit - return default settings
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


