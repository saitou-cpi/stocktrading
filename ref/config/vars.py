# config/vars.py

# ターゲット銘柄（複数対応）
ticker_symbols = ['4246', '4820']

# 初期所持金
initial_capital = 100000

# パラメータの組み合わせ float
upper_limits = [1.01, 1.05, 1.10, 1.15, 1.20]
lower_limits = [0.90, 0.95, 0.97, 0.99, 1.00]

# 移動平均の期間
short_term_window = 5
long_term_window = 10
trend_short_term_window = 5
trend_long_term_window = 10
