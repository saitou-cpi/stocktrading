import datetime
import pandas as pd
import logging

from ticker_symbol import ticker_symbol
from trading_logic import trading_logic

# ログの設定
logging.basicConfig(filename='backtest_trade.log', level=logging.INFO)

# 証券コード
symbol = ticker_symbol

# 初期所持金
initial_capital = 50000
capital = initial_capital
holding_quantity = 0
average_purchase_price = 0

# 過去の株価データを読み込む
date_str = datetime.datetime.now().strftime('%Y%m%d')  # ファイル名に使われる日付
csv_filename = f'{ticker_symbol.replace(".", "_")}_one_month_intraday_stock_data_{date_str}.csv'
df = pd.read_csv(csv_filename, index_col='Datetime', parse_dates=True)

def buy_stock(price, quantity):
    global capital, holding_quantity, average_purchase_price
    if quantity * price > capital:
        quantity = capital // price  # 買えるだけ買う
    if quantity > 0:
        capital -= quantity * price
        holding_quantity += quantity
        if holding_quantity > 0:
            average_purchase_price = ((average_purchase_price * (holding_quantity - quantity)) + (price * quantity)) / holding_quantity
        logging.info(f"Bought {quantity} shares at {price} each. New capital: {capital}, Holding: {holding_quantity}")

def sell_stock(price, quantity):
    global capital, holding_quantity, average_purchase_price
    if quantity > holding_quantity:
        quantity = holding_quantity  # 売れるだけ売る
    if quantity > 0:
        capital += quantity * price
        holding_quantity -= quantity
        if holding_quantity == 0:
            average_purchase_price = 0
        logging.info(f"Sold {quantity} shares at {price} each. New capital: {capital}, Holding: {holding_quantity}")

def backtest():
    global capital, holding_quantity, average_purchase_price
    for index, row in df.iterrows():
        price = row['Close']
        logging.info(f"Current price: {price}")

        action, quantity = trading_logic(price, capital, holding_quantity, average_purchase_price)

        if action == 'buy':
            logging.info(f"Buying {quantity} shares of {symbol}")
            buy_stock(price, quantity)
        elif action == 'sell':
            logging.info(f"Selling {quantity} shares of {symbol}")
            sell_stock(price, quantity)

        logging.info(f"Remaining capital: {capital}, Holding quantity: {holding_quantity}, Average purchase price: {average_purchase_price}")

if __name__ == "__main__":
    backtest()
    final_value = capital + holding_quantity * df.iloc[-1]['Close']
    print(f"Initial Capital: {initial_capital}")
    print(f"Final Capital: {final_value}")
    print(f"Profit/Loss: {final_value - initial_capital}")
