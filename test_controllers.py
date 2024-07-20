import unittest
from unittest.mock import patch
from controllers.controllers import TradeController


class TestTradeController(unittest.TestCase):
    @patch('controllers.controllers.requests.get')
    def test_get_stock_price(self, mock_get):
        # モックの設定
        mock_response = mock_get.return_value
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'lastPrice': 1000}

        controller = TradeController()
        price = controller.get_stock_price()

        self.assertEqual(price, 1000)
        mock_get.assert_called_once()

    def test_calculate_moving_average(self):
        controller = TradeController()
        prices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        moving_average = controller.calculate_moving_average(prices, 5)

        self.assertEqual(moving_average, 8.0)

    @patch('controllers.controllers.TradeController.get_historical_prices')
    def test_trading_logic(self, mock_get_historical_prices):
        mock_get_historical_prices.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

        controller = TradeController()
        controller.model.holding_quantity = 10
        controller.model.average_purchase_price = 10

        action, quantity = controller.trading_logic(11)
        self.assertEqual(action, 'sell')
        self.assertEqual(quantity, 10)


if __name__ == '__main__':
    unittest.main()
