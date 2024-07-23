'''trade.py'''
import logging
import numpy as np
from config.vars import short_term_window, long_term_window

class TradeModel:
    def __init__(self, initial_capital):
        self.capital = initial_capital
        self.holding_quantity = 0
        self.average_price = 0

    def buy_stock(self, price, quantity):
        quantity = min(quantity, (self.capital // price) // 100 * 100)  # 100株単位に調整
        if quantity > 0:
            self.capital -= quantity * price
            self.holding_quantity += quantity
            self.average_price = ((self.average_price * (self.holding_quantity - quantity)) + (price * quantity)) / self.holding_quantity
            logging.info(f"Bought {quantity} shares at {price} each. New capital: {self.capital}, Holding: {self.holding_quantity}, Average purchase price: {self.average_price}")

    def sell_stock(self, price, quantity):
        quantity = min(quantity, (self.holding_quantity // 100) * 100)  # 100株単位に調整
        if quantity > 0:
            self.capital += quantity * price
            self.holding_quantity -= quantity
            if self.holding_quantity == 0:
                self.average_price = 0
            logging.info(f"Sold {quantity} shares at {price} each. New capital: {self.capital}, Holding: {self.holding_quantity}, Average purchase price: {self.average_price}")


class TradeController:
    def __init__(self, df, symbol, initial_capital):
        self.model = TradeModel(initial_capital)
        self.logger = logging.getLogger()
        self.symbol = symbol
        self.historical_prices = self.get_daily_prices(df)

    def get_daily_prices(self, df):
        try:
            daily_df = df.resample('D').agg({'close': 'last'}).dropna()
            return daily_df['close'].tolist()
        except Exception as e:
            self.logger.error(f"Error loading daily prices: {e}")
            return []

    def calculate_moving_average(self, prices, window):
        if len(prices) < window:
            return None
        moving_average = np.convolve(prices, np.ones(window), 'valid') / window
        self.logger.info(f"Calculated moving average for window {window}: {moving_average}")
        return moving_average

    def trading_logic(self, current_price, upper_limit, lower_limit):
        action, quantity = None, 0

        if len(self.historical_prices) < long_term_window:
            self.logger.error("Not enough historical data to calculate moving averages.")
            return action, quantity

        short_term_ma = self.calculate_moving_average(self.historical_prices, short_term_window)
        long_term_ma = self.calculate_moving_average(self.historical_prices, long_term_window)

        if any(x is None for x in [short_term_ma, long_term_ma]) or any(len(x) == 0 for x in [short_term_ma, long_term_ma]):
            self.logger.error("Error calculating moving averages.")
            return action, quantity

        min_length = min(len(short_term_ma), len(long_term_ma))
        short_term_ma, long_term_ma = short_term_ma[-min_length:], long_term_ma[-min_length:]

        self.logger.info(f"Short-term MA: {short_term_ma[-1]}, Long-term MA: {long_term_ma[-1]}")
        self.logger.info(f"Before Action - Capital: {self.model.capital}, Holding Quantity: {self.model.holding_quantity}, Average Price: {self.model.average_price}")

        if self.model.holding_quantity == 0:
            quantity = (self.model.capital // current_price) // 100 * 100  # 100株単位に調整
            if quantity > 0:
                action = 'buy'
        else:
            if current_price >= self.model.average_price * upper_limit and short_term_ma[-1] > long_term_ma[-1]:
                action, quantity = 'sell', (self.model.holding_quantity // 100) * 100  # 100株単位に調整
            elif current_price <= self.model.average_price * lower_limit:
                action, quantity = 'sell', (self.model.holding_quantity // 100) * 100  # 100株単位に調整

        self.logger.info(f"After Action - Capital: {self.model.capital}, Holding Quantity: {self.model.holding_quantity}, Average Price: {self.model.average_price}")
        self.logger.info(f"Action: {action}, Quantity: {quantity}, Price: {current_price}")
        return action, quantity
