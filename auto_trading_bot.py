import requests
import logging
import os
import json

from vars import ticker_symbol, initial_capital, base_url, api_key
from trading_logic import trading_logic

# ログの設定
log_dir = "trade_logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_filename = os.path.join(log_dir, 'auto_trade.log')
logging.basicConfig(filename=log_filename, level=logging.INFO)

# 楽天証券APIのエンドポイントとAPIキーを設定
base_url = base_url
api_key = api_key

# 証券コード
symbol = ticker_symbol

# 初期所持金
state_file = 'trade_state.json'

def load_state():
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
        return state['capital'], state['holding_quantity'], state['average_purchase_price']
    else:
        return initial_capital, 0, 0

def save_state(capital, holding_quantity, average_purchase_price):
    state = {
        'capital': capital,
        'holding_quantity': holding_quantity,
        'average_purchase_price': average_purchase_price
    }
    with open(state_file, 'w') as f:
        json.dump(state, f)

capital, holding_quantity, average_purchase_price = load_state()

def get_stock_price(symbol):
    try:
        url = f"{base_url}/v1/marketdata/quote?symbol={symbol}"
        headers = {"x-api-key": api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["lastPrice"]
    except requests.RequestException as e:
        logging.error(f"Error fetching stock price: {e}")
        return None

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
    try:
        response = requests.post(url, headers=headers, json=order_data)
        response.raise_for_status()
        capital -= quantity * price
        holding_quantity += quantity
        average_purchase_price = ((average_purchase_price * (holding_quantity - quantity)) + (price * quantity)) / holding_quantity
        logging.info(f"Bought {quantity} shares of {symbol} at {price} each")
    except requests.RequestException as e:
        logging.error(f"Error buying stock: {e}")

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
    try:
        response = requests.post(url, headers=headers, json=order_data)
        response.raise_for_status()
        capital += quantity * price
        holding_quantity -= quantity
        if holding_quantity == 0:
            average_purchase_price = 0
        logging.info(f"Sold {quantity} shares of {symbol} at {price} each")
    except requests.RequestException as e:
        logging.error(f"Error selling stock: {e}")

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
    save_state(capital, holding_quantity, average_purchase_price)

if __name__ == "__main__":
    day_trade()
