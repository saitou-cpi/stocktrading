import pandas as pd
import requests
from datetime import datetime
from models.models import TradeModel
from views.views import Logger
from config.vars import ticker_symbol, base_url, api_key, upper_limit, lower_limit, initial_capital

class TradeController:
    def __init__(self):
        self.model = TradeModel(initial_capital)
        self.logger = Logger()
        self.symbol = ticker_symbol
        self.price_history = []

    def update_price_history(self, price):
        self.price_history.append(price)
        if len(self.price_history) > 50:
            self.price_history.pop(0)

    def calculate_moving_averages(self):
        if len(self.price_history) < 50:
            return None, None
        prices = pd.Series(self.price_history)
        short_ma = prices.rolling(window=10).mean().iloc[-1]
        long_ma = prices.rolling(window=50).mean().iloc[-1]
        return short_ma, long_ma

    def trading_logic(self, price):
        action = None
        quantity = 0

        self.update_price_history(price)
        short_ma, long_ma = self.calculate_moving_averages()

        if short_ma is not None and long_ma is not None:
            # 短期移動平均が長期移動平均を上回ると買いシグナル
            if short_ma > long_ma and self.model.capital >= price and self.model.holding_quantity == 0:
                quantity = int(self.model.capital / price)
                if quantity > 0:
                    action = 'buy'

            # 短期移動平均が長期移動平均を下回ると売りシグナル
            elif short_ma < long_ma and self.model.holding_quantity > 0:
                action = 'sell'
                quantity = self.model.holding_quantity

        # 動的な閾値の設定（ボラティリティに基づく）
        if self.model.holding_quantity > 0:
            volatility = self.calculate_volatility()
            dynamic_upper_limit = self.model.average_purchase_price * (1 + volatility * 0.1)
            dynamic_lower_limit = self.model.average_purchase_price * (1 - volatility * 0.1)

            # 動的な閾値に基づく売り
            if price >= dynamic_upper_limit:
                action = 'sell'
                quantity = self.model.holding_quantity // 2

            elif price <= dynamic_lower_limit:
                action = 'sell'
                quantity = self.model.holding_quantity // 2

        return action, quantity

    def calculate_volatility(self):
        if len(self.price_history) < 20:
            return 0.01  # 仮のデフォルトボラティリティ
        prices = pd.Series(self.price_history)
        return prices.pct_change().rolling(window=20).std().iloc[-1]

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
            
