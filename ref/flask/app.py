from flask import Flask, request, render_template, jsonify
import logging
from controllers.optimal_parameter_finder import process_ticker

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize():
    ticker_symbol = request.form['ticker']
    if not ticker_symbol:
        return jsonify({"error": "Ticker symbol is required"}), 400
    result = process_ticker(ticker_symbol)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
