# stocktrading
sudo dnf install -y python3-pip
pip install virtualenv
git clone https://github.com/saitou-cpi/stocktrading.git
cd stocktrading/
virtualenv stocktrading_env
source stocktrading_env/bin/activate
pip install requirements.txt
sudo chmod a+x get_stock_month.py
