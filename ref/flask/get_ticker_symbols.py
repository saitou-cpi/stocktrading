get_ticker_symbols.pyimport os
import requests
import pandas as pd

# ディレクトリの作成
output_dir = "tickersymbolslist"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# エクセルファイルのURL
url = 'https://www.mof.go.jp/policy/international_policy/gaitame_kawase/fdi/list.xlsx'

# エクセルファイルのダウンロード
response = requests.get(url)
xlsx_path = os.path.join(output_dir, 'list.xlsx')
with open(xlsx_path, 'wb') as file:
    file.write(response.content)

# エクセルファイルの読み込み
xls = pd.ExcelFile(xlsx_path)

# シート名の確認
print("シート名:", xls.sheet_names)

# "上場企業の銘柄リスト"シートの読み込み
df = pd.read_excel(xls, sheet_name='上場企業の銘柄リスト')

# データフレームの先頭を表示して、列名を確認
print("データフレームの先頭:", df.head())
print("列名:", df.columns)

# "証券コード"列の抽出とカラム名の変更
if '証券コード\n(Securities code)' in df.columns:
    df_codes = df[['証券コード\n(Securities code)']]
    df_codes.columns = ['ticker_symbol']  # カラム名の変更

    # CSVに保存
    csv_path = os.path.join(output_dir, 'tokyo_ticker_symbols.csv')
    df_codes.to_csv(csv_path, index=False, encoding='utf-8-sig')

    print('証券コードの取得が完了しました。')
else:
    print('証券コード列が見つかりませんでした。')
  
