import cProfile
import pstats
import logging
from controllers.optimal_parameter_finder import process_ticker
from models.database import load_stock_data

def main():
    logging.basicConfig(level=logging.INFO)

    ticker_symbol = "3204"  # サンプルのティッカーシンボル
    initial_capital = 100000  # 初期資本
    df = load_stock_data(ticker_symbol, days=30)  # サンプルデータをロード

    # プロファイリング対象の関数を実行
    result = process_ticker(ticker_symbol, initial_capital)
    print(result)

if __name__ == "__main__":
    # プロファイリングの実行
    cProfile.run('main()', 'profile_output.prof')

    # プロファイリング結果を読み込み、テキストファイルに出力
    with open('profile_output.txt', 'w') as f:
        p = pstats.Stats('profile_output.prof', stream=f)
        p.strip_dirs().sort_stats('cumulative').print_stats()
