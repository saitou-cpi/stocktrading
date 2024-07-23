import os
import datetime
import logging
import pandas as pd
from config.vars import ticker_symbols, upper_limits, lower_limits, initial_capital
from models.database import load_stock_data
from controllers.trade import TradeController
from views.logging_setup import setup_logging
from utils.trend import determine_trend

def optimize_parameters(df, upper_limit, lower_limit, ticker_symbol, initial_capital):
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

def save_results_to_csv(ticker_symbol, results, log_dir):
    results_df = pd.DataFrame(results, columns=['upper_limit', 'lower_limit', 'final_value', 'profit_loss'])
    results_filename = os.path.join(log_dir, f'{ticker_symbol.replace(".", "_")}_optimal_parameters_results_{datetime.datetime.now().strftime("%Y%m%d%H%M")}.csv')
    os.makedirs(os.path.dirname(results_filename), exist_ok=True)
    results_df.to_csv(results_filename, index=False)
    logging.info(f"Backtest results saved to {results_filename}")

def main():
    for ticker_symbol in ticker_symbols:
        log_dir = setup_logging(ticker_symbol)
        df = load_stock_data(ticker_symbol, days=30)

        param_combinations = [(ul, ll) for ul in upper_limits for ll in lower_limits]

        best_upper_limit, best_lower_limit = None, None
        best_profit_loss = float('-inf')
        results = []

        for upper_limit, lower_limit in param_combinations:
            final_value, profit_loss = optimize_parameters(df, upper_limit, lower_limit, ticker_symbol, initial_capital)
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
        save_results_to_csv(ticker_symbol, results, log_dir)

