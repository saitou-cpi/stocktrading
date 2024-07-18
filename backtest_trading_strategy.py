import os
import datetime
import pandas as pd
import logging

from config.vars import ticker_symbol, initial_capital
from controllers.controllers import TradeController
from models.models import TradeModel

# ディレクトリの設定
log_dir = "backtestlog"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# ログファイルの設定
log_filename = os.path.join(log_dir, 'backtest_trade.log')
logging.basicConfig(filename=log_filename, level=logging.INFO)

# 証券コード
symbol = ticker_symbol

# 初期所持金
capital = initial_capital
holding_quantity = 0
average_purchase_price = 0

# ディレクトリの設定
output_dir = "stockdata"

# ファイル名を作成
date_str = datetime.datetime.now().strftime('%Y%m%d')  # ファイル名に使われる日付
csv_filename = os.path.join(output_dir,  f'{ticker_symbol.replace(".", "_")}_one_month_intraday_stock_data_{date_str}.csv')  # 特定の日付に対応

# 過去の株価データを読み込む
if os.path.exists(csv_filename):
    df = pd.read_csv(csv_filename, index_col='Datetime', parse_dates=True)
    logging.info(f"Loaded data from {csv_filename}")
else:
    logging.error(f"File {csv_filename} does not exist")
    raise FileNotFoundError(f"File {csv_filename} does not exist")

# TradeControllerとTradeModelのインスタンスを作成
tradecontroller = TradeController()
trademodel = TradeModel(initial_capital)

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

        action, quantity = tradecontroller.trading_logic(price)

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
