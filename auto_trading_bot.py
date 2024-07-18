import requests
import time
import logging

from ticker_symbol import ticker_symbol
from trading_logic import trading_logic

# ログの設定
logging.basicConfig(filename='trade.log', level=logging.INFO)

# 楽天証券APIのエンドポイントとAPIキーを設定
base_url = "https://api.rakuten-sec.co.jp"
api_key = "YOUR_API_KEY"

# 証券コード
symbol = ticker_symbol

# 初期所持金
capital = 50000
holding_quantity = 0
average_purchase_price = 0

def get_stock_price(symbol):
    url = f"{base_url}/v1/marketdata/quote?symbol={symbol}"
    headers = {"x-api-key": api_key}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data["lastPrice"]

def buy_stock(symbol, quantity, price):
    global capital, holding_quantity, average_purchase_price
    url = f"{base_url}/v1/orders"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    order_data = {
        "symbol": symbol,
        "side": "buy",
        "quantity": quantity,
        "orderType": "market",
        "timeInForce": "day"
    }
    response = requests.post(url, headers=headers, json=order_data)
    if response.status_code == 200:
        capital -= quantity * price
        holding_quantity += quantity
        average_purchase_price = ((average_purchase_price * (holding_quantity - quantity)) + (price * quantity)) / holding_quantity
        logging.info(f"Bought {quantity} shares of {symbol} at {price} each")
    return response.json()

def sell_stock(symbol, quantity, price):
    global capital, holding_quantity, average_purchase_price
    url = f"{base_url}/v1/orders"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    order_data = {
        "symbol": symbol,
        "side": "sell",
        "quantity": quantity,
        "orderType": "market",
        "timeInForce": "day"
    }
    response = requests.post(url, headers=headers, json=order_data)
    if response.status_code == 200:
        capital += quantity * price
        holding_quantity -= quantity
        if holding_quantity == 0:
            average_purchase_price = 0
        logging.info(f"Sold {quantity} shares of {symbol} at {price} each")
    return response.json()

def day_trade():
    global capital, holding_quantity, average_purchase_price
    price = get_stock_price(symbol)
    logging.info(f"{symbol} current price: {price}")

    action, quantity = trading_logic(price, capital, holding_quantity, average_purchase_price)

    if action == 'buy':
        logging.info(f"Buying {quantity} shares of {symbol}")
        buy_stock(symbol, quantity, price)
    elif action == 'sell':
        logging.info(f"Selling {quantity} shares of {symbol}")
        sell_stock(symbol, quantity, price)

    logging.info(f"Remaining capital: {capital}, Holding quantity: {holding_quantity}, Average purchase price: {average_purchase_price}")

if __name__ == "__main__":
    while True:
        day_trade()
        time.sleep(60)  # 1分ごとにチェック