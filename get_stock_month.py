import yfinance as yf
import pandas as pd
import datetime
from time import sleep

# 証券コードを設定します。Yahoo Financeでは日本の証券コードに .T を付けます。
ticker_symbol = '4246.T'

# データを格納するリストを初期化
all_data = []

# 現在の日付から開始
current_date = datetime.datetime.now()
# 7日分のデータを取得
delta = datetime.timedelta(days=7)

# 過去1ヶ月分のデータを取得するためのループ
for _ in range(4):  # 1ヶ月は約4週間と仮定
    end_date = current_date
    start_date = end_date - delta
    
    # データをダウンロード
    try:
        data = yf.download(ticker_symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval="1m")
        all_data.append(data)
    except Exception as e:
        print(f"Error downloading data for {start_date} to {end_date}: {e}")
    
    # 次の期間に移動
    current_date = start_date
    
    # API制限を避けるために少し待機
    sleep(2)  # 2秒待機

# 全てのデータを連結
full_data = pd.concat(all_data)

# 日付順に並び替え
full_data.sort_index(inplace=True)

# 現在の日付を取得してフォーマット
date_str = datetime.datetime.now().strftime('%Y%m%d')

# データをCSV形式で保存
csv_filename = f'4246_one_month_intraday_stock_data_{date_str}.csv'
full_data.to_csv(csv_filename)

print(f"1分足の株価データをCSV形式で {csv_filename} に保存しました。")
