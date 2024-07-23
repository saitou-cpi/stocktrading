# trend.py
import pandas as pd
from trade import TradeController
from config.vars import initial_capital, short_term_window, long_term_window

def determine_trend(prices):
    trade_controller = TradeController(pd.DataFrame(prices), "", initial_capital)
    short_term_ma = trade_controller.calculate_moving_average(prices, short_term_window)
    long_term_ma = trade_controller.calculate_moving_average(prices, long_term_window)

    if short_term_ma is None or long_term_ma is None:
        return "データが不足しています"

    short_term_ma = short_term_ma[-1]
    long_term_ma = long_term_ma[-1]
    last_close = prices.iloc[-1]

    if last_close > short_term_ma * 1.2:
        return "上昇トレンド（前日高騰）"
    elif short_term_ma > long_term_ma:
        return "上昇トレンド"
    else:        return "下降トレンド"
