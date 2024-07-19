# stocktrading/controllers/controllers.py

import requests
from datetime import datetime, timedelta
import numpy as np
from models.models import TradeModel
from views.views import Logger
from config.vars import ticker_symbol, base_url, upper_limit, lower_limit, initial_capital
import os

class TradeController:
    def __init__(self):
        self.model = TradeModel(initial_capital)
        self.logger = Logger()
        self.symbol = ticker_symbol
        self.api_key = os.getenv("API_KEY")

    def get_stock_price(self):
        try:
            url = f"{base_url}/v1/marketdata/quote?symbol={self.symbol}"
            headers = {"x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["lastPrice"]
        except requests.RequestException as e:
            self.logger.error(f"Error fetching stock price: {e}")
            return None

    def get_historical_prices(self, days=30):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            url = f"{base_url}/v1/marketdata/history?symbol={self.symbol}&startDate={start_date.strftime('%Y-%m-%d')}&endDate={end_date.strftime('%Y-%m-%d')}"
            headers = {"x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            prices = [entry['close'] for entry in data['prices']]
            return prices
        except requests.RequestException as e:
            self.logger.error(f"Error fetching historical prices: {e}")
            return []

    def calculate_moving_average(self, prices, window):
        if len(prices) < window:
            return None
        return np.mean(prices[-window:])

    def buy_stock(self, quantity, price):
        url = f"{base_url}/v1/orders"
        headers = {
            "x-api-key": self.api_key,
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
            "x-api-key": self.api_key,
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

        historical_prices = self.get_historical_prices(30)
        if len(historical_prices) < 20:
            self.logger.error("Not enough historical data to calculate moving averages.")
            return action, quantity

        short_term_ma = self.calculate_moving_average(historical_prices, 5)
        long_term_ma = self.calculate_moving_average(historical_prices, 20)

        if short_term_ma is None or long_term_ma is None:
            self.logger.error("Error calculating moving averages.")
            return action, quantity

        # トレンドフォロー戦略
        if short_term_ma > long_term_ma:
            # 上昇トレンド: 取得した金額よりupper_limit%上がったら売る
            if self.model.holding_quantity > 0 and price >= self.model.average_purchase_price * upper_limit:
                action = 'sell'
                quantity = self.model.holding_quantity
            # 5万円以内で買える場合は買う
            elif self.model.capital >= price and self.model.holding_quantity == 0:
                quantity = int(self.model.capital / price)
                if quantity > 0:
                    action = 'buy'
        elif short_term_ma < long_term_ma:
            # 下降トレンド: 取得した金額よりlower_limit%下がったら売る
            if self.model.holding_quantity > 0 and price <= self.model.average_purchase_price * lower_limit:
                action = 'sell'
                quantity = self.model.holding_quantity

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

