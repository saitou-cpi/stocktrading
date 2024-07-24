from flask import Flask, request, jsonify, render_template
from controllers.optimal_parameter_finder import process_ticker
from models.database import check_ticker_symbol

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize():
    ticker_symbol = request.form['ticker']
    initial_capital = request.form.get('initial_capital', type=int)
    if not ticker_symbol:
        return jsonify({"error": "Ticker symbol is required"}), 400

    if not check_ticker_symbol(ticker_symbol):
        return jsonify({"error": "Ticker symbol not found in the database"}), 400

    result = process_ticker(ticker_symbol, initial_capital)
    if not result['trades_executed']:
        return jsonify({"error": "売買不成立"}), 400

    return jsonify(result)

@app.route('/help')
def help():
    return render_template('helppage.html')

if __name__ == '__main__':
    app.run(debug=True)
