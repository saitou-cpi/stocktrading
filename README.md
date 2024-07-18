# stocktrading
sudo dnf install -y python3-pip git
pip install virtualenv
git clone https://github.com/saitou-cpi/stocktrading.git
cd stocktrading/
virtualenv st_env
source st_env/bin/activate
pip install -r requirements.txt
sudo chmod a+x get_stock_month.py backtest_trading_strategy.py


# MVC
モデル（Model）:
models.py 内の TradeModel クラスは、取引の状態を管理し、保存および読み込みのメソッドを提供します。

ビュー（View）:
views.py 内の Logger クラスは、ログの設定とメッセージの記録を行います。

コントローラ（Controller）:
controllers.py 内の TradeController クラスは、取引のロジックを管理し、取引の実行を行います。

設定（Config）:
vars.py には、取引に必要な設定変数が含まれています。

メインスクリプト（Main Script）:
auto_trading_bot.py は、エントリーポイントとして、コントローラを呼び出して取引を実行します。