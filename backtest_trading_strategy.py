import os
import datetime
import pandas as pd
import logging

from config.vars import ticker_symbol, initial_capital
from controllers.controllers import TradeController

# ディレクトリの設定
log_dir = "backtestlog"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# ログファイルの設定
log_filename = os.path.join(log_dir, 'backtest_trade.log')
logging.basicConfig(filename=log_filename, level=logging.DEBUG)

# 証券コード
symbol = ticker_symbol

# ディレクトリの設定
output_dir = "stockdata"

# ファイル名を作成
date_str = datetime.datetime.now().strftime('%Y%m%d')  # ファイル名に使われる日付
csv_filename = os.path.join(output_dir, f'{ticker_symbol.replace(".", "_")}_one_month_intraday_stock_data_{date_str}.csv')  # 特定の日付に対応

# 過去の株価データを読み込む
if os.path.exists(csv_filename):
    df = pd.read_csv(csv_filename, index_col='Datetime', parse_dates=True)
    logging.info(f"Loaded data from {csv_filename}")
else:
    logging.error(f"File {csv_filename} does not exist")
    raise FileNotFoundError(f"File {csv_filename} does not exist")

# 取引関数の定義
def execute_trade(action, price, quantity, capital, holding_quantity, average_purchase_price):
    if action == 'buy':
        if quantity * price > capital:
            quantity = capital // price  # 買えるだけ買う
        if quantity > 0:
            capital -= quantity * price
            holding_quantity += quantity
            if holding_quantity > 0:
                average_purchase_price = ((average_purchase_price * (holding_quantity - quantity)) + (price * quantity)) / holding_quantity
            logging.debug(f"Bought {quantity} shares at {price} each. New capital: {capital}, Holding: {holding_quantity}, Avg purchase price: {average_purchase_price}")
    elif action == 'sell':
        if quantity > holding_quantity:
            quantity = holding_quantity  # 売れるだけ売る
        if quantity > 0:
            capital += quantity * price
            holding_quantity -= quantity
            if holding_quantity == 0:
                average_purchase_price = 0
            logging.debug(f"Sold {quantity} shares at {price} each. New capital: {capital}, Holding: {holding_quantity}, Avg purchase price: {average_purchase_price}")
    return capital, holding_quantity, average_purchase_price

def backtest(df, upper_limit, lower_limit):
    capital = initial_capital
    holding_quantity = 0
    average_purchase_price = 0
    trade_controller = TradeController(upper_limit, lower_limit)

    for index, row in df.iterrows():
        price = row['Close']
        logging.debug(f"Current price: {price}")

        action, quantity = trade_controller.trading_logic(price)
        logging.debug(f"Action: {action}, Quantity: {quantity}, Price: {price}, Upper limit: {upper_limit}, Lower limit: {lower_limit}")

        if action:
            capital, holding_quantity, average_purchase_price = execute_trade(action, price, quantity, capital, holding_quantity, average_purchase_price)

        logging.debug(f"Remaining capital: {capital}, Holding quantity: {holding_quantity}, Average purchase price: {average_purchase_price}")

    final_value = capital + holding_quantity * df.iloc[-1]['Close']
    profit_loss = final_value - initial_capital
    return final_value, profit_loss

if __name__ == "__main__":
    best_upper_limit = None
    best_lower_limit = None
    best_profit_loss = float('-inf')

    results = []

    for upper_limit in [1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09]:
        for lower_limit in [0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99]:
            logging.info(f"Testing upper_limit: {upper_limit}, lower_limit: {lower_limit}")
            final_value, profit_loss = backtest(df, upper_limit, lower_limit)
            results.append((upper_limit, lower_limit, final_value, profit_loss))

            if profit_loss > best_profit_loss:
                best_upper_limit = upper_limit
                best_lower_limit = lower_limit
                best_profit_loss = profit_loss

            logging.info(f"Upper limit: {upper_limit}, Lower limit: {lower_limit}, Final value: {final_value}, Profit/Loss: {profit_loss}")

    print(f"Best upper limit: {best_upper_limit}")
    print(f"Best lower limit: {best_lower_limit}")
    print(f"Best Profit/Loss: {best_profit_loss}")

    # 結果をCSVに保存
    results_df = pd.DataFrame(results, columns=['upper_limit', 'lower_limit', 'final_value', 'profit_loss'])
    results_filename = os.path.join(output_dir, 'backtest_results.csv')
    results_df.to_csv(results_filename, index=False)
    logging.info(f"Backtest results saved to {results_filename}")
