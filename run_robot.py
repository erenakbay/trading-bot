import time as true_time
import pprint
import pathlib
import operator
import pandas as pd

from datetime import datetime
from datetime import timedelta
from configparser import ConfigParser

from robot.robot import Robot
from robot.indicators import Indicators

# Grab the config file
config = ConfigParser()
config.read('configs/config.ini')

CLIENT_ID = config.get('main', 'CLIENT_ID')
REDIRECT_URI = config.get('main', 'REDIRECT_URI')
CREDENTIALS_PATH = config.get('main', 'JSON_PATH')
ACCOUNT_NUMBER = config.get('main', 'ACCOUNT_NUMBER')

# Initialize the robot
trading_robot = Robot(
    client_id=CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    credentials_path=CREDENTIALS_PATH,
    trading_account=ACCOUNT_NUMBER,
    paper_trading=True
)

# Create the portfolio
trading_robot_portfolio = trading_robot.create_portfolio()

# Add positions to the portfolio
multiple_positions = [
    {
        'asset_type': 'equity',
        'quantity': 2,
        'purchase_price': 4.00,
        'symbol': 'TSLA',
        'purchase_date': datetime.now()
    },
    {
        'asset_type': 'equity',
        'quantity': 2,
        'purchase_price': 4.00,
        'symbol': 'AAPL',
        'purchase_date': datetime.now()
    }
]

# Add the positions to the portfolio
new_positions = trading_robot.portfolio.add_positions(positions=multiple_positions)
pprint.pprint(new_positions)

# Add a single position
trading_robot.portfolio.add_position(
    symbol='MSFT',
    asset_type='equity',
    purchase_date=datetime.now(),
    quantity=3,
    purchase_price=10.00
)
pprint.pprint(trading_robot.portfolio.positions)

# Check if a regular market is open
if trading_robot.regular_market_open:
    print("The regular market is open")
else:
    print("The regular market is closed")

# Check if the pre-market is open
if trading_robot.pre_market_open:
    print("The pre-market is open")
else:
    print("The pre-market is closed")

# Check if the post-market is open
if trading_robot.post_market_open:
    print("The post-market is open")
else:
    print("The post-market is closed")

# Grab teh current quote in the portfolio
current_quote = trading_robot.grab_current_quotes()
# pprint.pprint(current_quote

# Define our date range
end_date = datetime.today()
start_date = end_date - timedelta(days=30)

# Grab the historical prices
historical_prices = trading_robot.grab_historical_prices(
    start=start_date,
    end=end_date,
    bar_size=1,
    bar_type='minute',
)

# convert the data to a stock frame
stock_frame = trading_robot.create_stock_frame(data=historical_prices['aggregated'])

# Print the stock frame
pprint.pprint(stock_frame.frame.head(n=20))

# Create a new Trade Object.
new_trade = trading_robot.create_trade(
    trade_id='long_tsla',
    enter_or_exit='enter',
    long_or_short='short',
    order_type='lmt',
    price=150.00
)

# Make it Good Till Cancel.
new_trade.good_till_cancel(cancel_time=datetime.now() + timedelta(minutes=90))

# Change the session
new_trade.modify_session(session='am')

# Add an Order Leg.
new_trade.instrument(
    symbol='TSLA',
    quantity=2,
    asset_type='EQUITY'
)

# Add a Stop Loss Order with the Main Order.
new_trade.add_stop_loss(
    stop_size=.10,
    percentage=False
)

# Print out the order.
pprint.pprint(new_trade.order)


# create a new indicator client
indicator_client = Indicators(price_data_frame=stock_frame)

# Add the RSI Indicator
indicator_client.rsi(period=14)

# Add a 200 day simple moving average
indicator_client.sma(period=200)

# Add a 50 day exponential moving average
indicator_client.ema(period=50)

# add a signal to check for 
indicator_client.set_indicator_signals(
    indicator='rsi',
    buy=40,
    sell=20,
    condition_buy=operator.ge,
    condition_sell=operator.le
)

# Define the trade strategy
trades_dict = {
    'TSLA': {
        'trade_func': trading_robot.trades['long_tsla'],
        'trade_id': trading_robot.trades['long_tsla'].trade_id
    }
}

while True:

    # Grab the latest bar
    latest_bars = trading_robot.get_latest_bar()

    # Add the latest bars to the stock frame
    stock_frame.add_rows(data=latest_bars)

    # Update the indicators
    indicator_client.refresh()

    print("="*50)
    print("Current StockFrame")
    print("-"*50)
    print(stock_frame.symbol_groups.tail())
    print("-"*50)
    print("")

    # Check for signals.
    signals = indicator_client.check_signals()

    # Execute Trades.
    trading_robot.execute_signals(signals=signals,trades_to_execute=trades_dict)

    # Grab the last bar.
    last_bar_timestamp = trading_robot.stock_frame.frame.tail(1).index.get_level_values(1)

    # Wait till the next bar.
    trading_robot.wait_till_next_bar(last_bar_timestamp=last_bar_timestamp)
