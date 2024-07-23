import requests
import pandas as pd

# エクセルファイルのURL
url = 'https://www.mof.go.jp/policy/international_policy/gaitame_kawase/fdi/list.xlsx'

# エクセルファイルのダウンロード
response = requests.get(url)
with open('list.xlsx', 'wb') as file:
    file.write(response.content)

# エクセルファイルの読み込み
xls = pd.ExcelFile('list.xlsx')

# シート名の確認
print("シート名:", xls.sheet_names)

# "上場企業の銘柄リスト"シートの読み込み
df = pd.read_excel(xls, sheet_name='上場企業の銘柄リスト')

# データフレームの先頭を表示して、列名を確認
print("データフレームの先頭:", df.head())
print("列名:", df.columns)

# "証券コード\n(Securities code)"列の抽出
if '証券コード\n(Securities code)' in df.columns:
    df_codes = df[['証券コード\n(Securities code)']]

    # JSONに保存
    df_codes.to_json('tse_stock_codes.json', orient='records', force_ascii=False, indent=4)

    print('証券コードの取得が完了しました。')
else:
    print('証券コード列が見つかりませんでした。')
