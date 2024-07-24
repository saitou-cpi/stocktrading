import os
import datetime
import logging
import pandas as pd
from config.vars import upper_limits, lower_limits, min_data_points
from models.database import load_stock_data
from controllers.trade import TradeController
from views.logging_setup import setup_logging
from utils.trend import determine_trend

def optimize_parameters(df, upper_limit, lower_limit, ticker_symbol, initial_capital):
    trade_controller = TradeController(df, ticker_symbol, initial_capital)
    trades_executed = False

    for price in df['close']:
        logging.info(f"Current price: {price}")
        action, quantity = trade_controller.trading_logic(price, upper_limit, lower_limit)

        if action == 'buy':
            if quantity > 0:
                trade_controller.model.buy_stock(price, quantity)
                trades_executed = True
            else:
                logging.error(f"Failed to buy: Not enough capital to purchase shares at price {price}")
        elif action == 'sell':
            if quantity > 0:
                trade_controller.model.sell_stock(price, quantity)
                trades_executed = True
            else:
                logging.error(f"Failed to sell: No shares available to sell at price {price}")
        else:
            logging.error(f"No trade action taken. Current Price: {price}, Capital: {trade_controller.model.capital}, Holding Quantity: {trade_controller.model.holding_quantity}")

    final_value = trade_controller.model.capital + trade_controller.model.holding_quantity * df.iloc[-1]['close']
    profit_loss = final_value - initial_capital
    return final_value, profit_loss, trades_executed

def save_results_to_csv(ticker_symbol, results, log_dir):
    results_df = pd.DataFrame(results, columns=['upper_limit', 'lower_limit', 'final_value', 'profit_loss'])
    results_filename = os.path.join(log_dir, f'{ticker_symbol.replace(".", "_")}_optimal_parameters_results_{datetime.datetime.now().strftime("%Y%m%d%H%M")}.csv')
    os.makedirs(os.path.dirname(results_filename), exist_ok=True)
    results_df.to_csv(results_filename, index=False)
    logging.info(f"Backtest results saved to {results_filename}")

def process_ticker(ticker_symbol, initial_capital):
    log_dir = setup_logging(ticker_symbol)
    df = load_stock_data(ticker_symbol, days=min_data_points)

    param_combinations = [(ul, ll) for ul in upper_limits for ll in lower_limits]

    best_upper_limit, best_lower_limit = None, None
    best_profit_loss = float('-inf')
    results = []
    trades_executed = False

    for upper_limit, lower_limit in param_combinations:
        final_value, profit_loss, trade_executed = optimize_parameters(df, upper_limit, lower_limit, ticker_symbol, initial_capital)
        results.append((upper_limit, lower_limit, final_value, profit_loss))
        if profit_loss > best_profit_loss:
            best_upper_limit = upper_limit
            best_lower_limit = lower_limit
            best_profit_loss = profit_loss

        if trade_executed:
            trades_executed = True

        logging.info(f"Upper limit: {upper_limit}, Lower limit: {lower_limit}, Final value: {final_value}, Profit/Loss: {profit_loss}")

    # トレンドの判定
    trend = determine_trend(df['close'])

    result = {
        "ticker": ticker_symbol,
        "best_upper_limit": best_upper_limit,
        "best_lower_limit": best_lower_limit,
        "best_profit_loss": best_profit_loss,
        "current_trend": trend,
        "trades_executed": trades_executed
    }

    # 結果をCSVに保存
    save_results_to_csv(ticker_symbol, results, log_dir)

    return result
