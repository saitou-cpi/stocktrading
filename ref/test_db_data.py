import sqlite3
import pandas as pd
from sqlalchemy import create_engine
import os

# データベースの設定
db_filename = 'stock_data.db'
db_path = os.path.join(os.getcwd(), db_filename)
engine = create_engine(f'sqlite:///{db_path}')

# データベースからデータを取得して表示する関数
def fetch_data_from_db(ticker=None, limit=5):
    with engine.connect() as conn:
        if ticker:
            query = f"""
            SELECT * FROM stock_data WHERE ticker='{ticker}' ORDER BY date DESC LIMIT {limit}
            """
            result = conn.execute(query)
            data = result.fetchall()
            df = pd.DataFrame(data, columns=['id', 'ticker', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume'])
        else:
            query = """
            SELECT DISTINCT ticker FROM stock_data
            """
            result = conn.execute(query)
            data = result.fetchall()
            df = pd.DataFrame(data, columns=['ticker'])
    
    return df

# メイン処理
def main():
    # 全ての証券コードを表示
    print("全ての証券コード:")
    tickers_df = fetch_data_from_db()
    print(tickers_df)

    # 特定の証券コードのデータを表示
    ticker = '1332'  # 確認したい証券コードに変更してください
    print(f"\n{ticker}の最新データ:")
    stock_data_df = fetch_data_from_db(ticker, limit=5)
    print(stock_data_df)

if __name__ == "__main__":
    main()
