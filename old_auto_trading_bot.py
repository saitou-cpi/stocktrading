# auto_trading_bot.py

import logging
import os
import requests
from datetime import datetime
from config.vars import ticker_symbol, base_url, api_key, upper_limit, lower_limit, initial_capital

class TradeModel:
    def __init__(self, initial_capital=50000):
        self.capital = initial_capital
        self.holding_quantity = 0
        self.average_purchase_price = 0

class Logger:
    def __init__(self, log_dir='logs/trade_logs', log_filename='auto_trade.log'):
        self.log_dir = log_dir
        self.log_filename = log_filename
        self.setup_logger()

    def setup_logger(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        logging.basicConfig(filename=os.path.join(self.log_dir, self.log_filename), level=logging.INFO)

    @staticmethod
    def info(message):
        logging.info(message)

    @staticmethod
    def error(message):
        logging.error(message)

class TradeController:
    def __init__(self, upper_limit, lower_limit):
        self.model = TradeModel(initial_capital)
        self.logger = Logger()
        self.symbol = ticker_symbol
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit

    def get_stock_price(self):
        try:
            url = f"{base_url}/v1/marketdata/quote?symbol={self.symbol}"
            headers = {"x-api-key": api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["lastPrice"]
        except requests.RequestException as e:
            self.logger.error(f"Error fetching stock price: {e}")
            return None

    def buy_stock(self, quantity, price):
        url = f"{base_url}/v1/orders"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        order_data = {
            "symbol": self.symbol,
            "side": "buy",
            "quantity": quantity,
            "orderType": "market",
            "timeInForce": "day"
        }
        try:
            response = requests.post(url, headers=headers, json=order_data)
            response.raise_for_status()
            self.model.capital -= quantity * price
            self.model.holding_quantity += quantity
            self.model.average_purchase_price = (
                (self.model.average_purchase_price * (self.model.holding_quantity - quantity)) + (price * quantity)
            ) / self.model.holding_quantity
            self.logger.info(f"Bought {quantity} shares of {self.symbol} at {price} each")
        except requests.RequestException as e:
            self.logger.error(f"Error buying stock: {e}")

    def sell_stock(self, quantity, price):
        url = f"{base_url}/v1/orders"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        order_data = {
            "symbol": self.symbol,
            "side": "sell",
            "quantity": quantity,
            "orderType": "market",
            "timeInForce": "day"
        }
        try:
            response = requests.post(url, headers=headers, json=order_data)
            response.raise_for_status()
            self.model.capital += quantity * price
            self.model.holding_quantity -= quantity
            if self.model.holding_quantity == 0:
                self.model.average_purchase_price = 0
            self.logger.info(f"Sold {quantity} shares of {self.symbol} at {price} each")
        except requests.RequestException as e:
            self.logger.error(f"Error selling stock: {e}")

    def trading_logic(self, price):
        action = None
        quantity = 0

        # ルール1: 取得した金額よりupper_limit%上がったら売る
        if self.model.holding_quantity > 0 and price >= self.model.average_purchase_price * self.upper_limit:
            action = 'sell'
            quantity = self.model.holding_quantity

        # ルール2: 取得した金額よりlower_limit%下がったら売る
        elif self.model.holding_quantity > 0 and price <= self.model.average_purchase_price * self.lower_limit:
            action = 'sell'
            quantity = self.model.holding_quantity

        # ルール3: capitalの金額以内で買える場合は買う
        elif self.model.capital >= price and self.model.holding_quantity == 0:
            quantity = int(self.model.capital / price)
            if quantity > 0:
                action = 'buy'

        return action, quantity

    def day_trade(self):
        price = self.get_stock_price()
        if price is not None:
            self.logger.info(f"{self.symbol} current price: {price}")

            # 14時45分以降はすべての株を売却
            now = datetime.now()
            if now.hour == 14 and now.minute >= 45:
                if self.model.holding_quantity > 0:
                    self.logger.info(f"Selling all shares of {self.symbol} at the end of the day")
                    self.sell_stock(self.model.holding_quantity, price)
            else:
                action, quantity = self.trading_logic(price)
                if action == 'buy':
                    self.logger.info(f"Buying {quantity} shares of {self.symbol}")
                    self.buy_stock(quantity, price)
                elif action == 'sell':
                    self.logger.info(f"Selling {quantity} shares of {self.symbol}")
                    self.sell_stock(quantity, price)

            self.logger.info(f"Remaining capital: {self.model.capital}, Holding quantity: {self.model.holding_quantity}, Average purchase price: {self.model.average_purchase_price}")



if __name__ == "__main__":
    controller = TradeController()
    controller.day_trade()
