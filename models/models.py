class TradeModel:
    def __init__(self, initial_capital=50000):
        self.capital = initial_capital
        self.holding_quantity = 0
        self.average_purchase_price = 0
