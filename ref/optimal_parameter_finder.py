import os
import datetime
import pandas as pd
import logging
import numpy as np
from sqlalchemy import create_engine, text
from config.vars import ticker_symbols, initial_capital, upper_limits, lower_limits, short_term_window, long_term_window


# ログの設定
def setup_logging(symbol):
    log_dir = os.path.abspath("optimal_parameter_log")
    os.makedirs(log_dir, exist_ok=True)
    results_date_str = datetime.datetime.now().strftime('%Y%m%d%H%M')
    log_filename = os.path.join(log_dir, f'{symbol.replace(".", "_")}_optimal_parameter_{results_date_str}.log')
    logging.basicConfig(filename=log_filename, level=logging.INFO)
    return log_dir

# データベースの設定
db_filename = 'stock_data.db'
db_path = os.path.join(os.getcwd(), db_filename)
engine = create_engine(f'sqlite:///{db_path}')

def load_stock_data(ticker, days=30):
    query = text(f"SELECT date, open, high, low, close, adj_close, volume FROM stock_data WHERE ticker=:ticker ORDER BY date DESC LIMIT :days")
    with engine.connect() as conn:
        result = conn.execute(query, {'ticker': ticker, 'days': days})
        data = result.fetchall()
        if not data:
            logging.error(f"No data found for ticker {ticker}")
            raise FileNotFoundError(f"No data found for ticker {ticker}")
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume'])
        df['date'] = pd.to_datetime(df['date'])  # 日付を日時型に変換
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)  # 昇順に並び替え
        logging.info(f"Loaded data from database for ticker {ticker}")
        return df

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

# トレンドを判定する関数
def determine_trend(prices):
    trade_controller = TradeController(pd.DataFrame(prices), "", initial_capital)
    short_term_ma = trade_controller.calculate_moving_average(prices, short_term_window)[-1]  # 20日移動平均
    long_term_ma = trade_controller.calculate_moving_average(prices, long_term_window)[-1]  # 50日移動平均
    last_close = prices.iloc[-1]  # 前日の終値を正しい方法で取得

    if last_close > short_term_ma * 1.2:
        return "上昇トレンド（前日高騰）"
    elif short_term_ma > long_term_ma:
        return "上昇トレンド"
    else:
        return "下降トレンド"

def optimize_parameters(df, upper_limit, lower_limit, ticker_symbol):
    trade_controller = TradeController(df, ticker_symbol, initial_capital)

    for price in df['close']:
        logging.info(f"Current price: {price}")
        action, quantity = trade_controller.trading_logic(price, upper_limit, lower_limit)

        if action == 'buy':
            trade_controller.model.buy_stock(price, quantity)
        elif action == 'sell':
            trade_controller.model.sell_stock(price, quantity)

    final_value = trade_controller.model.capital + trade_controller.model.holding_quantity * df.iloc[-1]['close']
    profit_loss = final_value - initial_capital
    return final_value, profit_loss

def main():
    for ticker_symbol in ticker_symbols:
        log_dir = setup_logging(ticker_symbol)
        df = load_stock_data(ticker_symbol, days=30)

        param_combinations = [(ul, ll) for ul in upper_limits for ll in lower_limits]

        best_upper_limit, best_lower_limit = None, None
        best_profit_loss = float('-inf')
        results = []

        for upper_limit, lower_limit in param_combinations:
            final_value, profit_loss = optimize_parameters(df, upper_limit, lower_limit, ticker_symbol)
            results.append((upper_limit, lower_limit, final_value, profit_loss))
            if profit_loss > best_profit_loss:
                best_upper_limit = upper_limit
                best_lower_limit = lower_limit
                best_profit_loss = profit_loss

            logging.info(f"Upper limit: {upper_limit}, Lower limit: {lower_limit}, Final value: {final_value}, Profit/Loss: {profit_loss}")

        # トレンドの判定
        trend = determine_trend(df['close'])

        print(f"Ticker: {ticker_symbol}")
        print(f"Best upper limit: {best_upper_limit}")
        print(f"Best lower limit: {best_lower_limit}")
        print(f"Best Profit/Loss: {best_profit_loss}")
        print(f"Current Trend: {trend}")

        # 結果をCSVに保存
        results_df = pd.DataFrame(results, columns=['upper_limit', 'lower_limit', 'final_value', 'profit_loss'])
        results_filename = os.path.join(log_dir, f'{ticker_symbol.replace(".", "_")}_optimal_parameters_results_{datetime.datetime.now().strftime("%Y%m%d%H%M")}.csv')
        os.makedirs(os.path.dirname(results_filename), exist_ok=True)
        results_df.to_csv(results_filename, index=False)
        logging.info(f"Backtest results saved to {results_filename}")
