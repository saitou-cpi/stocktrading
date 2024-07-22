import yfinance as yf
import pandas as pd
import datetime
import sqlite3
from sqlalchemy import create_engine, text
import logging
import os
from time import sleep

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベースの設定
db_filename = 'stock_data.db'
db_path = os.path.join(os.getcwd(), db_filename)
engine = create_engine(f'sqlite:///{db_path}', echo=True)

# 証券コードのCSVファイルから読み込み
def load_ticker_symbols(csv_filename):
    df = pd.read_csv(csv_filename, encoding='utf-8-sig')
    return df['ticker_symbol'].astype(str).tolist()

# テーブルを作成する関数
def create_table():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS stock_data (
            id INTEGER PRIMARY KEY,
            ticker TEXT,
            date DATE,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adj_close REAL,
            volume INTEGER
        )
        """))
        logger.info("Table created successfully.")

# 最終更新日を取得する関数
def get_last_update_date(ticker):
    query = text(f"SELECT MAX(date) FROM stock_data WHERE ticker=:ticker")
    with engine.connect() as conn:
        result = conn.execute(query, {'ticker': ticker}).fetchone()
        last_date = result[0]
        if last_date:
            last_date = datetime.datetime.strptime(last_date, '%Y-%m-%d')
        return last_date

# 株価データを取得してデータベースに保存する関数
def fetch_and_store_stock_data(ticker, start_date, end_date):
    try:
        yf_ticker = f"{ticker}.T"
        data = yf.download(yf_ticker, start=start_date, end=end_date, interval='1d')
        if data.empty:
            logger.warning(f"No data found for ticker {ticker}")
            return

        data.reset_index(inplace=True)
        data['ticker'] = ticker
        data.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Adj Close': 'adj_close',
            'Volume': 'volume'
        }, inplace=True)

        with engine.begin() as conn:  # 明示的にトランザクションを開始
            for index, row in data.iterrows():
                conn.execute(text("""
                INSERT INTO stock_data (ticker, date, open, high, low, close, adj_close, volume)
                VALUES (:ticker, :date, :open, :high, :low, :close, :adj_close, :volume)
                """), {
                    'ticker': row['ticker'],
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'adj_close': row['adj_close'],
                    'volume': row['volume']
                })
        logger.info(f"Data for ticker {ticker} inserted successfully.")
        
    except Exception as e:
        logger.error(f"Error fetching data for ticker {ticker}: {e}")

# メイン処理
def main():
    # 証券コードの読み込み
    ticker_symbols = load_ticker_symbols('tokyo_ticker_symbols.csv')
    
    create_table()
    
    end_date = datetime.datetime.now()
    
    for ticker in ticker_symbols:
        last_update_date = get_last_update_date(ticker)
        if last_update_date:
            start_date = last_update_date + datetime.timedelta(days=1)
        else:
            start_date = end_date - datetime.timedelta(days=100)  # データがない場合は過去100日分取得

        fetch_and_store_stock_data(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        sleep(1)  # API制限を避けるために待機

if __name__ == "__main__":
    main()
