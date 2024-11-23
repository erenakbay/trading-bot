import pandas as pdb 

from td.client import TDClient
from td.utils import milliseconds_since_epoch

from datetime import datetime
from datetime import time
from datetime import timezone
from datetime import timedelta

import time as time_true
import pathlib
import json
import pandas as pd

from typing import List
from typing import Dict
from typing import Union
from typing import Optional

from robot.portfolio import Portfolio
from robot.stock_frame import Stockframe
from robot.trades import Trade

class Robot():

    def __init__(self, client_id: str, redirect_uri: str, credentials_path: str = None, trading_account: str = None, paper_trading: bool = True) -> None:

        self.trading_account: str = trading_account
        self.client_id: str = client_id
        self.redirect_uri: str = redirect_uri
        self.credentials_path: str = credentials_path
        self.session: TDClient = self._create_session()
        self.trades: dict = {}
        self.historical_prices: dict = {}
        self.stock_frame = None
        self.paper_trading = paper_trading

    def _create_session(self) -> TDClient:

        td_client = TDClient(
            client_id = self.client_id,
            redirect_uri = self.redirect_uri,
            credentials_path = self.credentials_path
        )

        # Login to the session
        td_client.login()

        return td_client
    
    @property
    def pre_market_open(self) -> bool: #Premarket Open

        pre_market_start_time = datetime.utcnow().replace(hour = 12, minute = 00, second = 00).timestamp()
        market_start_time = datetime.utcnow().replace(hour = 13, minute = 30, second = 00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if market_start_time >= right_now >= pre_market_start_time:
            return True
        else:
            return False

    @property
    def post_market_open(self) -> bool: #Postmarket Open
        
        post_market_end_time = datetime.utcnow().replace(hour = 22, minute = 30, second = 00).timestamp()
        market_start_time = datetime.utcnow().replace(hour = 13, minute = 30, second = 00).timestamp()
        market_end_time = datetime.utcnow().replace(hour = 20, minute = 00, second = 00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if post_market_end_time >= right_now >= market_start_time:
            return True
        else:
            return False

    @property
    def regular_market_open(self) -> bool: #Regular Market Open
        
        market_start_time = datetime.utcnow().replace(hour = 22, minute = 30, second = 00).timestamp()
        market_end_time = datetime.utcnow().replace(hour = 20, minute = 00, second = 00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if market_end_time >= right_now >= market_start_time:
            return True
        else:
            return False
        
    def create_portfolio(self):
        
        #Initialize a new Portfolio object
        self.portfolio = Portfolio(account_number=self.trading_account)

        # Assign the TDClient to the portfolio
        self.portfolio.td_client = self.session

        return self.portfolio

    def create_trade(self, trade_id: str, enter_or_exit: str, long_or_short: str, order_type: str = 'mkt', price: float = 0.0, stop_limit_price: float = 0.0) -> Trade:
        
        # Initialzie new Trade object
        trade = Trade()

        #Create the trade
        trade.new_trade(
            trade_id = trade_id,
            order_type = order_type,
            enter_or_exit = enter_or_exit,
            long_or_short = long_or_short,
            price = price,
            stop_limit_price = stop_limit_price
        )

        self.trades[trade_id] = trade

        return trade

    def grab_current_quotes(self) -> dict:
        
        # Grab all the symbols in the portfolio
        symbols = self.portfolio.positions.keys()

        # Grab the current quotes for all the symbols
        quotes = self.session.get_quotes(instruments=list(symbols))

        return quotes

    def create_stock_frame(self, data: List[dict]) -> Stockframe:

        self.stock_frame = Stockframe(data=data)

        return self.stock_frame
    
    def grab_historical_prices(self, start: datetime, end: datetime, bar_size: int = 1, bar_type: str = 'minute', sumbols: Optional[List[str]] = None) -> dict:

        self._bar_size = bar_size
        self._bar_type = bar_type

        start = str(milliseconds_since_epoch(dt_object=start))
        end = str(milliseconds_since_epoch(dt_obejct=end))
        
        new_prices = []
        
        if not symbols:
            symbols = self.portfolio.positions

        for symbol in symbols:

            historical_price_response = self.session.get_price_history(
                symbol=symbol,
                period_type='day',
                start_date=start,
                end_date=end,
                frequency_type=bar_type,
                frequency=bar_size,
                extended_hours=True
            )

            self.historical_prices[symbol] = {}
            self.historical_prices[symbol]['candles'] = historical_price_response['candles']

            for candle in historical_price_response['candles']:

                new_prices_mini_dict = {}
                new_prices_mini_dict['symbol'] = symbol
                new_prices_mini_dict['open'] = candle['open']
                new_prices_mini_dict['high'] = candle['high']
                new_prices_mini_dict['low'] = candle['low']
                new_prices_mini_dict['close'] = candle['close']
                new_prices_mini_dict['volume'] = candle['volume']
                new_prices_mini_dict['datetime'] = datetime.fromtimestamp(candle['datetime'] / 1e3)
                new_prices.append(new_prices_mini_dict)

        self.historical_prices['aggregated'] = new_prices

        return self.historical_prices
        
    def get_latest_bar(self) -> List[dict]:

        bar_size = self._bar_size
        bar_type = self._bar_type

        # Define the date range
        end_date = datetime.today()
        start_date = end_date - timedelta(minutes=5)

        start = str(milliseconds_since_epoch(dt_object=start_date))
        end = str(milliseconds_since_epoch(dt_object=end_date))

        latest_prices = []
        for symbol in self.portfolio.positions:

            historical_price_response = self.session.get_price_history(
                symbol=symbol,
                period_type='day',
                start_date=start,
                end_date=end,
                frequency_type=bar_type,
                frequency=bar_size,
                extended_hours=True
            )

            if 'error' in historical_price_response:
            
                time_true.sleep(2)
                historical_price_response = self.session.get_price_history(
                    symbol=symbol,
                    period_type='day',
                    start_date=start,
                    end_date=end,
                    frequency_type=bar_type,
                    frequency=bar_size,
                    extended_hours=True
                )

            for candle in historical_price_response['candles'][-1]:

                new_prices_mini_dict = {}
                new_prices_mini_dict['symbol'] = symbol
                new_prices_mini_dict['open'] = candle['open']
                new_prices_mini_dict['high'] = candle['high']
                new_prices_mini_dict['low'] = candle['low']
                new_prices_mini_dict['close'] = candle['close']
                new_prices_mini_dict['volume'] = candle['volume']
                new_prices_mini_dict['datetime'] = candle['datetime']
                latest_prices.append(new_prices_mini_dict)

        return latest_prices
    
    def wait_till_next_bar(self, last_bar_timestamp: pd.DatetimeIndex) -> None:

        last_bar_time = last_bar_timestamp.to_pydatetime()[0].replace(tzinfo=timezone.utc)
        next_bar_time = last_bar_time + timedelta(seconds=60)
        curr_bar_time = datetime.now(tz=timezone.utc)

        last_bar_timestamp = int(last_bar_time.timestamp())
        next_bar_timestamp = int(next_bar_time.timestamp())
        curr_bar_timestamp = int(curr_bar_time.timestamp())

        time_to_wait_now = next_bar_timestamp - curr_bar_timestamp

        if time_to_wait_now < 0:
            time_to_wait_now = 0

        print("=" * 80)
        print("Pausing for the next bar")
        print("-" * 80)
        print("Curr Time: {time_curr}".format(
            time_curr=curr_bar_time.strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        print("Next Time: {time_next}".format(
            time_next=next_bar_time.strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        print("Sleep Time: {seconds}".format(seconds=time_to_wait_now))
        print("-" * 80)
        print('')

        time_true.sleep(time_to_wait_now)

    def execute_signals(self, signals: List[pd.Series], trades_to_execute: dict) -> List[dict]:

        # Define the Buy and sells.
        buys: pd.Series = signals['buys']
        sells: pd.Series = signals['sells']

        order_responses = []

        # If we have buys or sells continue.
        if not buys.empty:

            # Grab the buy Symbols.
            symbols_list = buys.index.get_level_values(0).to_list()

            # Loop through each symbol.
            for symbol in symbols_list:

                # Check to see if there is a Trade object.
                if symbol in trades_to_execute:

                    if self.portfolio.in_portfolio(symbol=symbol):
                        self.portfolio.set_ownership_status(
                            symbol=symbol,
                            ownership=True
                        )

                    # Set the Execution Flag.
                    trades_to_execute[symbol]['has_executed'] = True
                    trade_obj: Trade = trades_to_execute[symbol]['buy']['trade_func']

                    if not self.paper_trading:

                        # Execute the order.
                        order_response = self.execute_orders(
                            trade_obj=trade_obj
                        )

                        order_response = {
                            'order_id': order_response['order_id'],
                            'request_body': order_response['request_body'],
                            'timestamp': datetime.now().isoformat()
                        }

                        order_responses.append(order_response)

                    else:

                        order_response = {
                            'order_id': trade_obj._generate_order_id(),
                            'request_body': trade_obj.order,
                            'timestamp': datetime.now().isoformat()
                        }

                        order_responses.append(order_response)

        elif not sells.empty:

            # Grab the buy Symbols.
            symbols_list = sells.index.get_level_values(0).to_list()

            # Loop through each symbol.
            for symbol in symbols_list:

                # Check to see if there is a Trade object.
                if symbol in trades_to_execute:

                    # Set the Execution Flag.
                    trades_to_execute[symbol]['has_executed'] = True

                    if self.portfolio.in_portfolio(symbol=symbol):
                        self.portfolio.set_ownership_status(
                            symbol=symbol,
                            ownership=False
                        )

                    trade_obj: Trade = trades_to_execute[symbol]['sell']['trade_func']

                    if not self.paper_trading:

                        # Execute the order.
                        order_response = self.execute_orders(
                            trade_obj=trade_obj
                        )

                        order_response = {
                            'order_id': order_response['order_id'],
                            'request_body': order_response['request_body'],
                            'timestamp': datetime.now().isoformat()
                        }

                        order_responses.append(order_response)

                    else:

                        order_response = {
                            'order_id': trade_obj._generate_order_id(),
                            'request_body': trade_obj.order,
                            'timestamp': datetime.now().isoformat()
                        }

                        order_responses.append(order_response)

        # Save the response.
        self.save_orders(order_response_dict=order_responses)

        return order_responses

    def execute_orders(self, trade_obj: Trade) -> dict:

        # Execute the order.
        order_dict = self.session.place_order(
            account=self.trading_account,
            order=trade_obj.order
        )

        # Store the order.
        trade_obj._order_response = order_dict

        # Process the order response.
        trade_obj._process_order_response()

        return order_dict
    
    def save_orders(self, order_response_dict: dict) -> bool:
        
        def default(obj):

            if isinstance(obj, bytes):
                return str(obj)

        # Define the folder.
        folder: pathlib.PurePath = pathlib.Path(
            __file__
        ).parents[1].joinpath("data")

        # See if it exist, if not create it.
        if not folder.exists():
            folder.mkdir()

        # Define the file path.
        file_path = folder.joinpath('orders.json')

        # First check if the file alread exists.
        if file_path.exists():
            with open('data/orders.json', 'r') as order_json:
                orders_list = json.load(order_json)
        else:
            orders_list = []

        # Combine both lists.
        orders_list = orders_list + order_response_dict

        # Write the new data back.
        with open(file='data/orders.json', mode='w+') as order_json:
            json.dump(obj=orders_list, fp=order_json, indent=4, default=default)

        return True