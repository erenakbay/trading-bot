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
pprint.pprint(current_quote) 
