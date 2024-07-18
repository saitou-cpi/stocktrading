import logging
import os

class Logger:
    def __init__(self, log_dir='logs/trade_logs', log_filename='auto_trade.log'):
        self.log_dir = log_dir
        self.log_filename = log_filename
        self.setup_logger()

    def setup_logger(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        logging.basicConfig(filename=os.path.join(self.log_dir, self.log_filename), level=logging.INFO)

    @staticmethod
    def info(message):
        logging.info(message)

    @staticmethod
    def error(message):
        logging.error(message)
